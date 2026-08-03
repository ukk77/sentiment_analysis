import requests
import json
import time

url = 'http://localhost:8000/api/analyze'
payload = {'ticker': 'MSFT', 'company_name': 'Microsoft Corporation'}

print('=' * 70)
print('Testing MSFT Sentiment Analysis')
print('=' * 70)
print('This may take 2-3 minutes on first run (model loading + API calls)')
print('-' * 70)

start_time = time.time()

try:
    print('Sending request...')
    response = requests.post(url, json=payload, timeout=300)  # 5 min timeout
    elapsed = time.time() - start_time
    print(f'Completed in {elapsed:.1f}s')
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTicker: {data['ticker']}")
        print(f"Company: {data['company_name']}")
        print(f"Overall Sentiment: {data['overall_sentiment'].upper()}")
        print(f"Confidence: {data['confidence']:.1%}")
        print(f"\nArticles Analyzed: {data['metrics']['total_articles']}")
        print(f"  Positive: {data['metrics']['positive_count']}")
        print(f"  Negative: {data['metrics']['negative_count']}")
        print(f"  Neutral: {data['metrics']['neutral_count']}")
        print(f"\nSources: NewsAPI={data['metrics']['sources_breakdown']['newsapi']}, Finnhub={data['metrics']['sources_breakdown']['finnhub']}")
        print("\n--- Top 5 Articles ---")
        for i, article in enumerate(data['articles'][:5], 1):
            print(f"{i}. [{article['sentiment'].upper()}] {article['title'][:60]}...")
            print(f"   Score: {article['score']:.3f} | Source: {article['source']}")
        
        # Save full response
        with open('msft_result.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\nFull response saved to: msft_result.json")
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
print('=' * 70)
