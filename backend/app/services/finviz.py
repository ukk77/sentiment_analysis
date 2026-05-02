"""
Finviz client for insider trading and analyst ratings.
Uses Playwright headless browser to bypass Cloudflare protection.
No API key required.
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import subprocess
import json
import tempfile
import os
import sys


class FinvizClient:
    """Finviz client using Playwright headless browser."""
    
    BASE_URL = "https://finviz.com"
    
    def __init__(self):
        self.last_request_time = 0
        self.min_delay = 2.0  # 2 seconds between requests
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def _fetch_page(self, url: str, params: dict = None) -> str:
        """Fetch page using Playwright in subprocess to avoid event loop conflicts."""
        # Build URL with params
        full_url = url
        if params:
            query = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query}"
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        # Playwright script to run in subprocess
        # Use string concatenation to avoid f-string escaping issues
        script = (
            'import sys\n'
            'import json\n'
            'from playwright.sync_api import sync_playwright\n'
            '\n'
            'try:\n'
            '    with sync_playwright() as p:\n'
            '        browser = p.chromium.launch(\n'
            '            headless=True,\n'
            '            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]\n'
            '        )\n'
            '        \n'
            '        context = browser.new_context(\n'
            '            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",\n'
            '            viewport={"width": 1920, "height": 1080}\n'
            '        )\n'
            '        \n'
            '        page = context.new_page()\n'
            f'        page.goto("{full_url}", wait_until="domcontentloaded", timeout=60000)\n'
            '        page.wait_for_timeout(4000)\n'
            '        content = page.content()\n'
            '        \n'
            '        context.close()\n'
            '        browser.close()\n'
            '        \n'
            f'        with open(r"{output_file}", "w", encoding="utf-8") as f:\n'
            '            json.dump({"success": True, "content": content}, f)\n'
            'except Exception as e:\n'
            f'    with open(r"{output_file}", "w", encoding="utf-8") as f:\n'
            '        json.dump({"success": False, "error": str(e)}, f)\n'
        )
        
        # Get venv Python path
        venv_python = os.path.join(os.path.dirname(sys.executable), 'python.exe')
        if not os.path.exists(venv_python):
            venv_python = sys.executable  # Fallback to current Python
        
        # Run script in subprocess with isolated event loop
        result = subprocess.run(
            [venv_python, '-c', script],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            os.unlink(output_file)
            
            if data.get('success'):
                return data['content']
            else:
                raise Exception(data.get('error', 'Unknown error'))
        except Exception as e:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise e
    
    def get_insider_trading(self, ticker: str) -> List[Dict]:
        """Get recent insider trading transactions using Playwright."""
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/insidertrading.ashx"
            params = {"ticker": ticker}
            
            content = self._fetch_page(url, params)
            soup = BeautifulSoup(content, "html.parser")
            
            # Find the insider trading table
            table = soup.find("table", {"class": "body-table"})
            if not table:
                return []
            
            transactions = []
            rows = table.find_all("tr")[1:]  # Skip header
            
            for row in rows[:10]:  # Get top 10 transactions
                cols = row.find_all("td")
                if len(cols) >= 8:
                    transactions.append({
                        "insider_name": cols[0].text.strip(),
                        "title": cols[1].text.strip(),
                        "date": cols[2].text.strip(),
                        "transaction_type": cols[3].text.strip(),
                        "price": cols[4].text.strip(),
                        "shares": cols[5].text.strip(),
                        "value": cols[6].text.strip(),
                        "shares_owned": cols[7].text.strip()
                    })
            
            return transactions
            
        except Exception as e:
            print(f"Error fetching Finviz insider data: {e}")
            return []
    
    def get_news(self, ticker: str) -> List[Dict]:
        """Get news from Finviz using Playwright."""
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/news.ashx"
            params = {"ticker": ticker}
            
            content = self._fetch_page(url, params)
            soup = BeautifulSoup(content, "html.parser")
            
            # Find news items - try multiple selectors for new Finviz layout
            articles = []
            
            # Try new layout first (news_table-row class)
            news_rows = soup.find_all("tr", {"class": lambda x: x and "news_table-row" in x})
            
            # Fallback to old layout
            if not news_rows:
                news_table = soup.find("table", {"class": "fullview-news-outer"})
                if news_table:
                    news_rows = news_table.find_all("tr")
            
            for row in news_rows[:20]:  # Get top 20 news items
                cols = row.find_all("td")
                # New layout has 3 columns: icon, time, title
                if len(cols) >= 3:
                    # Extract time from second column
                    time_text = cols[1].text.strip() if len(cols) > 1 else ""
                    
                    # Extract title and link from third column
                    title_col = cols[2] if len(cols) > 2 else None
                    if title_col:
                        link_elem = title_col.find("a")
                        if link_elem:
                            title = link_elem.text.strip()
                            link = link_elem.get("href", "")
                            
                            # Extract source from onclick or nearby
                            source = "Finviz"
                            # Try to get source from onclick URL or small text
                            onclick = row.get("onclick", "")
                            if onclick:
                                # Extract URL from onclick="trackAndOpenNews(event, id, 'url')"
                                import re
                                url_match = re.search(r"'([^']+)'", onclick)
                                if url_match:
                                    actual_url = url_match.group(1)
                                    if actual_url.startswith("http"):
                                        link = actual_url
                            
                            # Try to extract source from small text in title col
                            source_elem = title_col.find("span", {"class": lambda x: x and "text-xs" in str(x)}) or \
                                         title_col.find("small") or \
                                         title_col.find("div", {"class": lambda x: x and "source" in str(x).lower()})
                            if source_elem:
                                source = source_elem.text.strip()
                            
                            # Build publication date (use today + time)
                            pub_date = ""
                            try:
                                from datetime import datetime
                                today = datetime.now().strftime("%Y-%m-%d")
                                if time_text:
                                    pub_date = f"{today} {time_text}"
                                else:
                                    pub_date = today
                            except:
                                pub_date = time_text
                            
                            if title:  # Add if we have title
                                articles.append({
                                    "title": title,
                                    "description": title,
                                    "content": title,
                                    "url": link if link.startswith("http") else f"{self.BASE_URL}/{link}",
                                    "source": source,
                                    "published_at": pub_date,
                                    "author": "",
                                    "_source": "finviz"
                                })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching Finviz news: {e}")
            return []
    
    def get_stock_screen_data(self, ticker: str) -> Optional[Dict]:
        """Get stock screening data using Playwright."""
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/quote.ashx"
            params = {"t": ticker}
            
            content = self._fetch_page(url, params)
            soup = BeautifulSoup(content, "html.parser")
            
            data = {}
            table = soup.find("table", {"class": "snapshot-table2"})
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    for i in range(0, len(cols) - 1, 2):
                        if i + 1 < len(cols):
                            key = cols[i].text.strip()
                            value = cols[i + 1].text.strip()
                            data[key] = value
            
            return data
            
        except Exception as e:
            print(f"Error fetching Finviz stock data: {e}")
            return None
    
    def check_health(self) -> str:
        """Check if Finviz is accessible via Playwright."""
        try:
            content = self._fetch_page(self.BASE_URL)
            if content and "finviz" in content.lower():
                return "healthy"
            return "degraded"
        except Exception as e:
            print(f"Finviz health check failed: {e}")
            return "unreachable"
