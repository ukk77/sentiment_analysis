"""
Standalone test for Phase 4 Step 1 (A0a): article persistence layer.

Run directly (no pytest required):
    python test_article_persistence.py

Uses an isolated temporary SQLite file (via SENTIMENT_DB_PATH) so it never
touches the real sentiment_history.db.
"""
import os
import sys
import tempfile
import sqlite3
from datetime import datetime, timedelta, timezone

# Point db.py at a throwaway DB file BEFORE importing it.
_tmp_dir = tempfile.mkdtemp(prefix="sentiment_test_")
_tmp_db = os.path.join(_tmp_dir, "test_sentiment_history.db")
os.environ["SENTIMENT_DB_PATH"] = _tmp_db

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.services import db as history_db  # noqa: E402

PASS = []
FAIL = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


def make_article(i: int, title_suffix: str = "") -> dict:
    return {
        "title": f"AAPL beats earnings estimates {title_suffix}{i}",
        "url": f"https://example.com/article-{i}",
        "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_source": "newsapi",
        "source": "NewsAPI | Reuters",
        "description": "Apple reported strong quarterly results driven by iPhone sales.",
        "sentiment": "positive",
        "sentiment_score": 0.82,
        "confidence": 0.91,
        "impact_score": 0.55,
        "source_weight": 1.0,
        "event_type": "earnings",
    }


def test_save_and_dedup():
    print("\n--- test_save_and_dedup ---")
    history_db.init_db()
    articles = [make_article(i) for i in range(3)]

    inserted_first = history_db.save_articles("AAPL", articles)
    check("first save inserts 3 rows", inserted_first == 3, f"got {inserted_first}")

    # Re-save the exact same articles -> should be fully deduped (0 new rows)
    inserted_second = history_db.save_articles("AAPL", articles)
    check("re-save of identical articles inserts 0 rows", inserted_second == 0, f"got {inserted_second}")

    fetched = history_db.get_articles("AAPL", days=10)
    check("get_articles returns exactly 3 rows after dedup", len(fetched) == 3, f"got {len(fetched)}")

    if fetched:
        row = fetched[0]
        check("persisted row has non-null sentiment", row.get("sentiment") == "positive")
        check("persisted row has event_type carried through", row.get("event_type") == "earnings")
        check("persisted row has url_hash", bool(row.get("url_hash")))


def test_purge_boundary():
    print("\n--- test_purge_boundary ---")
    history_db.init_db()

    # Insert one "fresh" article via the normal path.
    fresh = make_article(100, title_suffix="fresh-")
    history_db.save_articles("MSFT", [fresh])

    # Manually insert one "stale" article directly with an old captured_at
    # (bypassing save_articles, since it always stamps "now").
    old_captured_at = (datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with sqlite3.connect(history_db.DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO article_sentiments
              (ticker, captured_at, published_at, collector, source, title,
               summary, url, sentiment, score, confidence, impact_score,
               source_weight, event_type, url_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MSFT", old_captured_at, old_captured_at, "newsapi", "NewsAPI",
                "Old stale MSFT article", "summary", "https://example.com/stale-msft",
                "neutral", 0.0, 0.5, 0.1, 1.0, "other", "stale-hash-msft",
            ),
        )
        conn.commit()

    before = history_db.get_articles("MSFT", days=9999)
    check("both fresh and stale rows exist before purge", len(before) == 2, f"got {len(before)}")

    removed = history_db.prune_old_articles(days=10)
    check("prune_old_articles removes at least the stale row", removed >= 1, f"removed={removed}")

    after = history_db.get_articles("MSFT", days=9999)
    stale_still_present = any(r["url"] == "https://example.com/stale-msft" for r in after)
    check("stale row (15d old) is gone after 10-day purge", not stale_still_present)
    fresh_still_present = any("fresh-" in r["title"] for r in after)
    check("fresh row survives the purge", fresh_still_present)


def test_prune_old_analyst():
    print("\n--- test_prune_old_analyst ---")
    history_db.init_db()
    history_db.save_analyst_snapshot("AAPL", "buy", 200.0, 30)

    old_captured_at = (datetime.now(timezone.utc) - timedelta(days=95)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with sqlite3.connect(history_db.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO analyst_history (ticker, captured_at, recommendation, target_mean, num_analysts) "
            "VALUES (?, ?, ?, ?, ?)",
            ("AAPL", old_captured_at, "hold", 150.0, 20),
        )
        conn.commit()

    before = history_db.get_analyst_history("AAPL", days=9999)
    check("both recent and stale analyst rows exist before purge", len(before) == 2, f"got {len(before)}")

    removed = history_db.prune_old_analyst(days=90)
    check("prune_old_analyst removes the 95-day-old row", removed >= 1, f"removed={removed}")

    after = history_db.get_analyst_history("AAPL", days=9999)
    check("recent analyst row survives 90-day purge", len(after) == 1, f"got {len(after)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Step 1 (A0a) — Article Persistence Layer Tests")
    print(f"Isolated test DB: {_tmp_db}")
    print("=" * 60)

    test_save_and_dedup()
    test_purge_boundary()
    test_prune_old_analyst()

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
