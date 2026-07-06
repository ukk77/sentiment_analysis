"""
Standalone test for Phase 4 Step 1 (A5): FinBERT confidence calibration
(temperature scaling).

Run directly (no pytest required):
    python test_calibration.py

Avoids downloading/loading the real FinBERT model: the softmax-temperature
math is tested directly with torch, and the env-var wiring is tested via a
lightweight subclass that skips _load_model().
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import torch  # noqa: E402

PASS = []
FAIL = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


def test_temperature_softens_distribution():
    print("\n--- test_temperature_softens_distribution ---")
    # Simulate a confident FinBERT logit vector (large gap -> peaky softmax).
    logits = torch.tensor([[4.0, 0.5, 0.2]])

    probs_t1 = torch.nn.functional.softmax(logits / 1.0, dim=-1)
    probs_t15 = torch.nn.functional.softmax(logits / 1.5, dim=-1)

    max_t1 = float(probs_t1.max())
    max_t15 = float(probs_t15.max())

    check(
        "T=1.5 max-prob is lower than T=1.0 max-prob",
        max_t15 < max_t1,
        f"T=1.0 -> {max_t1:.4f}, T=1.5 -> {max_t15:.4f}",
    )
    check(
        "probabilities still sum to 1.0 at T=1.5",
        abs(float(probs_t15.sum()) - 1.0) < 1e-5,
    )
    check(
        "argmax label unchanged by temperature (only confidence changes)",
        int(probs_t1.argmax()) == int(probs_t15.argmax()),
    )


def test_temperature_env_var_wiring():
    print("\n--- test_temperature_env_var_wiring ---")

    # Import lazily and patch _load_model so instantiation doesn't try to
    # download/load the real FinBERT weights.
    from app.services import analyzer as analyzer_module

    original_load = analyzer_module.FinBERTAnalyzer._load_model
    analyzer_module.FinBERTAnalyzer._load_model = lambda self: None

    try:
        os.environ["FINBERT_TEMPERATURE"] = "2.0"
        instance = analyzer_module.FinBERTAnalyzer()
        check("self.temperature reads FINBERT_TEMPERATURE=2.0", instance.temperature == 2.0, f"got {instance.temperature}")

        del os.environ["FINBERT_TEMPERATURE"]
        instance_default = analyzer_module.FinBERTAnalyzer()
        check("self.temperature defaults to 1.5 when unset", instance_default.temperature == 1.5, f"got {instance_default.temperature}")
    finally:
        analyzer_module.FinBERTAnalyzer._load_model = original_load
        os.environ.pop("FINBERT_TEMPERATURE", None)


def test_relevance_threshold_volume_note():
    print("\n--- test_relevance_threshold_volume_note ---")
    # This is a documentation-level check: softened confidence at T=1.5 means
    # the existing min_confidence=0.40 pre-filter may need to drop to ~0.35
    # once validated on real traffic (see plan §2.3). We assert the threshold
    # constant used in main.py hasn't silently drifted without review.
    with open(os.path.join(os.path.dirname(__file__), "app", "main.py"), encoding="utf-8") as f:
        main_src = f.read()
    check(
        "main.py still uses the documented min_confidence=0.40 pre-filter",
        "min_confidence=0.40" in main_src,
        "threshold changed — re-validate drop volume per plan before editing this test",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Step 1 (A5) — FinBERT Confidence Calibration Tests")
    print("=" * 60)

    test_temperature_softens_distribution()
    test_temperature_env_var_wiring()
    test_relevance_threshold_volume_note()

    print("\n" + "=" * 60)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 60)

    if FAIL:
        for name in FAIL:
            print(f"  FAILED: {name}")
        sys.exit(1)
    else:
        print("All tests passed.")
        sys.exit(0)
