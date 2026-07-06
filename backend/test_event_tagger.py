"""
Standalone test for Phase 4 Step 1 (A1): keyword-based event tagger.

Run directly (no pytest required):
    python test_event_tagger.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.services.event_tagger import classify_event, classify_event_batch  # noqa: E402

PASS = []
FAIL = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


# (title, summary, expected_event_type)
FIXTURES = [
    ("Apple beats Q3 earnings estimates on strong iPhone revenue", "", "earnings"),
    ("Apple reports Q4 EPS of $1.50, above forecasts", "", "earnings"),
    ("Microsoft to acquire Activision Blizzard in $69B deal", "", "m_and_a"),
    ("Amazon and Whole Foods merger finalized", "", "m_and_a"),
    ("Tesla faces SEC probe over Musk's tweets", "", "legal"),
    ("Google hit with antitrust lawsuit settlement", "", "legal"),
    ("Nvidia raises full-year guidance amid AI demand", "", "guidance"),
    ("Company issues weak outlook for next quarter", "", "guidance"),
    ("Goldman Sachs upgrades AAPL to buy, raises price target", "", "analyst"),
    ("Analyst downgrades stock rating to sell", "", "analyst"),
    ("CEO insider selling triggers Form 4 filing", "", "insider"),
    ("Apple unveils new iPhone model with improved chip", "", "product"),
    ("Company launches new product feature globally", "", "product"),
    ("Fed signals interest rate hike amid rising inflation and CPI data", "", "macro"),
    ("Tariffs threaten global supply chain amid recession fears", "", "macro"),
    ("Stock closes flat in quiet trading session", "", "other"),
    ("", "", "other"),
]


def test_classify_event_fixtures():
    print("\n--- test_classify_event_fixtures ---")
    for title, summary, expected in FIXTURES:
        result = classify_event(title, summary)
        check(
            f"'{title[:50]}' -> {expected}",
            result == expected,
            f"got '{result}'",
        )


def test_classify_event_batch_inplace():
    print("\n--- test_classify_event_batch_inplace ---")
    articles = [
        {"title": "Apple beats Q3 earnings estimates", "description": ""},
        {"title": "Company faces SEC lawsuit", "description": "Regulatory probe underway"},
        {"title": "Quiet day for markets", "description": ""},
    ]
    classify_event_batch(articles)

    check("batch: article 0 tagged earnings", articles[0]["event_type"] == "earnings")
    check("batch: article 1 tagged legal", articles[1]["event_type"] == "legal")
    check("batch: article 2 tagged other", articles[2]["event_type"] == "other")
    check("batch: all articles have event_type key", all("event_type" in a for a in articles))


def test_ordering_specificity():
    print("\n--- test_ordering_specificity ---")
    # M&A should win over a generic "acquisition" mention even if macro-ish words nearby.
    result = classify_event(
        "Fed comments aside, Broadcom to acquire VMware in blockbuster deal", ""
    )
    check("m_and_a takes precedence over macro mention", result == "m_and_a", f"got '{result}'")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Step 1 (A1) — Event Tagger Tests")
    print("=" * 60)

    test_classify_event_fixtures()
    test_classify_event_batch_inplace()
    test_ordering_specificity()

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
