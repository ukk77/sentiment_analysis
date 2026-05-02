"""Debug individual source responses."""
import sys
sys.path.insert(0, 'backend')

from app.services.yahoofinance import YahooFinanceClient
from app.services.finviz import FinvizClient
from app.services.secedgar import SECEDGARClient

print("=" * 70)
print("DEBUGGING NEWS SOURCES")
print("=" * 70)

# Test Yahoo Finance News
print("\n1. Yahoo Finance News (AAPL)")
print("-" * 50)
yf_client = YahooFinanceClient()
try:
    news = yf_client.get_news("AAPL", max_articles=5)
    print(f"Articles returned: {len(news)}")
    if news:
        for i, article in enumerate(news[:3], 1):
            print(f"\n  {i}. {article['title'][:60]}...")
            print(f"     Source: {article['source']}")
    else:
        print("  (Empty - Yahoo Finance may not have recent news)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test Finviz
print("\n2. Finviz News (AAPL)")
print("-" * 50)
finviz_client = FinvizClient()
try:
    news = finviz_client.get_news("AAPL")
    print(f"Articles returned: {len(news)}")
    if news:
        for i, article in enumerate(news[:3], 1):
            print(f"\n  {i}. {article['title'][:60]}...")
    else:
        print("  (Empty - Finviz may be blocking scrapers)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test SEC EDGAR
print("\n3. SEC EDGAR 8-K Filings (AAPL)")
print("-" * 50)
sec_client = SECEDGARClient()
try:
    filings = sec_client.get_latest_8k("AAPL")
    print(f"Filings returned: {len(filings)}")
    if filings:
        for i, filing in enumerate(filings[:3], 1):
            print(f"\n  {i}. {filing['title'][:60]}...")
            print(f"     Date: {filing.get('published_at', 'N/A')}")
    else:
        print("  (Empty - No 8-K filings in last 14 days)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test Yahoo Price (to confirm it works)
print("\n4. Yahoo Finance Price Data (AAPL)")
print("-" * 50)
try:
    price_data = yf_client.get_price_history("AAPL", period="5d")
    if price_data:
        print(f"✓ Price data working: {len(price_data)} days")
        print(f"  Latest close: ${price_data[-1]['close']}")
    else:
        print("✗ Price data empty")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("CONCLUSIONS:")
print("=" * 70)
print("""
- Yahoo Finance News: Returns empty list (yfinance library limitation)
  * Alternative: Use RSS feeds or Yahoo Finance API v7
  * Price data works fine via yfinance

- Finviz: Likely blocked by Cloudflare/anti-bot measures
  * Would need headless browser (Selenium/Playwright)
  * Or use Finviz API (paid)

- SEC EDGAR: Working, but AAPL has no recent 8-K filings
  * Try a more volatile stock or extend date range

RECOMMENDATIONS:
1. Yahoo Finance News: Implement RSS feed scraper as alternative
2. Finviz: Consider removing or implementing Selenium fallback
3. SEC EDGAR: Extend to 30 days, add 10-Q and 10-K support
""")
