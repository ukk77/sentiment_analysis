"""
SEC EDGAR API client for fetching company filings.
No API key required. Rate limit: 10 requests/second
Documentation: https://www.sec.gov/edgar/sec-api-documentation

Deep Dive features:
  - 30-day look-back window (was 14)
  - 10-K (annual) and 10-Q (quarterly) filing support alongside 8-K
  - Fetches actual filing body text via EDGAR's primaryDocument field for
    richer FinBERT sentiment analysis (limited to first 3 000 chars per doc)
"""
import re
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

try:
    from bs4 import BeautifulSoup
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False


def _strip_html(html: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    if _BS4_AVAILABLE:
        text = BeautifulSoup(html, "lxml").get_text(separator=" ")
    else:
        text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


class SECEDGARClient:
    """SEC EDGAR client for fetching company filings and financial reports."""

    BASE_URL = "https://www.sec.gov/Archives/edgar"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "StockSentimentBot/1.0 (contact@example.com)"}
        )
        self.last_request_time = 0
        self.min_delay = 0.12  # ~8 req/sec (SEC limit is 10/sec)

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()

    # ------------------------------------------------------------------
    # Core filing retrieval
    # ------------------------------------------------------------------

    def get_company_filings(
        self,
        ticker: str,
        filing_types: List[str] = None,
        days_back: int = 30,
        fetch_text: bool = False,
        max_text_chars: int = 3000,
        max_text_fetches: int = 3,
    ) -> List[Dict]:
        """Fetch recent company filings from SEC EDGAR.

        Args:
            ticker: Stock ticker symbol.
            filing_types: Filing form types to include, e.g. ['8-K', '10-Q', '10-K'].
            days_back: Look-back window in calendar days.
            fetch_text: If True, fetch the primary document body for sentiment analysis.
            max_text_chars: Maximum characters to extract per document.
            max_text_fetches: Maximum number of documents to fetch text for (speed cap).

        Returns:
            List of article-compatible filing dicts.
        """
        if filing_types is None:
            filing_types = ["8-K", "10-Q", "10-K"]

        try:
            cik = self._get_cik_from_ticker(ticker)
            if not cik:
                print(f"[secedgar] Could not resolve CIK for {ticker}")
                return []

            submissions = self._get_submissions(cik)
            if not submissions:
                return []

            recent = submissions.get("filings", {}).get("recent", {})
            accession_numbers = recent.get("accessionNumber", [])
            forms = recent.get("form", [])
            filing_dates = recent.get("filingDate", [])
            primary_docs = recent.get("primaryDocument", [])

            cutoff_date = datetime.now() - timedelta(days=days_back)
            filings: List[Dict] = []
            text_fetched = 0

            for i, accession in enumerate(accession_numbers):
                if i >= len(forms) or i >= len(filing_dates):
                    continue

                form = forms[i]
                filing_date = filing_dates[i]
                primary_doc = primary_docs[i] if i < len(primary_docs) else ""

                if form not in filing_types:
                    continue

                try:
                    filing_dt = datetime.strptime(filing_date, "%Y-%m-%d")
                    if filing_dt < cutoff_date:
                        continue
                except ValueError:
                    continue

                accession_no_dashes = accession.replace("-", "")
                cik_int = int(cik)
                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik_int}/{accession_no_dashes}/{accession}-index.htm"
                )

                description = f"SEC {form} filing for {ticker} filed on {filing_date}"
                content = description

                if fetch_text and primary_doc and text_fetched < max_text_fetches:
                    doc_text = self._fetch_filing_text(
                        cik_int, accession_no_dashes, primary_doc, max_text_chars
                    )
                    if doc_text:
                        content = doc_text
                        description = doc_text[:500]
                        text_fetched += 1

                filings.append(
                    {
                        "title": f"{form} Filing — {ticker.upper()} ({filing_date})",
                        "description": description,
                        "content": content,
                        "url": filing_url,
                        "source": "SEC EDGAR",
                        "published_at": f"{filing_date}T00:00:00Z",
                        "author": "SEC",
                        "_source": "secedgar",
                        "_filing_type": form,
                        "_cik": cik,
                    }
                )

            return filings[:20]

        except Exception as e:
            print(f"[secedgar] Error fetching filings: {e}")
            return []

    # ------------------------------------------------------------------
    # Deep Dive: all major filing types with body text
    # ------------------------------------------------------------------

    def get_deep_dive_filings(self, ticker: str) -> List[Dict]:
        """Fetch 8-K, 10-K, and 10-Q filings over 30 days.

        For 10-K/10-Q, fetches the primary document body text (up to 3 000 chars)
        to give FinBERT richer content for sentiment analysis.
        """
        return self.get_company_filings(
            ticker,
            filing_types=["8-K", "10-Q", "10-K"],
            days_back=30,
            fetch_text=True,
            max_text_chars=3000,
            max_text_fetches=3,
        )

    # ------------------------------------------------------------------
    # Legacy convenience method (kept for backward compat)
    # ------------------------------------------------------------------

    def get_latest_8k(self, ticker: str) -> List[Dict]:
        """Get 8-K filings over the last 30 days (expanded from 14)."""
        return self.get_company_filings(
            ticker, filing_types=["8-K"], days_back=30, fetch_text=False
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_filing_text(
        self,
        cik_int: int,
        accession_no_dashes: str,
        primary_doc: str,
        max_chars: int = 3000,
    ) -> Optional[str]:
        """Download and strip the primary filing document.

        Returns plain text (up to *max_chars* chars) or None on failure.
        """
        if not primary_doc:
            return None
        url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_no_dashes}/{primary_doc}"
        )
        try:
            self._rate_limit()
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            raw = resp.text
            # Strip HTML for .htm / .html documents
            if primary_doc.lower().endswith((".htm", ".html")):
                raw = _strip_html(raw)
            return raw[:max_chars].strip() or None
        except Exception as e:
            print(f"[secedgar] Could not fetch filing text from {url}: {e}")
            return None

    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Resolve ticker → 10-digit zero-padded CIK."""
        try:
            self._rate_limit()
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            for entry in response.json().values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
            return None
        except Exception as e:
            print(f"[secedgar] Error fetching CIK: {e}")
            return None

    def _get_submissions(self, cik: str) -> Optional[Dict]:
        """Fetch the EDGAR submissions JSON for a CIK."""
        try:
            self._rate_limit()
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = self.session.get(url, timeout=30)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[secedgar] Error fetching submissions: {e}")
            return None

    def check_health(self) -> str:
        """Check if SEC EDGAR API is accessible."""
        try:
            self._rate_limit()
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return "healthy"
            elif response.status_code == 403:
                return "blocked"
            return f"error_{response.status_code}"
        except requests.exceptions.RequestException:
            return "unreachable"
