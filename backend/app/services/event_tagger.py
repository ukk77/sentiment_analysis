"""Phase 4 Step 1 (A1): keyword-based event classification for news articles.

Deterministic, zero-dependency, fast. Classifies each article's title +
summary into one coarse event category so downstream consumers (harness,
RAG layer, analytics) can filter/weight by event type without re-reading
the article text.

An LLM-based tagger is a later, optional swap behind the same function
signature — see EVENT_TAGGER_MODE below.
"""
import os
import re
from typing import List, Tuple

EVENT_TAGGER_MODE = os.environ.get("EVENT_TAGGER_MODE", "keyword")

EventRule = Tuple[str, List[re.Pattern]]

# Ordered rules: first matching category wins. Order matters — more specific
# categories (m_and_a, legal) are checked before broader ones (macro, other).
_RULES: List[EventRule] = [
    ("earnings", [
        re.compile(r"\bq[1-4]\b", re.I),
        re.compile(r"\beps\b", re.I),
        re.compile(r"\brevenue\b", re.I),
        re.compile(r"\bearnings\b", re.I),
        re.compile(r"\bbeats?\b.*\b(estimate|expectation|forecast)s?\b", re.I),
        re.compile(r"\bmisses?\b.*\b(estimate|expectation|forecast)s?\b", re.I),
        re.compile(r"\bquarterly\s+results?\b", re.I),
    ]),
    ("m_and_a", [
        re.compile(r"\bacquir\w*\b", re.I),
        re.compile(r"\bmerger\b", re.I),
        re.compile(r"\bmerge[sd]?\b", re.I),
        re.compile(r"\bbuyout\b", re.I),
        re.compile(r"\btakeover\b", re.I),
        re.compile(r"\bacquisition\b", re.I),
    ]),
    ("legal", [
        re.compile(r"\blawsuit\b", re.I),
        re.compile(r"\bsec\b", re.I),
        re.compile(r"\bprobe\b", re.I),
        re.compile(r"\bsettlement\b", re.I),
        re.compile(r"\blitigation\b", re.I),
        re.compile(r"\bantitrust\b", re.I),
        re.compile(r"\bregulator[sy]*\b", re.I),
        re.compile(r"\bfine[ds]?\b", re.I),
    ]),
    ("guidance", [
        re.compile(r"\bguidance\b", re.I),
        re.compile(r"\boutlook\b", re.I),
        re.compile(r"\bforecast\b", re.I),
        re.compile(r"\bprojections?\b", re.I),
    ]),
    ("analyst", [
        re.compile(r"\bupgrade[sd]?\b", re.I),
        re.compile(r"\bdowngrade[sd]?\b", re.I),
        re.compile(r"\bprice\s+target\b", re.I),
        re.compile(r"\brating\b", re.I),
        re.compile(r"\binitiat\w*\s+coverage\b", re.I),
    ]),
    ("insider", [
        re.compile(r"\binsider\b", re.I),
        re.compile(r"\bform\s*4\b", re.I),
        re.compile(r"\binsider\s+(buy|sell|trading)\b", re.I),
    ]),
    ("product", [
        re.compile(r"\blaunch\w*\b", re.I),
        re.compile(r"\bunveil\w*\b", re.I),
        re.compile(r"\brelease[sd]?\b", re.I),
        re.compile(r"\bnew\s+(product|model|feature|chip|device)\b", re.I),
    ]),
    ("macro", [
        re.compile(r"\bfed\b", re.I),
        re.compile(r"\bcpi\b", re.I),
        re.compile(r"\binterest\s+rate[s]?\b", re.I),
        re.compile(r"\btariff[s]?\b", re.I),
        re.compile(r"\binflation\b", re.I),
        re.compile(r"\brecession\b", re.I),
        re.compile(r"\bgdp\b", re.I),
    ]),
]

_VALID_EVENT_TYPES = {rule[0] for rule in _RULES} | {"other"}


def classify_event(title: str, summary: str = "") -> str:
    """Classify a news article into a coarse event category.

    Args:
        title: Article title.
        summary: Article summary/description (optional, improves recall).

    Returns:
        One of: earnings, guidance, m_and_a, legal, macro, product,
        analyst, insider, other.
    """
    text = f"{title or ''} {summary or ''}"
    if not text.strip():
        return "other"

    for event_type, patterns in _RULES:
        for pattern in patterns:
            if pattern.search(text):
                return event_type

    return "other"


def classify_event_batch(articles: List[dict]) -> None:
    """In-place: set article['event_type'] for each article in *articles*.

    Reads 'title' and 'description' (or 'summary') from each article dict.
    """
    for article in articles:
        title = article.get("title") or ""
        summary = article.get("description") or article.get("summary") or ""
        article["event_type"] = classify_event(title, summary)
