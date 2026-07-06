"""SQLite-based historical sentiment tracking.

Free, zero-config, file-based storage. No extra dependencies — uses Python stdlib sqlite3.
DB file: backend/sentiment_history.db  (auto-created on first use; add to .gitignore)

Free production alternatives if you outgrow SQLite:
  - Supabase  (free tier PostgreSQL, 500 MB)  https://supabase.com
  - Turso     (free tier SQLite edge, 9 GB)   https://turso.tech
  - PlanetScale (free tier MySQL)             https://planetscale.com
"""
import hashlib
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone

_DEFAULT_DB = Path(__file__).resolve().parents[2] / "sentiment_history.db"
DB_PATH = Path(os.environ.get("SENTIMENT_DB_PATH", str(_DEFAULT_DB)))


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and indexes if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_snapshots (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker            TEXT    NOT NULL,
                captured_at       TEXT    NOT NULL,
                avg_sentiment     REAL    NOT NULL,
                overall_sentiment TEXT    NOT NULL,
                confidence        REAL    NOT NULL,
                total_articles    INTEGER NOT NULL,
                positive_count    INTEGER NOT NULL DEFAULT 0,
                negative_count    INTEGER NOT NULL DEFAULT 0,
                neutral_count     INTEGER NOT NULL DEFAULT 0,
                -- Contrarian metrics
                contrarian_signal TEXT,
                sentiment_percentile REAL,
                -- Sector-relative metrics
                sector_etf        TEXT,
                sector_sentiment  REAL,
                relative_sentiment REAL,
                percentile_vs_sector REAL,
                session           TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ticker_date "
            "ON sentiment_snapshots(ticker, captured_at)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyst_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker          TEXT    NOT NULL,
                captured_at     TEXT    NOT NULL,
                recommendation  TEXT,
                target_mean     REAL,
                num_analysts    INTEGER
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyst_ticker_date "
            "ON analyst_history(ticker, captured_at)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS article_sentiments (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker         TEXT    NOT NULL,
                captured_at    TEXT    NOT NULL,
                published_at   TEXT,
                collector      TEXT,
                source         TEXT,
                title          TEXT    NOT NULL,
                summary        TEXT,
                url            TEXT,
                sentiment      TEXT    NOT NULL,
                score          REAL,
                confidence     REAL,
                impact_score   REAL,
                source_weight  REAL,
                event_type     TEXT,
                url_hash       TEXT    NOT NULL,
                UNIQUE(ticker, url_hash)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_article_ticker_pub "
            "ON article_sentiments(ticker, published_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_article_captured "
            "ON article_sentiments(captured_at)"
        )
        conn.commit()
        # Migration: add new columns if they don't exist (for existing DBs)
        _migrate_add_column(conn, "contrarian_signal", "TEXT")
        _migrate_add_column(conn, "sentiment_percentile", "REAL")
        _migrate_add_column(conn, "sector_etf", "TEXT")
        _migrate_add_column(conn, "sector_sentiment", "REAL")
        _migrate_add_column(conn, "relative_sentiment", "REAL")
        _migrate_add_column(conn, "percentile_vs_sector", "REAL")
        _migrate_add_column(conn, "session", "TEXT")


def _migrate_add_column(conn: sqlite3.Connection, column: str, col_type: str) -> None:
    """Add a column if it doesn't already exist."""
    try:
        conn.execute(f"ALTER TABLE sentiment_snapshots ADD COLUMN {column} {col_type}")
        conn.commit()
    except Exception:
        pass  # column already exists


def save_snapshot(
    ticker: str,
    avg_sentiment: float,
    overall_sentiment: str,
    confidence: float,
    total_articles: int,
    positive_count: int,
    negative_count: int,
    neutral_count: int,
    session: str = "intraday",
    contrarian_signal: str = None,
    sentiment_percentile: float = None,
    sector_etf: str = None,
    sector_sentiment: float = None,
    relative_sentiment: float = None,
    percentile_vs_sector: float = None,
) -> None:
    """Persist one analysis snapshot for a ticker."""
    init_db()
    captured_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sentiment_snapshots
              (ticker, captured_at, avg_sentiment, overall_sentiment,
               confidence, total_articles, positive_count, negative_count, neutral_count,
               session, contrarian_signal, sentiment_percentile,
               sector_etf, sector_sentiment, relative_sentiment, percentile_vs_sector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker.upper(), captured_at, avg_sentiment, overall_sentiment,
                confidence, total_articles, positive_count, negative_count, neutral_count,
                session, contrarian_signal, sentiment_percentile,
                sector_etf, sector_sentiment, relative_sentiment, percentile_vs_sector,
            ),
        )
        conn.commit()


def save_analyst_snapshot(
    ticker: str,
    recommendation: Optional[str],
    target_mean: Optional[float],
    num_analysts: int,
) -> None:
    """Persist analyst rating snapshot for revision velocity tracking."""
    init_db()
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO analyst_history (ticker, captured_at, recommendation, target_mean, num_analysts) "
            "VALUES (?, ?, ?, ?, ?)",
            (ticker.upper(), captured_at, recommendation, target_mean, num_analysts),
        )
        conn.commit()


def get_analyst_history(ticker: str, days: int = 10) -> List[Dict]:
    """Return analyst snapshots for ticker from the last *days* days, newest first."""
    init_db()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT ticker, captured_at, recommendation, target_mean, num_analysts "
            "FROM analyst_history WHERE UPPER(ticker)=UPPER(?) AND captured_at >= ? "
            "ORDER BY captured_at DESC",
            (ticker.upper(), since),
        ).fetchall()
    return [dict(r) for r in rows]


def prune_old_snapshots(days: int = 90) -> int:
    """Delete sentiment_snapshots older than *days* days. Returns number of rows deleted."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM sentiment_snapshots WHERE captured_at < ?", (cutoff,)
        )
        conn.commit()
    return cur.rowcount


def get_history(ticker: str, limit: int = 90) -> List[Dict]:
    """Return the last *limit* snapshots for *ticker*, newest first."""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ticker, captured_at, avg_sentiment, overall_sentiment, confidence,
                   total_articles, positive_count, negative_count, neutral_count,
                   contrarian_signal, sentiment_percentile,
                   sector_etf, sector_sentiment, relative_sentiment, percentile_vs_sector
            FROM   sentiment_snapshots
            WHERE  UPPER(ticker) = UPPER(?)
            ORDER  BY captured_at DESC
            LIMIT  ?
            """,
            (ticker.upper(), limit),
        ).fetchall()
    return [dict(row) for row in rows]


def _url_hash(url: Optional[str], title: str) -> str:
    """Stable dedup key: sha1 of the URL, or the title if no URL is present."""
    basis = (url or title or "").strip().lower()
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()


def save_articles(ticker: str, articles: List[Dict]) -> int:
    """Persist analyzed articles for *ticker*, deduped on (ticker, url_hash).

    Each item in *articles* is expected to carry the same fields already
    used to build the API response: title, source (formatted), published_at,
    sentiment, sentiment_score, url, description, impact_score,
    source_weight, and optionally event_type. Missing fields default safely.

    Returns the number of new rows actually inserted (duplicates are ignored).
    """
    if not articles:
        return 0
    init_db()
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for a in articles:
        title = a.get("title") or ""
        url = a.get("url") or ""
        summary = (a.get("summary") or a.get("description") or "")[:200]
        rows.append((
            ticker.upper(),
            captured_at,
            a.get("published_at") or "",
            a.get("collector") or a.get("_source") or "",
            a.get("source") or "",
            title,
            summary,
            url,
            a.get("sentiment") or "neutral",
            a.get("score") if a.get("score") is not None else a.get("sentiment_score"),
            a.get("confidence"),
            a.get("impact_score"),
            a.get("source_weight"),
            a.get("event_type"),
            _url_hash(url, title),
        ))
    with _get_conn() as conn:
        cur = conn.executemany(
            """
            INSERT OR IGNORE INTO article_sentiments
              (ticker, captured_at, published_at, collector, source, title,
               summary, url, sentiment, score, confidence, impact_score,
               source_weight, event_type, url_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    return cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else 0


def prune_old_articles(days: int = 10) -> int:
    """Delete article_sentiments rows older than *days* days (by captured_at)."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM article_sentiments WHERE captured_at < ?", (cutoff,)
        )
        conn.commit()
    return cur.rowcount


def get_articles(ticker: str, days: int = 10) -> List[Dict]:
    """Return persisted articles for *ticker* captured in the last *days* days."""
    init_db()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ticker, captured_at, published_at, collector, source, title,
                   summary, url, sentiment, score, confidence, impact_score,
                   source_weight, event_type, url_hash
            FROM   article_sentiments
            WHERE  UPPER(ticker) = UPPER(?) AND captured_at >= ?
            ORDER  BY published_at DESC
            """,
            (ticker.upper(), since),
        ).fetchall()
    return [dict(row) for row in rows]


def prune_old_analyst(days: int = 90) -> int:
    """Delete analyst_history rows older than *days* days. Returns rows deleted."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM analyst_history WHERE captured_at < ?", (cutoff,)
        )
        conn.commit()
    return cur.rowcount
