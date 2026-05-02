"""Diagnostic test for Yahoo Finance, Finviz, and SEC EDGAR sources."""
import requests
import json

def test_sources():
    """Test individual news sources."""
    
    print("=" * 70)
    print("TESTING NEWS SOURCE INTEGRATIONS")
    print("=" * 70)
    
    # Test 1: Health check
    print("\n1. API Health Check")
    print("-" * 50)
    try:
        resp = requests.get("http://localhost:8000/api/health", timeout=10)
        data = resp.json()
        print(f"Status: {data.get('status', 'unknown')}")
        print(f"NewsAPI: {data.get('news_api', 'unknown')}")
        print(f"Finnhub: {data.get('finnhub', 'unknown')}")
        print(f"Yahoo Finance: {data.get('yahoofinance', 'unknown')}")
        print(f"Finviz: {data.get('finviz', 'unknown')}")
        print(f"SEC EDGAR: {data.get('secedgar', 'unknown')}")
        print(f"Model Loaded: {data.get('model_loaded', False)}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Full analysis with source breakdown
    print("\n2. Testing Full Analysis (AAPL)")
    print("-" * 50)
    try:
        resp = requests.post(
            "http://localhost:8000/api/analyze",
            json={"ticker": "AAPL", "company_name": "Apple Inc."},
            timeout=120
        )
        data = resp.json()
        
        print(f"Ticker: {data.get('ticker')}")
        print(f"Articles Analyzed: {data.get('metrics', {}).get('total_articles', 0)}")
        
        # Source breakdown
        sources = data.get('metrics', {}).get('sources_breakdown', {})
        print("\nSource Breakdown:")
        for source, count in sources.items():
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {source}: {count} articles")
        
        # Price data check
        price_data = data.get('price_data')
        if price_data:
            print(f"\n✓ Price Data Available:")
            print(f"  Current Price: ${price_data.get('current_price', 0)}")
            print(f"  History Points: {len(price_data.get('history', []))}")
        else:
            print("\n✗ Price Data: Not available")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Test with TSLA (more volatile, might have more news)
    print("\n3. Testing with TSLA (volatile stock)")
    print("-" * 50)
    try:
        resp = requests.post(
            "http://localhost:8000/api/analyze",
            json={"ticker": "TSLA", "company_name": "Tesla Inc."},
            timeout=120
        )
        data = resp.json()
        
        sources = data.get('metrics', {}).get('sources_breakdown', {})
        print("Source Breakdown:")
        for source, count in sources.items():
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {source}: {count} articles")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    
    # Analysis
    print("\nAnalysis:")
    print("- Yahoo Finance: Requires Yahoo to have recent news for the ticker")
    print("- Finviz: Scrapes Finviz news table - may be blocked or rate-limited")
    print("- SEC EDGAR: Only returns 8-K filings from last 14 days")
    print("- If sources show 0 articles, it may be due to:")
    print("  * No recent news/filings for that specific ticker")
    print("  * Rate limiting from the source")
    print("  * Blocking of scrapers (Finviz)")
    print("  * Yahoo Finance may have different news availability")

if __name__ == "__main__":
    test_sources()
