from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


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
    output: int = 0


class SentimentMetrics(BaseModel):
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment: float
    sources_breakdown: dict
    filter_stats: Optional[FilterStats] = None


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
    secedgar: Optional[str] = None
    yahoofinance: Optional[str] = None
    finviz: Optional[str] = None
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


class HistoryResponse(BaseModel):
    ticker: str
    snapshots: List[HistorySnapshot]
    count: int
