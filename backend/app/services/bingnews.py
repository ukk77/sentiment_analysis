"""
Bing News RSS client - no API key required, no rate limits.
Uses RSS feeds to fetch news headlines via Bing News.
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime
from html import unescape


class BingNewsClient:
    """Bing News RSS client for fetching stock-related news."""
    
    BASE_URL = "https://www.bing.com/news/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
    
    def search_news(
        self, 
        ticker: str, 
        company_name: str,
        max_articles: int = 20
    ) -> List[Dict]:
        """
        Fetch news from Bing News RSS.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            max_articles: Maximum articles to return
        
        Returns:
            List of article dictionaries
        """
        # Build search query - use both ticker and company name
        query = f"{ticker} OR {company_name} stock"
        
        # Bing News RSS endpoint with format=rss
        params = {
            "q": query,
            "format": "rss",
            "count": min(max_articles, 50)  # Request enough articles
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            # Find all items (articles)
            items = root.findall(".//item")
            
            normalized = []
            for item in items[:max_articles]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                description_elem = item.find("description")
                
                title = unescape(title_elem.text) if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                description = unescape(description_elem.text) if description_elem is not None else ""
                
                # Parse pub date to ISO format
                if pub_date:
                    try:
                        # Parse RFC 2822 format
                        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                        pub_date = dt.isoformat() + "Z"
                    except Exception:
                        pass
                
                normalized.append({
                    "title": title,
                    "description": description,
                    "content": description,
                    "url": link,
                    "source": "Bing News",
                    "published_at": pub_date,
                    "author": "",  # RSS doesn't always provide author
                    "_source": "bingnews"
                })
            
            return normalized
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Bing News: {e}")
            return []
        except ET.ParseError as e:
            print(f"Error parsing Bing News RSS: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error with Bing News: {e}")
            return []
    
    def check_health(self) -> str:
        """Check if Bing News RSS is accessible."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}?q=test&format=rss",
                timeout=10
            )
            
            if response.status_code == 200:
                return "healthy"
            elif response.status_code == 429:
                return "rate_limited"
            else:
                return f"error_{response.status_code}"
                
        except requests.exceptions.RequestException:
            return "unreachable"
