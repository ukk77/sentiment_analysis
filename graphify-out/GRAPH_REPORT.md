# Graph Report - sentiment_analysis  (2026-05-06)

## Corpus Check
- 42 files · ~18,116 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 286 nodes · 353 edges · 28 communities (26 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 22|Community 22]]

## God Nodes (most connected - your core abstractions)
1. `analyze_stock()` - 15 edges
2. `SECEDGARClient` - 12 edges
3. `Implementation Notes` - 11 edges
4. `Stock Sentiment Analysis Bot` - 11 edges
5. `lifespan()` - 10 edges
6. `FinvizClient` - 10 edges
7. `YahooFinanceClient` - 10 edges
8. `FinnhubClient` - 9 edges
9. `Stock Sentiment Analysis Bot - Features & Improvements Roadmap` - 9 edges
10. `FinBERTAnalyzer` - 8 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --calls--> `FinBERTAnalyzer`  [INFERRED]
  backend/app/main.py → backend/app/services/analyzer.py
- `lifespan()` --calls--> `FinnhubClient`  [INFERRED]
  backend/app/main.py → backend/app/services/finnhub.py
- `lifespan()` --calls--> `TwitterClient`  [INFERRED]
  backend/app/main.py → backend/app/services/twitter.py
- `lifespan()` --calls--> `GoogleNewsClient`  [INFERRED]
  backend/app/main.py → backend/app/services/googlenews.py
- `lifespan()` --calls--> `SECEDGARClient`  [INFERRED]
  backend/app/main.py → backend/app/services/secedgar.py

## Communities (28 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (9): AnalystRatings(), recStyle(), PEARSON_COLOR(), PriceSentimentChart(), SENTIMENT_COLOR(), SentimentHistory(), analyzeStock(), checkHealth() (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (26): analyze_stock(), get_sentiment_history(), get_sources(), health_check(), Health check endpoint., Analyze sentiment for a stock using news from multiple sources.          - **tic, Get information about configured data sources., Return historical sentiment snapshots for a ticker.      Each snapshot is one co (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (15): FinBERTAnalyzer, Analyze sentiment of a news article.                  Args:             article:, Analyze sentiment for multiple articles.          Args:             articles: Li, Sentiment analyzer using FinBERT model from Hugging Face.     FinBERT is specifi, Load the FinBERT model and tokenizer., Analyze sentiment of a single text.                  Args:             text: Tex, SentimentResult, clean_text() (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (12): SEC EDGAR API client for fetching company filings. No API key required. Rate lim, Fetch 8-K, 10-K, and 10-Q filings over 30 days.          For 10-K/10-Q, fetches, Get 8-K filings over the last 30 days (expanded from 14)., Download and strip the primary filing document.          Returns plain text (up, Resolve ticker → 10-digit zero-padded CIK., Fetch the EDGAR submissions JSON for a CIK., Check if SEC EDGAR API is accessible., Strip HTML tags and collapse whitespace. (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (19): _build_ticker_pattern(), deduplicate_articles(), _domain_matches_trusted(), filter_articles(), _get_domain(), _normalize_title(), passes_domain_whitelist(), passes_title_relevance() (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (19): Analyst Ratings Integration ✅, Article Impact Scoring ✅, Data Source Status, Finviz Integration ✅, High Priority, Historical Tracking ✅, Implementation Notes, Implemented Features ✓ (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (19): Additional Free Sources (Recommended), API Endpoints, API Sources, Architecture, Backend Setup, code:block1 (sentiment_analysis/), code:bash (cd backend), code:bash (cd frontend) (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (9): FinvizClient, Finviz client for insider trading and analyst ratings. Uses Playwright headless, Get recent insider trading transactions using Playwright., Get news from Finviz using Playwright., Finviz client using Playwright headless browser., Get stock screening data using Playwright., Check if Finviz is accessible via Playwright., Enforce rate limiting. (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (9): Yahoo Finance client using yfinance library. No API key required - uses web scra, Fetch news from Yahoo Finance for a ticker.         Tries yfinance library first, Yahoo Finance client for stock data and news., Get analyst recommendations for a stock.          Handles both the legacy list-o, Get comprehensive ticker information.                  Args:             ticker:, Get historical price data for correlation analysis.                  Args:, Check if Yahoo Finance is accessible., Fetch news via Yahoo Finance RSS feed as fallback. (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (9): Config, get_settings(), Settings, lifespan(), Manage application lifespan - load/unload model., BaseSettings, NewsAPIClient, Fetch news articles for a company using ticker and company name. (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.2
Nodes (7): FinnhubClient, Check if Finnhub API is accessible., Make authenticated request to Finnhub API., Fetch company news from Finnhub.                  Args:             ticker: Stoc, Get company profile information., Get real-time quote for a stock., Get basic financial metrics.

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (6): GoogleNewsClient, Google News RSS client - no API key required. Uses RSS feeds to fetch news headl, Get news for a specific topic (e.g., 'business', 'technology')., Google News RSS client for fetching stock-related news., Check if Google News RSS is accessible., Fetch news from Google News RSS.                  Args:             ticker: Stoc

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (6): Twitter/X API v2 client for sentiment analysis. Free tier: 100 posts/month, 500, Check if Twitter API is accessible., Twitter/X API v2 client for fetching stock-related tweets., Check if Twitter API is configured., Search for tweets about a stock/company.                  Args:             tick, TwitterClient

### Community 13 - "Community 13"
Cohesion: 0.36
Nodes (8): _get_conn(), get_history(), init_db(), SQLite-based historical sentiment tracking.  Free, zero-config, file-based stora, Create tables and indexes if they don't exist., Persist one analysis snapshot for a ticker., Return the last *limit* snapshots for *ticker*, newest first., save_snapshot()

### Community 14 - "Community 14"
Cohesion: 0.4
Nodes (5): compute_correlation(), _pearson_r(), Price–sentiment correlation metrics.  Uses numpy (already in requirements) — no, Compute Pearson r. Returns None if insufficient variance or data., Compute price–sentiment correlation metrics.      Args:         price_history: L

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (3): Diagnostic test for Yahoo Finance, Finviz, and SEC EDGAR sources., Test individual news sources., test_sources()

### Community 16 - "Community 16"
Cohesion: 0.5
Nodes (3): extract_keywords(), Keyword / topic extraction from analyzed articles.  No external NLP dependencies, Extract top *top_n* keywords from article titles + descriptions.      Args:

## Knowledge Gaps
- **111 isolated node(s):** `Debug individual source responses.`, `Diagnostic test for Yahoo Finance, Finviz, and SEC EDGAR sources.`, `Test individual news sources.`, `Config`, `Manage application lifespan - load/unload model.` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `lifespan()` connect `Community 9` to `Community 1`, `Community 2`, `Community 3`, `Community 7`, `Community 8`, `Community 10`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.329) - this node is a cross-community bridge._
- **Why does `analyze_stock()` connect `Community 1` to `Community 4`, `Community 14`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Why does `FinBERTAnalyzer` connect `Community 2` to `Community 9`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `analyze_stock()` (e.g. with `filter_articles()` and `ArticleSentiment`) actually correct?**
  _`analyze_stock()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Debug individual source responses.`, `Diagnostic test for Yahoo Finance, Finviz, and SEC EDGAR sources.`, `Test individual news sources.` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._