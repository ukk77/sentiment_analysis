"""
Twitter/X API v2 client for sentiment analysis.
Free tier: 100 posts/month, 500 posts/month with academic access
Get API keys at: https://developer.twitter.com/en/portal/dashboard
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.config import get_settings
import os


class TwitterClient:
    """Twitter/X API v2 client for fetching stock-related tweets."""
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self):
        # Twitter Bearer Token from environment or settings
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.headers = {}
        if self.bearer_token:
            self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
    
    def is_configured(self) -> bool:
        """Check if Twitter API is configured."""
        return bool(self.bearer_token)
    
    def search_tweets(
        self, 
        ticker: str, 
        company_name: str,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Search for tweets about a stock/company.
        
        Args:
            ticker: Stock ticker (e.g., '$MSFT' or 'MSFT')
            company_name: Company name to search
            max_results: Max tweets to return (free tier: max 25 per request)
        
        Returns:
            List of tweet dictionaries
        """
        if not self.is_configured():
            print("Twitter API not configured - set TWITTER_BEARER_TOKEN")
            return []
        
        # Build query - search for ticker with $ or company name
        # Cashtag ($) is commonly used for stocks on Twitter
        query_parts = [f"${ticker}", f"#{ticker}", company_name]
        query = " OR ".join([f'"{part}"' for part in query_parts])
        
        # Add filters to remove retweets and replies for cleaner data
        query += " -is:retweet -is:reply lang:en"
        
        params = {
            "query": query,
            "max_results": min(max_results, 100),  # API limit
            "tweet.fields": "created_at,author_id,public_metrics",
            "expansions": "author_id",
            "user.fields": "username,public_metrics"
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/tweets/search/recent",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 429:
                print("Twitter API rate limit exceeded")
                return []
            
            if response.status_code != 200:
                print(f"Twitter API error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            # Normalize to common article format
            normalized = []
            for tweet in tweets:
                author_id = tweet.get("author_id", "")
                author = users.get(author_id, {})
                username = author.get("username", "unknown")
                
                # Calculate influence score based on followers
                followers = author.get("public_metrics", {}).get("followers_count", 0)
                tweet_metrics = tweet.get("public_metrics", {})
                engagement = (
                    tweet_metrics.get("like_count", 0) + 
                    tweet_metrics.get("retweet_count", 0) +
                    tweet_metrics.get("reply_count", 0)
                )
                
                normalized.append({
                    "title": tweet.get("text", "")[:200],  # Truncate for title
                    "description": tweet.get("text", ""),
                    "content": tweet.get("text", ""),
                    "url": f"https://twitter.com/{username}/status/{tweet.get('id', '')}",
                    "source": f"Twitter/@{username}",
                    "published_at": tweet.get("created_at", ""),
                    "author": username,
                    "_source": "twitter",
                    "_metrics": {
                        "followers": followers,
                        "likes": tweet_metrics.get("like_count", 0),
                        "retweets": tweet_metrics.get("retweet_count", 0),
                        "engagement": engagement
                    }
                })
            
            return normalized
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Twitter data: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error with Twitter API: {e}")
            return []
    
    def check_health(self) -> str:
        """Check if Twitter API is accessible."""
        if not self.is_configured():
            return "not_configured"
        
        try:
            # Make a minimal request to check connectivity
            params = {"query": "test", "max_results": 1}
            response = requests.get(
                f"{self.BASE_URL}/tweets/search/recent",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return "healthy"
            elif response.status_code == 401:
                return "invalid_token"
            elif response.status_code == 429:
                return "rate_limited"
            else:
                return f"error_{response.status_code}"
                
        except requests.exceptions.RequestException:
            return "unreachable"
