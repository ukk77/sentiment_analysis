"""Enhanced sentiment metrics computation.

Provides contrarian signal detection and sector-relative sentiment analysis.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ..models.sentiment import ContrarianSignal, ContrarianMetrics, SectorRelativeMetrics
from .sector_mapping import get_sector_etf, get_tickers_in_sector


@dataclass
class ContrarianResult:
    signal: ContrarianSignal
    sentiment_percentile: Optional[float]
    confidence_threshold_met: bool


def compute_contrarian_signal(
    avg_sentiment: float,
    confidence: float,
    total_articles: int,
    percentile_threshold: float = 0.85,
    min_confidence: float = 0.7,
    min_articles: int = 10,
) -> ContrarianResult:
    """Compute contrarian signal based on sentiment extremes.
    
    When sentiment reaches extremes (>90% bullish or <10%) with high confidence,
    it often indicates a crowded trade ready to reverse.
    
    Args:
        avg_sentiment: Average sentiment score (-1 to 1)
        confidence: Sentiment confidence (0 to 1)
        total_articles: Number of articles analyzed
        percentile_threshold: Threshold for extreme signal (0.85 = 85th percentile)
        min_confidence: Minimum confidence required for signal
        min_articles: Minimum articles required for signal
        
    Returns:
        ContrarianResult with signal type and metadata
    """
    # Normalize sentiment to 0-1 scale for percentile calculation
    # avg_sentiment ranges from -1 (very negative) to +1 (very positive)
    sentiment_percentile = (avg_sentiment + 1) / 2
    
    # Check if we meet minimum requirements
    if confidence < min_confidence or total_articles < min_articles:
        return ContrarianResult(
            signal=ContrarianSignal.NONE,
            sentiment_percentile=round(sentiment_percentile, 3),
            confidence_threshold_met=False,
        )
    
    # Check for extreme bullish sentiment (contrarian caution)
    if sentiment_percentile >= percentile_threshold:
        return ContrarianResult(
            signal=ContrarianSignal.EXTREME_BULLISH_CAUTION,
            sentiment_percentile=round(sentiment_percentile, 3),
            confidence_threshold_met=True,
        )
    
    # Check for extreme bearish sentiment (contrarian opportunity)
    if sentiment_percentile <= (1 - percentile_threshold):
        return ContrarianResult(
            signal=ContrarianSignal.EXTREME_BEARISH_OPPORTUNITY,
            sentiment_percentile=round(sentiment_percentile, 3),
            confidence_threshold_met=True,
        )
    
    return ContrarianResult(
        signal=ContrarianSignal.NONE,
        sentiment_percentile=round(sentiment_percentile, 3),
        confidence_threshold_met=True,
    )


@dataclass
class SectorRelativeResult:
    sector_etf: Optional[str]
    sector_sentiment: Optional[float]
    relative_sentiment: Optional[float]
    percentile_vs_sector: Optional[float]


def compute_sector_relative_sentiment(
    ticker: str,
    ticker_sentiment: float,
    sector_sentiments: Dict[str, float],
) -> SectorRelativeResult:
    """Compute sector-relative sentiment metrics.
    
    Compares ticker sentiment to its sector average to identify
    outperformance or underperformance vs peers.
    
    Args:
        ticker: Stock ticker symbol
        ticker_sentiment: The ticker's sentiment score
        sector_sentiments: Dict mapping ETF symbols to sector sentiment scores
        
    Returns:
        SectorRelativeResult with relative metrics
    """
    sector_etf = get_sector_etf(ticker)
    
    if not sector_etf:
        # No sector mapping available
        return SectorRelativeResult(
            sector_etf=None,
            sector_sentiment=None,
            relative_sentiment=None,
            percentile_vs_sector=None,
        )
    
    # Get sector sentiment
    sector_sentiment = sector_sentiments.get(sector_etf)
    if sector_sentiment is None:
        return SectorRelativeResult(
            sector_etf=sector_etf,
            sector_sentiment=None,
            relative_sentiment=None,
            percentile_vs_sector=None,
        )
    
    # Calculate relative sentiment
    relative_sentiment = ticker_sentiment - sector_sentiment
    
    # Calculate percentile within sector
    # Get all tickers in this sector and their sentiments
    sector_tickers = get_tickers_in_sector(sector_etf)
    sector_sentiment_list = []
    
    for t in sector_tickers:
        if t in sector_sentiments:
            sector_sentiment_list.append(sector_sentiments[t])
    
    if not sector_sentiment_list:
        percentile_vs_sector = None
    else:
        # Add current ticker sentiment
        all_sector_sentiments = sector_sentiment_list + [ticker_sentiment]
        all_sector_sentiments.sort()
        
        # Calculate percentile (position in sorted list)
        position = all_sector_sentiments.index(ticker_sentiment)
        percentile_vs_sector = position / (len(all_sector_sentiments) - 1) if len(all_sector_sentiments) > 1 else 0.5
    
    return SectorRelativeResult(
        sector_etf=sector_etf,
        sector_sentiment=round(sector_sentiment, 3),
        relative_sentiment=round(relative_sentiment, 3),
        percentile_vs_sector=round(percentile_vs_sector, 3) if percentile_vs_sector is not None else None,
    )


def create_contrarian_metrics(result: ContrarianResult) -> ContrarianMetrics:
    """Convert ContrarianResult to ContrarianMetrics model."""
    return ContrarianMetrics(
        signal=result.signal,
        sentiment_percentile=result.sentiment_percentile,
        confidence_threshold_met=result.confidence_threshold_met,
    )


def create_sector_relative_metrics(result: SectorRelativeResult) -> SectorRelativeMetrics:
    """Convert SectorRelativeResult to SectorRelativeMetrics model."""
    return SectorRelativeMetrics(
        sector_etf=result.sector_etf,
        sector_sentiment=result.sector_sentiment,
        relative_sentiment=result.relative_sentiment,
        percentile_vs_sector=result.percentile_vs_sector,
    )
