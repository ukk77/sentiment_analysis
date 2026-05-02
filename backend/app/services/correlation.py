"""Price–sentiment correlation metrics.

Uses numpy (already in requirements) — no scipy needed.
Computes:
  - Pearson r between same-day price returns and daily sentiment
  - Lead/lag table: does today's sentiment predict price at +1/+2/+3 days?
  - Divergence alert: 3-day price trend vs 3-day sentiment trend diverging
"""
import numpy as np
from typing import List, Dict, Optional


def _pearson_r(x: List[float], y: List[float]) -> Optional[float]:
    """Compute Pearson r. Returns None if insufficient variance or data."""
    if len(x) < 4 or len(y) < 4:
        return None
    xa = np.array(x, dtype=float)
    ya = np.array(y, dtype=float)
    if np.std(xa) < 1e-9 or np.std(ya) < 1e-9:
        return None
    r = float(np.corrcoef(xa, ya)[0, 1])
    return None if np.isnan(r) else round(r, 3)


def compute_correlation(
    price_history: List[Dict],
    daily_sentiment: Dict[str, float],
) -> Dict:
    """Compute price–sentiment correlation metrics.

    Args:
        price_history: List of ``{date, open, high, low, close, volume}`` dicts
                       ordered chronologically.
        daily_sentiment: ``{YYYY-MM-DD: avg_sentiment_score}`` mapping.

    Returns:
        Dict with keys: pearson_r, lead_lag, divergence_alert, divergence_direction.
    """
    # Build a chronologically ordered series of (price_return, sentiment) pairs
    # for days where BOTH a sentiment score AND a price exist.
    aligned: List[Dict] = []
    for i in range(1, len(price_history)):
        prev = price_history[i - 1]
        curr = price_history[i]
        date_key = curr["date"][:10]   # YYYY-MM-DD
        if date_key in daily_sentiment and curr["close"] and prev["close"]:
            price_return = (curr["close"] - prev["close"]) / prev["close"]
            aligned.append(
                {
                    "date": date_key,
                    "price_return": price_return,
                    "sentiment": daily_sentiment[date_key],
                }
            )

    returns_list = [d["price_return"] for d in aligned]
    sentiments_list = [d["sentiment"] for d in aligned]

    # Same-day Pearson r
    pearson = _pearson_r(returns_list, sentiments_list)

    # Lead/lag: past sentiment predicts future price return
    lead_lag: List[Dict] = []
    for offset in [1, 2, 3]:
        if len(aligned) > offset + 2:
            past_sentiment = [d["sentiment"] for d in aligned[:-offset]]
            future_returns = [d["price_return"] for d in aligned[offset:]]
            lag_r = _pearson_r(past_sentiment, future_returns)
            if lag_r is not None:
                lead_lag.append({"offset_days": offset, "correlation": lag_r})

    # Divergence detection using the last 3 overlapping days
    divergence_alert = False
    divergence_direction = None
    if len(aligned) >= 3:
        recent = aligned[-3:]
        price_trend = sum(d["price_return"] for d in recent)
        sentiment_trend = recent[-1]["sentiment"] - recent[0]["sentiment"]
        if abs(price_trend) > 0.01 and abs(sentiment_trend) > 0.10:
            if price_trend > 0 and sentiment_trend < 0:
                divergence_alert = True
                divergence_direction = "price_up_sentiment_down"
            elif price_trend < 0 and sentiment_trend > 0:
                divergence_alert = True
                divergence_direction = "price_down_sentiment_up"

    return {
        "pearson_r": pearson,
        "lead_lag": lead_lag,
        "divergence_alert": divergence_alert,
        "divergence_direction": divergence_direction,
    }
