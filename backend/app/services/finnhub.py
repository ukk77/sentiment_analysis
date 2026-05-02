import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from app.config import get_settings


class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self):
        self.api_key = get_settings().FINNHUB_API_KEY
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make authenticated request to Finnhub API."""
        if params is None:
            params = {}
        
        params["token"] = self.api_key
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Finnhub API error ({endpoint}): {e}")
            return None
        except Exception as e:
            print(f"Unexpected error with Finnhub ({endpoint}): {e}")
            return None
    
    def get_company_news(
        self, 
        ticker: str,
        days_back: int = 7
    ) -> List[Dict]:
        """
        Fetch company news from Finnhub.
        
        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back
        
        Returns:
            List of article dictionaries
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "symbol": ticker,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d")
        }
        
        data = self._make_request("company-news", params)
        
        if not data or not isinstance(data, list):
            return []
        
        # Normalize the article format
        normalized = []
        for article in data:
            if not article:
                continue
            
            # Convert Unix timestamp to ISO format
            timestamp = article.get("datetime", 0)
            if timestamp:
                published_at = datetime.fromtimestamp(timestamp).isoformat() + "Z"
            else:
                published_at = ""
            
            normalized.append({
                "title": article.get("headline", ""),
                "description": article.get("summary", ""),
                "content": article.get("summary", ""),  # Finnhub provides summary
                "url": article.get("url", ""),
                "source": article.get("source", "Finnhub"),
                "published_at": published_at,
                "author": "",  # Finnhub doesn't provide author
                "image": article.get("image", "")
            })
        
        return normalized
    
    def get_company_profile(self, ticker: str) -> Optional[Dict]:
        """Get company profile information."""
        return self._make_request("stock/profile2", {"symbol": ticker})
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get real-time quote for a stock."""
        return self._make_request("quote", {"symbol": ticker})
    
    def get_basic_financials(self, ticker: str) -> Optional[Dict]:
        """Get basic financial metrics."""
        return self._make_request("stock/metric", {
            "symbol": ticker,
            "metric": "all"
        })
    
    def check_health(self) -> str:
        """Check if Finnhub API is accessible."""
        try:
            # Make a simple request
            result = self._make_request("stock/profile2", {"symbol": "AAPL"})
            
            if result is not None:
                return "healthy"
            else:
                return "error"
                
        except requests.exceptions.RequestException:
            return "unreachable"
