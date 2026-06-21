"""SQLite-based historical sentiment tracking.

Free, zero-config, file-based storage. No extra dependencies — uses Python stdlib sqlite3.
DB file: backend/sentiment_history.db  (auto-created on first use; add to .gitignore)

Free production alternatives if you outgrow SQLite:
  - Supabase  (free tier PostgreSQL, 500 MB)  https://supabase.com
  - Turso     (free tier SQLite edge, 9 GB)   https://turso.tech
  - PlanetScale (free tier MySQL)             https://planetscale.com
"""
import sqlite3
from pathlib import Path
from typing import List, Dict
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[2] / "sentiment_history.db"


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
