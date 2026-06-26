import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.models.sentiment import (
    AnalyzeRequest,
    SentimentResponse,
    ArticleSentiment,
    SentimentMetrics,
    SentimentLabel,
    HealthResponse,
    StockPriceData,
    PriceDataPoint,
    FilterStats,
    TopicKeyword,
    AnalystRatings,
    AnalystRevisionMetrics,
    LeadLagPoint,
    PriceCorrelation,
    HistorySnapshot,
    HistoryResponse,
    ComprehensiveAnalysisRequest,
    ComprehensiveAnalysisResponse,
)
from app.services.newsapi import NewsAPIClient
from app.services.finnhub import FinnhubClient
from app.services.twitter import TwitterClient
from app.services.googlenews import GoogleNewsClient
from app.services.bingnews import BingNewsClient
from app.services.secedgar import SECEDGARClient
from app.services.yahoofinance import YahooFinanceClient
from app.services.finviz import FinvizClient
from app.services.financialjuice import FinancialJuiceClient
from app.services.analyzer import FinBERTAnalyzer
from app.services.article_filter import filter_articles
from app.services import db as history_db
from app.services.keywords import extract_keywords
from app.services.correlation import compute_correlation
from app.services.enhanced_metrics import (
    compute_contrarian_signal,
    compute_sector_relative_sentiment,
    create_contrarian_metrics,
    create_sector_relative_metrics,
    compute_analyst_revision_velocity,
)
from app.services.sector_mapping import get_sector_etf
from app.services.cache import sentiment_cache
from app.services import comprehensive_analysis as comprehensive

# Global instances
analyzer = None
news_client = None
finnhub_client = None
twitter_client = None
googlenews_client = None
bingnews_client = None
secedgar_client = None
yahoofinance_client = None
finviz_client = None
financial_juice_client = None

_SOURCE_LABELS = {
    "newsapi": "NewsAPI",
    "finnhub": "Finnhub",
    "googlenews": "Google News",
    "bingnews": "Bing News",
    "yahoofinance": "Yahoo Finance",
    "finviz": "Finviz",
    "secedgar": "SEC EDGAR",
    "financialjuice": "FinancialJuice",
    "twitter": "Twitter",
}


async def _run_source_call(label, func, *args, **kwargs):
    try:
        return await asyncio.to_thread(func, *args, **kwargs)
    except Exception as e:
        print(f"Error fetching {label}: {e}")
        return []


def _format_article_source(article):
    publisher = (article.get("source") or "").strip()
    collector = _SOURCE_LABELS.get(article.get("_source"), article.get("_source") or "Unknown")
    if publisher and publisher.lower() != collector.lower():
        return f"{collector} | {publisher}"
    return publisher or collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - load/unload model."""
    global analyzer, news_client, finnhub_client, twitter_client, googlenews_client, bingnews_client, secedgar_client, yahoofinance_client, finviz_client, financial_juice_client
    
    # Startup
    print("Starting up... Loading model and clients")
    history_db.init_db()
    # B4: Prune stale sentiment snapshots older than 90 days on each startup
    try:
        pruned = history_db.prune_old_snapshots(days=90)
        if pruned:
            print(f"[db_prune] Removed {pruned} snapshots older than 90 days")
    except Exception as e:
        print(f"[db_prune] Warning: {e}")
    try:
        analyzer = FinBERTAnalyzer()
        news_client = NewsAPIClient()
        finnhub_client = FinnhubClient()
        twitter_client = TwitterClient()
        googlenews_client = GoogleNewsClient()
        bingnews_client = BingNewsClient()
        secedgar_client = SECEDGARClient()
        yahoofinance_client = YahooFinanceClient()
        finviz_client = FinvizClient()
        financial_juice_client = FinancialJuiceClient()
        print("Startup complete - all services loaded")
    except Exception as e:
        print(f"Error during startup: {e}")
        # Still continue - health check will show issues
        analyzer = None
        news_client = NewsAPIClient()
        finnhub_client = FinnhubClient()
        twitter_client = TwitterClient()
        googlenews_client = GoogleNewsClient()
        bingnews_client = BingNewsClient()
        secedgar_client = SECEDGARClient()
        yahoofinance_client = YahooFinanceClient()
        finviz_client = FinvizClient()
        financial_juice_client = FinancialJuiceClient()
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Stock Sentiment Analysis API",
    description="API for analyzing stock sentiment using NewsAPI, Finnhub, Twitter, Google News, SEC EDGAR, Yahoo Finance, Finviz, and FinBERT",
    version="1.1.0",
    lifespan=lifespan
)

# CORS middleware
# allow_credentials=True is incompatible with allow_origins=["*"] per the CORS spec;
# browsers reject such responses. Use allow_credentials=False with wildcard origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Stock Sentiment Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    news_status = news_client.check_health() if news_client else "not_loaded"
    finnhub_status = finnhub_client.check_health() if finnhub_client else "not_loaded"
    twitter_status = twitter_client.check_health() if twitter_client else "not_loaded"
    googlenews_status = googlenews_client.check_health() if googlenews_client else "not_loaded"
    bingnews_status = bingnews_client.check_health() if bingnews_client else "not_loaded"
    secedgar_status = secedgar_client.check_health() if secedgar_client else "not_loaded"
    yahoofinance_status = yahoofinance_client.check_health() if yahoofinance_client else "not_loaded"
    finviz_status = finviz_client.check_health() if finviz_client else "not_loaded"
    financialjuice_status = financial_juice_client.check_health() if financial_juice_client else "not_loaded"
    model_loaded = analyzer.is_loaded if analyzer else False
    
    # Determine overall status
    core_services = [news_status, finnhub_status]
    if all(s == "healthy" for s in core_services) and model_loaded:
        status = "healthy"
    elif not model_loaded:
        status = "degraded_model_unavailable"
    else:
        status = "degraded"
    
    return {
        "status": status,
        "news_api": news_status,
        "finnhub": finnhub_status,
        "twitter": twitter_status,
        "googlenews": googlenews_status,
        "bingnews": bingnews_status,
        "secedgar": secedgar_status,
        "yahoofinance": yahoofinance_status,
        "finviz": finviz_status,
        "financialjuice": financialjuice_status,
        "model_loaded": model_loaded
    }


@app.post("/api/analyze", response_model=SentimentResponse)
async def analyze_stock(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze sentiment for a stock using news from multiple sources.
    
    - **ticker**: Stock ticker symbol (e.g., "AAPL")
    - **company_name**: Company name (e.g., "Apple Inc.")
    
    Returns sentiment analysis with article breakdown.
    Results are cached for 1 hour — repeat calls within that window return instantly.
    """
    # ── TTL Cache check — return instantly on cache hit ───────────────────────
    cache_key = f"{request.ticker.upper()}:{request.company_name or ''}"
    cached = sentiment_cache.get(cache_key)
    if cached is not None:
        return cached

    if not analyzer or not analyzer.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Sentiment analyzer model is not loaded. Please try again later."
        )
    
    try:
        source_tasks = {
            "newsapi": asyncio.create_task(_run_source_call(
                "newsapi",
                news_client.get_company_news,
                ticker=request.ticker,
                company_name=request.company_name,
                days_back=7,
                max_articles=20,
            )),
            "finnhub": asyncio.create_task(_run_source_call(
                "finnhub",
                finnhub_client.get_company_news,
                ticker=request.ticker,
                days_back=7,
            )),
            "googlenews": asyncio.create_task(_run_source_call(
                "googlenews",
                googlenews_client.search_news,
                ticker=request.ticker,
                company_name=request.company_name,
                max_articles=20,
            )),
            "bingnews": asyncio.create_task(_run_source_call(
                "bingnews",
                bingnews_client.search_news,
                ticker=request.ticker,
                company_name=request.company_name,
                max_articles=20,
            )),
            "yahoofinance": asyncio.create_task(_run_source_call(
                "yahoofinance",
                yahoofinance_client.get_news,
                ticker=request.ticker,
                max_articles=20,
            )),
            "finviz": asyncio.create_task(_run_source_call(
                "finviz",
                finviz_client.get_news,
                ticker=request.ticker,
            )),
            "secedgar": asyncio.create_task(_run_source_call(
                "secedgar",
                secedgar_client.get_deep_dive_filings,
                ticker=request.ticker,
            )),
            "financialjuice": asyncio.create_task(_run_source_call(
                "financialjuice",
                financial_juice_client.get_company_news,
                ticker=request.ticker,
                company_name=request.company_name,
                max_articles=20,
            )),
        }
        if twitter_client.is_configured():
            source_tasks["twitter"] = asyncio.create_task(_run_source_call(
                "twitter",
                twitter_client.search_tweets,
                ticker=request.ticker,
                company_name=request.company_name,
                max_results=25,
            ))

        source_results = {
            name: await task for name, task in source_tasks.items()
        }

        newsapi_articles = source_results.get("newsapi", [])
        finnhub_articles = source_results.get("finnhub", [])
        googlenews_articles = source_results.get("googlenews", [])
        bingnews_articles = source_results.get("bingnews", [])
        yahoofinance_articles = source_results.get("yahoofinance", [])
        finviz_articles = source_results.get("finviz", [])
        secedgar_articles = source_results.get("secedgar", [])
        financialjuice_articles = source_results.get("financialjuice", [])
        twitter_articles = source_results.get("twitter", [])
        
        # Add source tracking
        for article in newsapi_articles:
            article["_source"] = "newsapi"
        
        for article in finnhub_articles:
            article["_source"] = "finnhub"
        
        for article in googlenews_articles:
            article["_source"] = "googlenews"
        
        for article in bingnews_articles:
            article["_source"] = "bingnews"
        
        for article in yahoofinance_articles:
            article["_source"] = "yahoofinance"
        
        for article in finviz_articles:
            article["_source"] = "finviz"
        
        for article in secedgar_articles:
            article["_source"] = "secedgar"
        
        for article in financialjuice_articles:
            article["_source"] = "financialjuice"
        
        for article in twitter_articles:
            article["_source"] = "twitter"
        
        # Combine all sources
        all_articles = (
            newsapi_articles + 
            finnhub_articles + 
            googlenews_articles + 
            bingnews_articles +
            yahoofinance_articles + 
            finviz_articles + 
            secedgar_articles + 
            financialjuice_articles +
            twitter_articles
        )
        
        if not all_articles:
            raise HTTPException(
                status_code=404,
                detail=f"No news articles found for {request.ticker} ({request.company_name})"
            )

        # Strict matching: dedup across sources + domain whitelist + title relevance
        filtered_articles, filter_stats = filter_articles(
            all_articles,
            ticker=request.ticker,
            company_name=request.company_name,
        )

        if not filtered_articles:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No relevant articles found for {request.ticker} ({request.company_name}) "
                    f"after filtering. {filter_stats['input']} articles were fetched but all "
                    f"were dropped as duplicates, untrusted domains, or off-topic."
                )
            )

        # Analyze sentiment with FinBERT-confidence relevance pre-filter
        analyzed_articles, metrics = analyzer.analyze_articles(
            filtered_articles,
            min_confidence=0.40,  # drop articles where FinBERT is uncertain (likely off-topic)
        )
        # Surface filter stats alongside analyzer metrics
        metrics["filter_stats"] = filter_stats
        metrics["finbert_relevance_dropped"] = metrics.get("relevance_dropped", 0)
        
        # Build response articles
        response_articles = []
        for article in analyzed_articles:
            title = article.get("title") or ""
            source = _format_article_source(article)
            published_at = article.get("published_at") or ""
            url = article.get("url") or ""
            description = article.get("description") or ""
            response_articles.append(ArticleSentiment(
                title=title,
                source=source,
                published_at=published_at,
                sentiment=SentimentLabel(article.get("sentiment", "neutral")),
                score=round(article.get("sentiment_score", 0), 3),
                url=url,
                summary=description[:200],
                description=description,
                impact_score=round(article.get("impact_score", 0.0), 4)
            ))
        
        # Sort by published date (most recent first)
        response_articles.sort(key=lambda x: x.published_at or "", reverse=True)
        
        # Calculate sources breakdown
        sources_breakdown = {
            "newsapi": sum(1 for a in analyzed_articles if a.get("_source") == "newsapi"),
            "finnhub": sum(1 for a in analyzed_articles if a.get("_source") == "finnhub"),
            "googlenews": sum(1 for a in analyzed_articles if a.get("_source") == "googlenews"),
            "bingnews": sum(1 for a in analyzed_articles if a.get("_source") == "bingnews"),
            "yahoofinance": sum(1 for a in analyzed_articles if a.get("_source") == "yahoofinance"),
            "finviz": sum(1 for a in analyzed_articles if a.get("_source") == "finviz"),
            "secedgar": sum(1 for a in analyzed_articles if a.get("_source") == "secedgar"),
            "financialjuice": sum(1 for a in analyzed_articles if a.get("_source") == "financialjuice"),
            "twitter": sum(1 for a in analyzed_articles if a.get("_source") == "twitter")
        }
        
        # Build metrics (include filter pipeline stats for transparency)
        fs = metrics.get("filter_stats") or {}
        
        # Compute enhanced metrics
        contrarian_result = compute_contrarian_signal(
            avg_sentiment=metrics["average_score"],
            confidence=metrics["confidence"],
            total_articles=metrics["total"],
        )
        contrarian_metrics = create_contrarian_metrics(contrarian_result)
        
        # Sector-relative metrics require cross-ticker sector sentiment data which
        # is not fetched in single-ticker requests — leave as None until implemented.
        sector_relative_metrics = None
        
        sentiment_metrics = SentimentMetrics(
            total_articles=metrics["total"],
            positive_count=metrics["positive"],
            negative_count=metrics["negative"],
            neutral_count=metrics["neutral"],
            avg_sentiment=round(metrics["average_score"], 3),
            sources_breakdown=sources_breakdown,
            filter_stats=FilterStats(
                input=fs.get("input", 0),
                dedup_dropped=fs.get("dedup_dropped", 0),
                domain_dropped=fs.get("domain_dropped", 0),
                title_dropped=fs.get("title_dropped", 0),
                ner_validation_dropped=fs.get("ner_validation_dropped", 0),
                finbert_relevance_dropped=metrics.get("relevance_dropped", 0),
                output=metrics["total"],
            ),
            contrarian=contrarian_metrics,
            sector_relative=sector_relative_metrics,
        )
        
        # Determine overall sentiment
        overall_sentiment = SentimentLabel(metrics["overall_sentiment"])
        confidence = round(metrics["confidence"], 3)
        
        # --- Keyword / Topic Extraction ---
        topics = None
        try:
            raw_topics = extract_keywords(analyzed_articles, top_n=20, min_count=2)
            if raw_topics:
                topics = [TopicKeyword(**t) for t in raw_topics]
        except Exception as e:
            print(f"Error extracting keywords: {e}")

        analyst_ratings_task = asyncio.create_task(_run_source_call(
            "analyst_ratings",
            yahoofinance_client.get_analyst_recommendations,
            request.ticker,
        ))
        price_history_task = asyncio.create_task(_run_source_call(
            "price_history",
            yahoofinance_client.get_price_history,
            request.ticker,
            period="1mo",
        ))
        ticker_info_task = asyncio.create_task(_run_source_call(
            "ticker_info",
            yahoofinance_client.get_ticker_info,
            request.ticker,
        ))

        # --- Analyst Ratings + Revision Velocity ---
        analyst_ratings = None
        analyst_revision = None
        try:
            raw_ratings = await analyst_ratings_task
            if raw_ratings:
                analyst_ratings = AnalystRatings(**raw_ratings)
                # Save snapshot for revision velocity tracking
                background_tasks.add_task(
                    history_db.save_analyst_snapshot,
                    ticker=request.ticker,
                    recommendation=raw_ratings.get("recommendation"),
                    target_mean=raw_ratings.get("target_mean_price"),
                    num_analysts=raw_ratings.get("num_analysts", 0),
                )
            # Compute revision velocity from historical snapshots
            analyst_history = history_db.get_analyst_history(request.ticker, days=10)
            if len(analyst_history) >= 2:
                analyst_revision = compute_analyst_revision_velocity(analyst_history)
        except Exception as e:
            print(f"Error fetching analyst ratings: {e}")

        # --- Price data + Correlation ---
        price_data = None
        correlation = None
        try:
            price_history = await price_history_task
            if price_history:
                ticker_info = await ticker_info_task
                current_price = ticker_info.get("price", 0) if ticker_info else 0

                if len(price_history) >= 2:
                    prev_close = price_history[-2]["close"]
                    price_change = current_price - prev_close
                    price_change_pct = (price_change / prev_close) * 100 if prev_close else 0
                else:
                    price_change = 0
                    price_change_pct = 0

                price_data = StockPriceData(
                    current_price=current_price,
                    price_change=round(price_change, 2),
                    price_change_percent=round(price_change_pct, 2),
                    history=[PriceDataPoint(**day) for day in price_history[-30:]]
                )

                # Build daily sentiment map from analyzed articles
                daily_sentiment_map: dict = {}
                for art in analyzed_articles:
                    pub = art.get("published_at", "")
                    score = art.get("sentiment_score")
                    if pub and score is not None:
                        try:
                            day_key = pub[:10]
                            if day_key not in daily_sentiment_map:
                                daily_sentiment_map[day_key] = []
                            daily_sentiment_map[day_key].append(float(score))
                        except Exception:
                            pass
                daily_sentiment_avg = {
                    d: sum(v) / len(v) for d, v in daily_sentiment_map.items()
                }

                corr_data = compute_correlation(price_history[-30:], daily_sentiment_avg)
                correlation = PriceCorrelation(
                    pearson_r=corr_data["pearson_r"],
                    divergence_alert=corr_data["divergence_alert"],
                    divergence_direction=corr_data.get("divergence_direction"),
                    lead_lag=[LeadLagPoint(**ll) for ll in corr_data["lead_lag"]],
                )
        except Exception as e:
            print(f"Error fetching price / correlation data: {e}")
            price_data = None
            correlation = None

        response = SentimentResponse(
            ticker=request.ticker,
            company_name=request.company_name,
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            low_coverage=metrics.get("low_coverage", False),
            metrics=sentiment_metrics,
            articles=response_articles,
            price_data=price_data,
            topics=topics,
            analyst_ratings=analyst_ratings,
            analyst_revision=analyst_revision,
            correlation=correlation,
        )

        # ── Cache the result for 1 hour ───────────────────────────────────────
        sentiment_cache.set(cache_key, response)

        # ── Save DB snapshot in background (don't block HTTP response) ────────
        _contrarian = sentiment_metrics.contrarian
        _sector_rel = sentiment_metrics.sector_relative
        _snap_kwargs = dict(
            ticker=request.ticker,
            avg_sentiment=metrics["average_score"],
            overall_sentiment=metrics["overall_sentiment"],
            confidence=metrics["confidence"],
            total_articles=metrics["total"],
            positive_count=metrics["positive"],
            negative_count=metrics["negative"],
            neutral_count=metrics["neutral"],
            contrarian_signal=_contrarian.signal.value if _contrarian else None,
            sentiment_percentile=_contrarian.sentiment_percentile if _contrarian else None,
            sector_etf=_sector_rel.sector_etf if _sector_rel else None,
            sector_sentiment=_sector_rel.sector_sentiment if _sector_rel else None,
            relative_sentiment=_sector_rel.relative_sentiment if _sector_rel else None,
            percentile_vs_sector=_sector_rel.percentile_vs_sector if _sector_rel else None,
        )

        def _save_snapshot(**kwargs):
            try:
                history_db.save_snapshot(**kwargs)
            except Exception as e:
                print(f"Error saving history snapshot: {e}")

        background_tasks.add_task(_save_snapshot, **_snap_kwargs)

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing {request.ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@app.post("/api/alerts")
async def check_sentiment_alerts(tickers: list[str]):
    """Check for major sentiment shifts (>0.3 delta) for a list of tickers.

    Returns tickers that have triggered an alert based on their last two
    sentiment snapshots. The harness can call this to pause trading on
    news-event-driven sentiment spikes.

    - **tickers**: List of ticker symbols to check (e.g. ["AAPL", "MSFT"])
    """
    alerts = []
    for ticker in tickers:
        try:
            history = history_db.get_history(ticker.upper(), limit=3)
            if len(history) < 2:
                continue
            latest_score = history[0].get("avg_sentiment", 0.0)
            prev_score = history[1].get("avg_sentiment", 0.0)
            delta = latest_score - prev_score
            if abs(delta) >= 0.3:
                alerts.append({
                    "ticker": ticker.upper(),
                    "delta": round(delta, 3),
                    "direction": "positive" if delta > 0 else "negative",
                    "latest_sentiment": round(latest_score, 3),
                    "prev_sentiment": round(prev_score, 3),
                    "captured_at": history[0].get("captured_at"),
                    "alert": True,
                })
        except Exception as e:
            print(f"[alerts] Error checking {ticker}: {e}")
    return {"alerts": alerts, "count": len(alerts)}


@app.get("/api/cache")
async def cache_stats():
    """Return TTL cache statistics (entries, keys, TTL)."""
    return sentiment_cache.stats()


@app.delete("/api/cache/{ticker}")
async def cache_invalidate(ticker: str):
    """Invalidate cached result for a specific ticker (forces fresh analysis on next call)."""
    sentiment_cache.delete(f"{ticker.upper()}:")
    sentiment_cache.delete(f"{ticker.upper()}")
    return {"invalidated": ticker.upper()}


@app.get("/api/sources")
async def get_sources():
    """Get information about configured data sources."""
    return {
        "sources": [
            {
                "name": "NewsAPI",
                "description": "Global news from 80,000+ sources",
                "url": "https://newsapi.org",
                "status": news_client.check_health() if news_client else "unknown",
                "requires_api_key": True
            },
            {
                "name": "Finnhub",
                "description": "Financial data and news for stocks",
                "url": "https://finnhub.io",
                "status": finnhub_client.check_health() if finnhub_client else "unknown",
                "requires_api_key": True
            },
            {
                "name": "Twitter/X",
                "description": "Real-time tweets and social sentiment",
                "url": "https://developer.twitter.com",
                "status": twitter_client.check_health() if twitter_client else "unknown",
                "requires_api_key": True,
                "configured": twitter_client.is_configured() if twitter_client else False
            },
            {
                "name": "Google News",
                "description": "RSS news feeds from Google News",
                "url": "https://news.google.com",
                "status": googlenews_client.check_health() if googlenews_client else "unknown",
                "requires_api_key": False
            },
            {
                "name": "SEC EDGAR",
                "description": "SEC filings and regulatory documents",
                "url": "https://www.sec.gov/edgar",
                "status": secedgar_client.check_health() if secedgar_client else "unknown",
                "requires_api_key": False
            },
            {
                "name": "Yahoo Finance",
                "description": "Stock news and financial data",
                "url": "https://finance.yahoo.com",
                "status": yahoofinance_client.check_health() if yahoofinance_client else "unknown",
                "requires_api_key": False
            },
            {
                "name": "Finviz",
                "description": "Insider trading and stock screening data",
                "url": "https://finviz.com",
                "status": finviz_client.check_health() if finviz_client else "unknown",
                "requires_api_key": False
            }
        ],
        "model": {
            "name": "FinBERT",
            "description": "Financial sentiment analysis model from ProsusAI",
            "loaded": analyzer.is_loaded if analyzer else False
        }
    }


@app.get("/api/history/{ticker}", response_model=HistoryResponse)
async def get_sentiment_history(ticker: str, limit: int = 90):
    """Return historical sentiment snapshots for a ticker.

    Each snapshot is one completed ``POST /api/analyze`` call stored in the
    local SQLite database (``backend/sentiment_history.db``).

    - **ticker**: Stock ticker symbol (case-insensitive)
    - **limit**: Maximum number of snapshots to return (newest first, default 90)
    """
    try:
        rows = history_db.get_history(ticker.upper(), limit=min(limit, 365))
        snapshots = [HistorySnapshot(**r) for r in rows]
        return HistoryResponse(
            ticker=ticker.upper(),
            snapshots=snapshots,
            count=len(snapshots),
        )
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.post("/api/comprehensive", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
):
    """Run a comprehensive deep-dive report on a single ticker.

    This endpoint is meant to be invoked through the harness CLI only. It returns:

    - **current_data**: live price, bid/ask, volume vs average, 52-week range
    - **deep_research**: revenue/earnings trend, balance sheet, competitors, risks,
      business operations, and future growth outlook
    - **news_check**: recent material news and developments
    """
    try:
        if yahoofinance_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Yahoo Finance client is not available.",
            )
        report = comprehensive.run_comprehensive_analysis(request.ticker, yahoofinance_client)
        return ComprehensiveAnalysisResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in comprehensive analysis for {request.ticker}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive analysis failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
