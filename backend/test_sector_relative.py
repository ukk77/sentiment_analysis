"""
Standalone test for Phase 4 Step 1 (A0b): sector-relative sentiment in the
primary /api/analyze path.

Run directly (no pytest required):
    python test_sector_relative.py

Exercises the same call sequence main.py now uses:
    get_sector_etf(ticker) -> history_db.get_history(etf, limit=1)
    -> compute_sector_relative_sentiment(...) -> create_sector_relative_metrics(...)

Uses an isolated temporary SQLite file so it never touches the real DB.
"""
import os
import sys
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="sentiment_test_")
_tmp_db = os.path.join(_tmp_dir, "test_sentiment_history.db")
os.environ["SENTIMENT_DB_PATH"] = _tmp_db

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.services import db as history_db  # noqa: E402
from app.services.sector_mapping import get_sector_etf  # noqa: E402
from app.services.enhanced_metrics import (  # noqa: E402
    compute_sector_relative_sentiment,
    create_sector_relative_metrics,
)

PASS = []
FAIL = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


def _sector_relative_for(ticker: str, ticker_sentiment: float):
    """Mirror the exact logic added to main.py's /api/analyze handler."""
    sector_etf = get_sector_etf(ticker)
    if not sector_etf:
        return None
    etf_history = history_db.get_history(sector_etf, limit=1)
    if not etf_history:
        return None
    sector_sentiments = {sector_etf: etf_history[0]["avg_sentiment"]}
    result = compute_sector_relative_sentiment(
        ticker=ticker,
        ticker_sentiment=ticker_sentiment,
        sector_sentiments=sector_sentiments,
    )
    return create_sector_relative_metrics(result)


def test_populated_when_etf_snapshot_present():
    print("\n--- test_populated_when_etf_snapshot_present ---")
    history_db.init_db()

    # AAPL maps to XLK (Technology) per sector_mapping.py.
    etf = get_sector_etf("AAPL")
    check("AAPL has a sector ETF mapping", etf is not None, f"got {etf}")

    # Persist a snapshot for the sector ETF so get_history(etf, limit=1) finds it.
    history_db.save_snapshot(
        ticker=etf,
        avg_sentiment=0.10,
        overall_sentiment="neutral",
        confidence=0.7,
        total_articles=15,
        positive_count=6,
        negative_count=4,
        neutral_count=5,
    )

    metrics = _sector_relative_for("AAPL", ticker_sentiment=0.45)
    check("sector_relative_metrics is populated (not None)", metrics is not None)
    if metrics:
        check("sector_etf matches", metrics.sector_etf == etf, f"got {metrics.sector_etf}")
        check("sector_sentiment matches persisted snapshot", metrics.sector_sentiment == 0.10, f"got {metrics.sector_sentiment}")
        check(
            "relative_sentiment = ticker - sector (0.45 - 0.10 = 0.35)",
            abs(metrics.relative_sentiment - 0.35) < 1e-6,
            f"got {metrics.relative_sentiment}",
        )


def test_none_when_etf_snapshot_absent():
    print("\n--- test_none_when_etf_snapshot_absent ---")
    history_db.init_db()

    # NVDA also maps to XLK, but we deliberately do not persist a snapshot
    # for a fresh ticker with an unpopulated sector history in this test DB.
    # Use a ticker whose ETF has never been snapshotted in this isolated DB.
    etf = get_sector_etf("JPM")  # Financial sector ETF, no snapshot persisted for it
    check("JPM has a sector ETF mapping", etf is not None, f"got {etf}")

    metrics = _sector_relative_for("JPM", ticker_sentiment=0.20)
    check("sector_relative_metrics is None when ETF has no snapshot", metrics is None, f"got {metrics}")


def test_none_when_no_sector_mapping():
    print("\n--- test_none_when_no_sector_mapping ---")
    metrics = _sector_relative_for("ZZZZ_UNMAPPED", ticker_sentiment=0.20)
    check("sector_relative_metrics is None for an unmapped ticker", metrics is None, f"got {metrics}")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Step 1 (A0b) — Sector-Relative Sentiment Tests")
    print(f"Isolated test DB: {_tmp_db}")
    print("=" * 60)

    test_populated_when_etf_snapshot_present()
    test_none_when_etf_snapshot_absent()
    test_none_when_no_sector_mapping()

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
