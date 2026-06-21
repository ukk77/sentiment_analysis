"""TTL cache for sentiment analysis results.

Prevents redundant FinBERT runs when the same ticker is requested multiple
times within a short window (e.g. data_collection hitting 65 tickers in loop).

Usage:
    from app.services.cache import sentiment_cache
    cached = sentiment_cache.get("AAPL")
    if cached:
        return cached
    result = ... expensive work ...
    sentiment_cache.set("AAPL", result)
"""
from __future__ import annotations

import threading
import time
from typing import Any, Optional


class TTLCache:
    """Thread-safe in-memory cache with per-entry TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            now = time.monotonic()
            return sum(1 for _, (_, exp) in self._store.items() if exp > now)

    def stats(self) -> dict:
        with self._lock:
            now = time.monotonic()
            live = [(k, exp - now) for k, (_, exp) in self._store.items() if exp > now]
        return {
            "entries": len(live),
            "ttl_seconds": self._ttl,
            "keys": [k for k, _ in live],
        }


# Singleton — 1-hour TTL (matches data_collection schedule: every 3 hours)
sentiment_cache = TTLCache(ttl_seconds=3600)
