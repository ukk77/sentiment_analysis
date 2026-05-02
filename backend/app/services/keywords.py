"""Keyword / topic extraction from analyzed articles.

No external NLP dependencies — uses regex tokenisation + stop-word filtering.
Each keyword is annotated with occurrence count and average sentiment score so the
frontend can colour-code topics by positive / negative signal.
"""
import re
from collections import Counter, defaultdict
from typing import List, Dict

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "its", "it", "this", "that", "these",
    "those", "from", "by", "as", "into", "through", "during", "before",
    "after", "above", "below", "between", "out", "off", "over", "under",
    "again", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "same", "so", "than", "too", "very", "just", "also",
    "new", "one", "two", "says", "said", "say", "year", "years", "day", "days",
    "time", "up", "down", "per", "about", "if", "your", "our", "their", "his",
    "her", "we", "they", "he", "she", "you", "my", "us", "who", "which",
    "what", "now", "back", "get", "like", "make", "take", "know", "go", "see",
    "think", "look", "want", "use", "find", "give", "tell", "work", "call",
    "try", "ask", "need", "feel", "seem", "leave", "put", "mean", "keep",
    "let", "begin", "show", "hear", "play", "run", "move", "live", "believe",
    "hold", "bring", "happen", "write", "provide", "sit", "stand", "lose",
    "pay", "meet", "include", "continue", "set", "learn", "change", "lead",
    "understand", "watch", "follow", "stop", "create", "speak", "spend",
    "grow", "open", "walk", "win", "offer", "remember", "love", "consider",
    "appear", "buy", "wait", "serve", "die", "send", "expect", "build",
    "stay", "fall", "cut", "reach", "remain", "suggest", "raise", "pass",
    "sell", "require", "report", "decide", "pull",
    # Common web / meta tokens
    "com", "www", "http", "https", "co", "inc", "corp", "ltd", "llc",
    "sec", "form", "filed", "filing", "filings",
    # Noise finance words (too generic to be topics)
    "stock", "stocks", "market", "markets", "share", "shares", "investor",
    "investors", "price", "prices", "quarter", "quarterly", "annual",
    "today", "week", "month", "amid", "reuters", "bloomberg", "cnbc",
    "wsj", "press", "release", "read", "click", "subscribe", "newsletter",
    "percent", "billion", "million", "trillion",
    # Single chars / two-char noise
    "s", "re", "ve", "ll", "d", "m", "t",
}


def extract_keywords(
    articles: List[Dict],
    top_n: int = 20,
    min_count: int = 2,
) -> List[Dict]:
    """Extract top *top_n* keywords from article titles + descriptions.

    Args:
        articles: Analyzed article dicts (must contain 'title', optional
                  'description', and 'sentiment_score').
        top_n: Maximum number of keywords to return.
        min_count: Minimum article occurrences to include a keyword.

    Returns:
        List of ``{keyword, count, avg_sentiment}`` dicts sorted by count desc.
    """
    keyword_counts: Counter = Counter()
    keyword_sentiments: defaultdict = defaultdict(list)

    for article in articles:
        text = (
            f"{article.get('title', '')} "
            f"{article.get('description', '') or ''}"
        )
        score = float(article.get("sentiment_score", 0.0))

        # Tokenise: keep only alphabetic tokens of 3+ characters
        tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())

        seen_in_article: set = set()
        for token in tokens:
            if token in STOP_WORDS:
                continue
            if token not in seen_in_article:
                keyword_counts[token] += 1
                seen_in_article.add(token)
            keyword_sentiments[token].append(score)

    results: List[Dict] = []
    for kw, count in keyword_counts.most_common(top_n * 3):
        if count < min_count:
            break
        sentiments = keyword_sentiments[kw]
        avg_s = sum(sentiments) / len(sentiments)
        results.append(
            {
                "keyword": kw,
                "count": count,
                "avg_sentiment": round(avg_s, 3),
            }
        )
        if len(results) >= top_n:
            break

    return results
