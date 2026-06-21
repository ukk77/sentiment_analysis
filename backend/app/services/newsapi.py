import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import get_settings


_rate_limited = False  # module-level flag: set True on first 429, skips rest of batch


class NewsAPIClient:
    BASE_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self):
        self.api_key = get_settings().NEWS_API_KEY
    
    def get_company_news(
        self, 
        ticker: str, 
        company_name: str,
        days_back: int = 7,
        max_articles: int = 20
    ) -> List[Dict]:
        """
        Fetch news articles for a company using ticker and company name.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            company_name: Company name (e.g., 'Apple')
            days_back: Number of days to look back
            max_articles: Maximum number of articles to return
        
        Returns:
            List of article dictionaries
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build query - use both ticker and company name
        # Use quotes around company name for exact matching when relevant
        query_parts = [f"{ticker}", f"{company_name}"]
        query = " OR ".join(query_parts)
        
        params = {
            "q": query,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": min(max_articles, 100),  # NewsAPI max is 100
            "apiKey": self.api_key
        }
        
        global _rate_limited
        if _rate_limited:
            return []

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            if response.status_code == 429:
                _rate_limited = True
                print("Error fetching NewsAPI data: 429 Too Many Requests — quota exhausted, skipping NewsAPI for remainder of batch")
                return []
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get("articles", [])
            
            # Normalize the article format
            normalized = []
            for article in articles:
                normalized.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", ""),
                    "author": article.get("author", "")
                })
            
            return normalized
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NewsAPI data: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error with NewsAPI: {e}")
            return []
    
    def check_health(self) -> str:
        """Check if NewsAPI is accessible."""
        try:
            # Make a minimal request to check connectivity
            params = {
                "q": "test",
                "pageSize": 1,
                "apiKey": self.api_key
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                return "healthy"
            elif response.status_code == 401:
                return "invalid_api_key"
            elif response.status_code == 429:
                return "rate_limited"
            else:
                return f"error_{response.status_code}"
                
        except requests.exceptions.RequestException:
            return "unreachable"
