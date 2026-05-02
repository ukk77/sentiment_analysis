"""
Google News RSS client - no API key required.
Uses RSS feeds to fetch news headlines.
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime
from html import unescape
import re


class GoogleNewsClient:
    """Google News RSS client for fetching stock-related news."""
    
    BASE_URL = "https://news.google.com/rss"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"
        })
    
    def search_news(
        self, 
        ticker: str, 
        company_name: str,
        max_articles: int = 20
    ) -> List[Dict]:
        """
        Fetch news from Google News RSS.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            max_articles: Maximum articles to return
        
        Returns:
            List of article dictionaries
        """
        # Build search query
        query = f"{ticker} OR {company_name} stock"
        
        # Google News RSS endpoint
        url = f"{self.BASE_URL}/search"
        params = {
            "q": query,
            "hl": "en",  # English
            "gl": "US",  # US edition
            "ceid": "US:en"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            # Find all items (articles)
            # RSS namespace handling
            items = root.findall(".//item")
            
            normalized = []
            for item in items[:max_articles]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                description_elem = item.find("description")
                source_elem = item.find("source")
                
                title = unescape(title_elem.text) if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                description = unescape(description_elem.text) if description_elem is not None else ""
                source = source_elem.text if source_elem is not None else "Google News"
                
                # Clean Google News redirect URLs if present
                if link and "news.google.com/articles" in link:
                    # Extract actual URL from Google redirect if possible
                    pass  # Keep as-is, browser will handle redirect
                
                # Parse pub date to ISO format
                if pub_date:
                    try:
                        # Parse RFC 2822 format
                        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                        pub_date = dt.isoformat() + "Z"
                    except:
                        pass
                
                normalized.append({
                    "title": title,
                    "description": description,
                    "content": description,
                    "url": link,
                    "source": source,
                    "published_at": pub_date,
                    "author": "",  # RSS doesn't always provide author
                    "_source": "googlenews"
                })
            
            return normalized
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Google News: {e}")
            return []
        except ET.ParseError as e:
            print(f"Error parsing Google News RSS: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error with Google News: {e}")
            return []
    
    def get_topic_news(
        self, 
        topic: str,
        max_articles: int = 10
    ) -> List[Dict]:
        """
        Get news for a specific topic (e.g., 'business', 'technology').
        
        Args:
            topic: Topic section
            max_articles: Maximum articles
        
        Returns:
            List of articles
        """
        # Map common topics to Google News topics
        topic_mapping = {
            "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
            "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
            "finance": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB"
        }
        
        topic_id = topic_mapping.get(topic.lower())
        if not topic_id:
            return []
        
        url = f"{self.BASE_URL}/topics/{topic_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            normalized = []
            for item in items[:max_articles]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                source_elem = item.find("source")
                
                title = unescape(title_elem.text) if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                source = source_elem.text if source_elem is not None else "Google News"
                
                if pub_date:
                    try:
                        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                        pub_date = dt.isoformat() + "Z"
                    except:
                        pass
                
                normalized.append({
                    "title": title,
                    "description": "",
                    "content": "",
                    "url": link,
                    "source": source,
                    "published_at": pub_date,
                    "author": "",
                    "_source": "googlenews"
                })
            
            return normalized
            
        except Exception as e:
            print(f"Error fetching Google News topic: {e}")
            return []
    
    def check_health(self) -> str:
        """Check if Google News RSS is accessible."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/search?q=test&hl=en",
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
