"""
Yahoo Finance client using yfinance library.
No API key required - uses web scraping.
Provides stock data and news from Yahoo Finance.
"""
import yfinance as yf
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime


class YahooFinanceClient:
    """Yahoo Finance client for stock data and news."""
    
    def __init__(self):
        pass
    
    def get_ticker_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive ticker information.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with company info
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "price": info.get("currentPrice", 0),
                "target_price": info.get("targetMeanPrice", 0),
                "recommendation": info.get("recommendationKey", ""),
                "num_analysts": info.get("numberOfAnalystOpinions", 0),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "country": info.get("country", ""),
                "employees": info.get("fullTimeEmployees", 0)
            }
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance info: {e}")
            return None
    
    def _get_news_rss(self, ticker: str, max_articles: int = 20) -> List[Dict]:
        """Fetch news via Yahoo Finance RSS feed as fallback."""
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            channel = root.find("channel")
            if channel is None:
                return []
            
            articles = []
            for item in channel.findall("item")[:max_articles]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                description = item.findtext("description", "").strip()
                pub_date_str = item.findtext("pubDate", "").strip()
                source_elem = item.find("source")
                source = source_elem.text.strip() if source_elem is not None and source_elem.text else "Yahoo Finance"
                
                # Parse RFC 2822 date
                pub_date = ""
                if pub_date_str:
                    try:
                        dt = parsedate_to_datetime(pub_date_str)
                        pub_date = dt.isoformat()
                    except Exception:
                        pub_date = pub_date_str
                
                if title:
                    articles.append({
                        "title": title,
                        "description": description,
                        "content": description,
                        "url": link,
                        "source": source,
                        "published_at": pub_date,
                        "author": "",
                        "_source": "yahoofinance"
                    })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance RSS: {e}")
            return []
    
    def get_news(self, ticker: str, max_articles: int = 20) -> List[Dict]:
        """
        Fetch news from Yahoo Finance for a ticker.
        Tries yfinance library first, falls back to RSS feed.
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum articles to return
        
        Returns:
            List of article dictionaries
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            normalized = []
            if news:
                for article in news[:max_articles]:
                    title = article.get("title", "").strip()
                    if not title:
                        continue  # Skip articles with no title
                    
                    # Yahoo provides Unix timestamp in milliseconds
                    pub_timestamp = article.get("published", 0)
                    if pub_timestamp:
                        pub_date = datetime.fromtimestamp(pub_timestamp / 1000).isoformat() + "Z"
                    else:
                        pub_date = ""
                    
                    publisher = article.get("publisher", "Yahoo Finance")
                    
                    normalized.append({
                        "title": title,
                        "description": article.get("summary", ""),
                        "content": article.get("summary", ""),
                        "url": article.get("link", ""),
                        "source": publisher,
                        "published_at": pub_date,
                        "author": "",
                        "_source": "yahoofinance",
                        "_thumbnail": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "")
                    })
            
            # Fall back to RSS if yfinance returned nothing or only empty articles
            if not normalized:
                print(f"yfinance news empty for {ticker}, falling back to RSS")
                normalized = self._get_news_rss(ticker, max_articles)
            
            return normalized
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance news via yfinance: {e}, trying RSS fallback")
            return self._get_news_rss(ticker, max_articles)
    
    def get_analyst_recommendations(self, ticker: str) -> Optional[Dict]:
        """Get analyst recommendations for a stock.

        Handles both the legacy list-of-dicts format and the newer DataFrame
        format returned by recent yfinance versions.

        Returns:
            Dict with recommendation, target prices, analyst counts, or None on failure.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            rec_key = info.get("recommendationKey", "")
            target_mean = info.get("targetMeanPrice") or info.get("targetMeanPrice")
            target_high = info.get("targetHighPrice")
            target_low = info.get("targetLowPrice")
            num_analysts = info.get("numberOfAnalystOpinions", 0) or 0

            strong_buy = buy = hold = sell = strong_sell = 0

            # yfinance >= 0.2 returns recommendationTrend as a DataFrame
            try:
                rec_trend = stock.recommendations
                if rec_trend is not None and hasattr(rec_trend, "iloc") and len(rec_trend) > 0:
                    latest = rec_trend.iloc[0]
                    strong_buy  = int(latest.get("strongBuy",  latest.get("strong_buy",  0)) or 0)
                    buy         = int(latest.get("buy",                                    0) or 0)
                    hold        = int(latest.get("hold",                                   0) or 0)
                    sell        = int(latest.get("sell",                                   0) or 0)
                    strong_sell = int(latest.get("strongSell", latest.get("strong_sell", 0)) or 0)
            except Exception:
                pass

            # Fallback: legacy info-dict format
            if strong_buy == buy == hold == sell == strong_sell == 0:
                trend_raw = info.get("recommendationTrend", [])
                if isinstance(trend_raw, list) and trend_raw:
                    first = trend_raw[0] if isinstance(trend_raw[0], dict) else {}
                    strong_buy  = int(first.get("strongBuy",  0) or 0)
                    buy         = int(first.get("buy",         0) or 0)
                    hold        = int(first.get("hold",        0) or 0)
                    sell        = int(first.get("sell",        0) or 0)
                    strong_sell = int(first.get("strongSell",  0) or 0)

            return {
                "recommendation":   rec_key,
                "target_mean_price": float(target_mean) if target_mean else None,
                "target_high_price": float(target_high) if target_high else None,
                "target_low_price":  float(target_low)  if target_low  else None,
                "num_analysts":  num_analysts,
                "strong_buy":    strong_buy,
                "buy":           buy,
                "hold":          hold,
                "sell":          sell,
                "strong_sell":   strong_sell,
            }

        except Exception as e:
            print(f"Error fetching analyst recommendations: {e}")
            return None
    
    def get_price_history(
        self, 
        ticker: str, 
        period: str = "1mo"
    ) -> Optional[List[Dict]]:
        """
        Get historical price data for correlation analysis.
        
        Args:
            ticker: Stock ticker
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            List of price data points
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.isoformat(),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"])
                })
            
            return data
            
        except Exception as e:
            print(f"Error fetching price history: {e}")
            return None
    
    def check_health(self) -> str:
        """Check if Yahoo Finance is accessible."""
        try:
            # Try to fetch a well-known stock
            stock = yf.Ticker("AAPL")
            info = stock.info
            
            if info and info.get("symbol") == "AAPL":
                return "healthy"
            else:
                return "degraded"
                
        except Exception as e:
            print(f"Yahoo Finance health check failed: {e}")
            return "unreachable"
