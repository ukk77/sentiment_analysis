"""
FinancialJuice RSS client - no API key required.
Fetches the public real-time news wire and filters by ticker/company relevance.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
from typing import List, Dict, Optional

# Module-level cache so the feed is fetched at most once per batch run
_feed_cache: Optional[List] = None          # parsed list of (title, link, pub_date)
_feed_cache_time: Optional[datetime] = None
_CACHE_TTL = timedelta(minutes=5)


class FinancialJuiceClient:
    """FinancialJuice public RSS feed client."""

    FEED_URL = "https://www.financialjuice.com/feed.ashx?category=all"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"
        })

    def _get_feed_items(self) -> List:
        """Return cached (title, link, pub_date) tuples, refreshing if stale."""
        global _feed_cache, _feed_cache_time
        now = datetime.utcnow()
        if _feed_cache is not None and _feed_cache_time is not None:
            if (now - _feed_cache_time) < _CACHE_TTL:
                return _feed_cache
        try:
            response = self.session.get(self.FEED_URL, timeout=20)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            raw = []
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem  = item.find("link")
                pub_elem   = item.find("pubDate")
                title    = unescape(title_elem.text or "") if title_elem is not None else ""
                link     = (link_elem.text  or "") if link_elem  is not None else ""
                pub_date = (pub_elem.text   or "") if pub_elem   is not None else ""
                if pub_date:
                    try:
                        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                        pub_date = dt.isoformat() + "Z"
                    except Exception:
                        pass
                raw.append((title, link, pub_date))
            _feed_cache = raw
            _feed_cache_time = now
            return raw
        except Exception as e:
            print(f"[financialjuice] Feed fetch error: {e}")
            return _feed_cache or []

    def get_company_news(
        self,
        ticker: str,
        company_name: str,
        max_articles: int = 20,
    ) -> List[Dict]:
        """
        Return feed items that mention the ticker or company name.
        Uses a module-level cache so the feed is fetched at most once per batch.
        """
        try:
            items = self._get_feed_items()

            ticker_upper = ticker.upper()
            company_words = [
                w.lower() for w in company_name.split()
                if len(w) > 3 and w.lower() not in {"corp", "inc.", "inc", "ltd", "llc", "the", "and"}
            ]

            normalized = []
            for (title, link, pub_date) in items:
                title_upper = title.upper()
                title_lower = title.lower()
                matched = (
                    ticker_upper in title_upper
                    or any(w in title_lower for w in company_words)
                )
                if not matched:
                    continue
                normalized.append({
                    "title":        title,
                    "description":  title,
                    "content":      title,
                    "url":          link,
                    "source":       "FinancialJuice",
                    "published_at": pub_date,
                    "author":       "",
                    "_source":      "financialjuice",
                })
                if len(normalized) >= max_articles:
                    break
            return normalized

        except Exception as e:
            print(f"[financialjuice] Unexpected error: {e}")
            return []

    def check_health(self) -> str:
        """Check if the FinancialJuice feed is reachable (uses cache if fresh)."""
        items = self._get_feed_items()
        return "healthy" if items else "unreachable"
