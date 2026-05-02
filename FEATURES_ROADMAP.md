# Stock Sentiment Analysis Bot - Features & Improvements Roadmap

## Implemented Features ✓

- [x] Multi-source news aggregation (NewsAPI, Finnhub, Google News, Yahoo Finance, Finviz, SEC EDGAR, Twitter)
- [x] FinBERT sentiment analysis with confidence scores
- [x] Web dashboard with sentiment gauge and metrics
- [x] Hugging Face authenticated model access
- [x] Article-level sentiment breakdown
- [x] Source distribution tracking
- [x] **Stock Price Correlation** — Price/sentiment dual-axis chart with volume bars
- [x] **Article Impact Scoring** — Per-article impact score (`|score − avg| × confidence`), impact bar + tier badge on each card, sort by impact/score/recent
- [x] **Finviz Integration Fix** — Playwright subprocess bypasses Cloudflare; ~20 articles per ticker
- [x] **Yahoo Finance RSS Fallback** — RSS feed used when yfinance returns no valid articles; ~10–20 articles per ticker
- [x] **Real Daily Sentiment Line** — Chart uses actual per-day avg sentiment from articles (replaced random mock data)
- [x] **Chart Date Filter** — Click any date on the price chart to filter articles to that day; ▼ marker + date badge + ✕ Reset button
- [x] **Strict Article Matching** — 5-stage filter pipeline (cross-source dedup → domain/publisher whitelist → ticker context regex → company alias map → FinBERT confidence relevance); ~40% noise reduction

---

## Data Source Status

| Source | Status | Articles (AAPL) | Notes |
|--------|--------|-----------------|-------|
| **NewsAPI** | ✅ Active | ~20 | Reliable, requires API key |
| **Finnhub** | ✅ Active | ~245 | Best coverage, requires API key |
| **Google News** | ✅ Active | ~20 | RSS-based, no API key needed |
| **Yahoo Finance** | ✅ Active | ~10-20 | yfinance + RSS fallback |
| **Finviz** | ✅ Active | ~20 | Playwright subprocess, no API key |
| **SEC EDGAR** | ✅ Active | 0-5 | 8-K + 10-K + 10-Q, 30-day window, body text fetch |
| **Twitter** | ⏸️ Not Configured | — | Requires Twitter API key |

---

## High Priority

| Feature | Description | Value | Status |
|---------|-------------|-------|--------|
| **Stock Price Correlation** | Overlay stock price chart with sentiment score | Validate if sentiment predicts price movements | ✅ Completed |
| **Article Impact Scoring** | Per-article impact score with visual bar; sort by impact | Identify which articles are driving overall sentiment | ✅ Completed |
| **Historical Tracking** | Store and display sentiment trends over days/weeks per stock | See if sentiment is improving or declining | ✅ Completed |
| **Multi-Stock Comparison** | Compare sentiment across 2-4 stocks side-by-side | Portfolio analysis, competitor comparison | ⏳ Planned |
| **Watchlist** | Save favorite tickers for quick re-analysis | Faster workflow for tracking stocks | ⏳ Planned |

---

## Price–Sentiment Correlation Upgrades

> The current chart overlays a static avg sentiment line on price. These upgrades make the correlation **real and actionable**.

| Feature | Description | Signal Value | Status |
|---------|-------------|--------------|--------|
| **Real Daily Sentiment Line** | Per-day avg sentiment from actual articles mapped onto price history; null gaps where no articles exist | Makes the chart meaningful | ✅ Completed |
| **Chart Date Filter** | Click a date on the chart → filters article list to that day; ▼ marker + date badge + ✕ Reset | Links price moves directly to news | ✅ Completed |
| **Correlation Coefficient (r)** | Pearson r between daily price returns and daily sentiment scores; shown as a badge on the chart | Quantifies how aligned they are | ✅ Completed |
| **High-Impact Article Markers** | Vertical `ReferenceLine` on price chart at dates of high-impact articles; hover shows title + sentiment | Directly links articles to price moves | ✅ Completed |
| **Lead/Lag Analysis** | Correlation table at offsets +1/+2/+3 days: does today's sentiment predict tomorrow's price? | Most actionable trading signal | ✅ Completed |
| **3-Day Rolling Sentiment Avg** | Smooth noisy daily sentiment line with a moving average overlay | Reveals sentiment trends | ✅ Completed |
| **Sentiment Divergence Alert** | Detect when price trend and sentiment trend diverge; show ⚠️ warning badge | Potential reversal signal | ✅ Completed |
| **Price Return vs Sentiment Scatter** | X = daily sentiment, Y = next-day price return — visual confirmation of predictive power | Validates the model for trading | ⏳ Planned |

---

## Medium Priority

| Feature | Description | Value | Status |
|---------|-------------|-------|--------|
| **Article Filtering** | Filter by source, sentiment, date range, keywords | Better noise reduction | ⏳ Planned |
| **Export Reports** | Download PDF/CSV of analysis results | Share with team, record keeping | ⏳ Planned |
| **Sentiment by Source Chart** | Bar chart showing sentiment breakdown per source | Understand which sources drive sentiment | ⏳ Planned |
| **Real-time Alerts** | Notify when sentiment shifts significantly (>20% change) | Trading signal | ⏳ Planned |
| **Keyword/Topic Extraction** | Show top mentioned topics (AI, earnings, lawsuit, etc.) | Understand *why* sentiment is positive/negative | ✅ Completed |

---

## Nice to Have

| Feature | Description | Value | Status |
|---------|-------------|-------|--------|
| **SEC Filing Deep Dive** | Extend EDGAR to 30 days + add 10-K/10-Q sentiment | Regulatory risk assessment | ✅ Completed |
| **Twitter Volume Metrics** | Tweet count, engagement stats alongside sentiment | Social momentum indicator | ⏳ Planned |
| **Analyst Ratings Integration** | Yahoo Finance analyst recommendations cross-validated with sentiment | Fundamental + sentiment combined signal | ✅ Completed |
| **Dark/Light Mode Toggle** | Theme switcher | User preference | ⏳ Planned |
| **Caching Layer** | In-memory cache for 15-min API results | Reduce API costs, faster response | ⏳ Planned |

---

## Technical Improvements

| Improvement | Impact | Status |
|-------------|--------|--------|
| **Background Jobs** | Async analysis for heavy requests (Celery/RQ) to avoid timeouts | ⏳ Planned |
| **Database Storage** | SQLite (stdlib, zero-config) for historical sentiment snapshots; upgrade path: Supabase/Turso/PlanetScale free tiers | ✅ Completed (SQLite) |
| **WebSocket Updates** | Real-time article streaming instead of single blocking request | ⏳ Planned |
| **API Rate Limiting** | Display remaining quota to users per source | ⏳ Planned |
| **Error Retry Logic** | Auto-retry failed source requests with exponential backoff | ⏳ Planned |

---

## Implementation Notes

### Strict Article Matching ✅
- **Problem**: Keyword-based sources (NewsAPI, Google News) return noisy results — "Apple" matches fruit/recipe content, short tickers (F, T, V) match random text
- **Solution**: 5-stage filter pipeline in `backend/app/services/article_filter.py`, runs after fetch but before sentiment analysis
- **Stage 1 — Cross-source dedup**: Normalize titles (lowercase, strip punctuation) + URL; dedupe both
- **Stage 2 — Domain / publisher whitelist** (keyword sources only):
  - `NewsAPI`: URL domain must be in `TRUSTED_DOMAINS` (Reuters, Bloomberg, CNBC, WSJ, etc.)
  - `Google News`: URL is a redirector, so instead check publisher name (`article.source`) against `TRUSTED_PUBLISHERS`
  - Ticker-bound sources (Finnhub, Yahoo, Finviz, SEC) skip this check (already curated)
- **Stage 3 — Ticker context regex**: Tickers ≥4 chars matched as bare word; short tickers (F, T, V, M) require financial context nearby (`stock`, `shares`, `earnings`, etc.) or `$TICKER`/`(TICKER)`/`NASDAQ:TICKER` format
- **Stage 4 — Company alias map**: `TICKER_ALIASES` dict with 80+ mega-caps (e.g. `META` → Facebook, Instagram, WhatsApp, Zuckerberg); user-provided `company_name` also checked; title must contain ≥1 alias
- **Stage 5 — FinBERT relevance pre-filter**: After sentiment scoring, drop articles where `max_prob < 0.40` (model is uncertain → likely off-topic)
- **Result on AAPL test**: 321 input → 188 output (41% noise reduction); stats surfaced in `metrics.filter_stats` for transparency

### Article Impact Scoring ✅
- **Formula**: `impact_score = |article_sentiment_score − overall_avg| × confidence` normalized to 0–1
- **Tiers**: High Impact ≥ 30%, Med Impact ≥ 15%, Low Impact < 15%
- **Backend**: `backend/app/services/analyzer.py` — computed after all articles are scored
- **Frontend**: `ArticleCard.jsx` — impact bar + tier label; `App.jsx` — sort controls (Recent / ⚡ Impact / 📊 Score)

### Stock Price Correlation ✅
- **Backend**: `get_price_history()` in `yahoofinance.py`, returned as `price_data` in `/api/analyze`
- **Frontend**: `PriceSentimentChart.jsx` — dual Y-axis Recharts component with volume bars
- **Real sentiment line**: `App.jsx` groups articles by date → daily avg → passed as `dailySentiment` prop; `null` for days with no coverage
- **Chart date filter**: Click handler on `ComposedChart` extracts `dateKey` from payload → `selectedDate` state in `App.jsx` → filters article list; blue `ReferenceLine` marks selected date; ✕ Reset clears filter

### Finviz Integration ✅
- **Problem**: Cloudflare blocks direct HTTP requests
- **Solution**: Playwright runs in an isolated subprocess (separate Python process + event loop)
- **HTML**: New 3-column `news_table-row` layout — icon | time | title
- **File**: `backend/app/services/finviz.py`

### Yahoo Finance RSS Fallback ✅
- **Problem**: `yfinance` library intermittently returns articles with empty titles
- **Solution**: `_get_news_rss()` parses `https://finance.yahoo.com/rss/headline?s={ticker}` via stdlib `urllib` + `xml.etree`
- **Logic**: Try yfinance first → fall back to RSS if no valid titles returned
- **File**: `backend/app/services/yahoofinance.py`

### SEC EDGAR Deep Dive ✅
- **Window**: 30 days (was 14)
- **Filing types**: 8-K + 10-K + 10-Q
- **Body text**: `_fetch_filing_text()` downloads primary document via EDGAR's `primaryDocument` field, strips HTML (BeautifulSoup), passes first 3 000 chars to FinBERT — capped at 3 fetches per request for speed
- **File**: `backend/app/services/secedgar.py` — `get_deep_dive_filings()`

### Keyword / Topic Extraction ✅
- **Approach**: Regex tokenisation + 120-word stop-list, no external NLP dependency
- **Output**: Top 20 keywords with `count` and `avg_sentiment`; colour-coded tag cloud in frontend
- **File**: `backend/app/services/keywords.py` — `extract_keywords()`; frontend `KeywordsPanel.jsx`

### Historical Tracking ✅
- **DB**: SQLite (`backend/sentiment_history.db`), Python stdlib `sqlite3`, auto-created on first run
- **Schema**: `sentiment_snapshots(ticker, captured_at, avg_sentiment, overall_sentiment, confidence, total_articles, …)`
- **Endpoint**: `GET /api/history/{ticker}?limit=90` — newest-first snapshots
- **Frontend**: `SentimentHistory.jsx` — line chart with colour-coded dots; trend delta vs previous run
- **Production upgrade path**: Supabase (free PostgreSQL), Turso (free SQLite edge), PlanetScale (free MySQL)
- **File**: `backend/app/services/db.py`

### Analyst Ratings Integration ✅
- **Source**: Yahoo Finance via `yfinance` — `stock.recommendations` (DataFrame) with legacy dict fallback
- **Fields**: consensus label, target mean/high/low prices, strong_buy/buy/hold/sell/strong_sell counts
- **Frontend**: `AnalystRatings.jsx` — consensus badge, price target range bar, animated breakdown bars
- **File**: `backend/app/services/yahoofinance.py` — `get_analyst_recommendations()`

### Price–Sentiment Correlation Upgrades ✅
- **Backend**: `backend/app/services/correlation.py` — `compute_correlation()` computes Pearson r, lead/lag (+1/+2/+3 days), divergence alert using numpy
- **Frontend** additions to `PriceSentimentChart.jsx`:
  - Pearson r badge (colour-coded: green > 0.3, red < −0.3, yellow otherwise)
  - 3-day rolling avg line (solid emerald) computed from `dailySentiment` map
  - High-impact article ⚡ markers (amber `ReferenceLine` for articles with `impact_score ≥ 0.3`)
  - Divergence ⚠️ alert badge with tooltip describing direction
  - Lead/lag mini table below the chart

---

*Last Updated: May 2025 — v2 features: Historical Tracking, Keyword/Topic Extraction, SEC Filing Deep Dive, Analyst Ratings, Correlation Upgrades*
