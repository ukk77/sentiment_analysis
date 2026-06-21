from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ContrarianSignal(str, Enum):
    NONE = "none"
    EXTREME_BULLISH_CAUTION = "extreme_bullish_caution"
    EXTREME_BEARISH_OPPORTUNITY = "extreme_bearish_opportunity"


class PriceDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockPriceData(BaseModel):
    current_price: float
    price_change: float
    price_change_percent: float
    history: List[PriceDataPoint]


class ArticleSentiment(BaseModel):
    title: str
    source: str
    published_at: str
    sentiment: SentimentLabel
    score: float
    url: str
    summary: str
    description: Optional[str] = None
    impact_score: float = 0.0


class FilterStats(BaseModel):
    input: int = 0
    dedup_dropped: int = 0
    domain_dropped: int = 0
    title_dropped: int = 0
    finbert_relevance_dropped: int = 0
    ner_validation_dropped: int = 0  # Articles dropped due to NER entity mismatch
    output: int = 0


class ContrarianMetrics(BaseModel):
    signal: ContrarianSignal = ContrarianSignal.NONE
    sentiment_percentile: Optional[float] = None  # 0-1 scale, where 1 = extreme bullish
    confidence_threshold_met: bool = False


class SectorRelativeMetrics(BaseModel):
    sector_etf: Optional[str] = None  # e.g., "XLK" for tech
    sector_sentiment: Optional[float] = None
    relative_sentiment: Optional[float] = None  # ticker_sentiment - sector_sentiment
    percentile_vs_sector: Optional[float] = None  # 0-1 scale within sector


class SentimentMetrics(BaseModel):
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment: float
    sources_breakdown: dict
    filter_stats: Optional[FilterStats] = None
    contrarian: Optional[ContrarianMetrics] = None
    sector_relative: Optional[SectorRelativeMetrics] = None


class TopicKeyword(BaseModel):
    keyword: str
    count: int
    avg_sentiment: float


class AnalystRatings(BaseModel):
    recommendation: str = ""
    target_mean_price: Optional[float] = None
    target_high_price: Optional[float] = None
    target_low_price: Optional[float] = None
    num_analysts: int = 0
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0


class LeadLagPoint(BaseModel):
    offset_days: int
    correlation: float


class PriceCorrelation(BaseModel):
    pearson_r: Optional[float] = None
    divergence_alert: bool = False
    divergence_direction: Optional[str] = None
    lead_lag: List[LeadLagPoint] = []


class SentimentResponse(BaseModel):
    ticker: str
    company_name: str
    overall_sentiment: SentimentLabel
    confidence: float
    metrics: SentimentMetrics
    articles: List[ArticleSentiment]
    price_data: Optional[StockPriceData] = None
    topics: Optional[List[TopicKeyword]] = None
    analyst_ratings: Optional[AnalystRatings] = None
    correlation: Optional[PriceCorrelation] = None


class AnalyzeRequest(BaseModel):
    ticker: str
    company_name: str


class HealthResponse(BaseModel):
    status: str
    news_api: str
    finnhub: str
    twitter: Optional[str] = None
    googlenews: Optional[str] = None
    bingnews: Optional[str] = None
    secedgar: Optional[str] = None
    yahoofinance: Optional[str] = None
    finviz: Optional[str] = None
    financialjuice: Optional[str] = None
    model_loaded: bool


class HistorySnapshot(BaseModel):
    ticker: str
    captured_at: str
    avg_sentiment: float
    overall_sentiment: str
    confidence: float
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    # Contrarian metrics
    contrarian_signal: Optional[str] = None
    sentiment_percentile: Optional[float] = None
    # Sector-relative metrics
    sector_etf: Optional[str] = None
    sector_sentiment: Optional[float] = None
    relative_sentiment: Optional[float] = None
    percentile_vs_sector: Optional[float] = None


class HistoryResponse(BaseModel):
    ticker: str
    snapshots: List[HistorySnapshot]
    count: int
