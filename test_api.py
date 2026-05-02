import requests
import json
import sys

url = 'http://localhost:8000/api/analyze'
payload = {'ticker': 'AAPL', 'company_name': 'Apple Inc.'}

print('=' * 60)
print('Testing Stock Sentiment Analysis API')
print('=' * 60)
print(f'\nRequest URL: {url}')
print(f'Payload: {json.dumps(payload, indent=2)}')
print()

try:
    print('Sending request (this may take 30-60s for model loading)...')
    response = requests.post(url, json=payload, timeout=120)
    
    print(f'\nStatus Code: {response.status_code}')
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        print('RESPONSE SUMMARY:')
        print('-' * 60)
        print(f"Ticker: {data['ticker']}")
        print(f"Company: {data['company_name']}")
        print(f"Overall Sentiment: {data['overall_sentiment'].upper()}")
        print(f"Confidence: {data['confidence']:.2%}")
        print()
        print('METRICS:')
        print(f"  Total Articles: {data['metrics']['total_articles']}")
        print(f"  Positive: {data['metrics']['positive_count']}")
        print(f"  Negative: {data['metrics']['negative_count']}")
        print(f"  Neutral: {data['metrics']['neutral_count']}")
        print(f"  Avg Sentiment Score: {data['metrics']['avg_sentiment']:.3f}")
        print()
        print('SOURCES:')
        print(f"  NewsAPI: {data['metrics']['sources_breakdown']['newsapi']}")
        print(f"  Finnhub: {data['metrics']['sources_breakdown']['finnhub']}")
        print()
        print('ARTICLES:')
        print('-' * 60)
        for i, article in enumerate(data['articles'][:5], 1):  # Show first 5
            print(f"\n{i}. [{article['sentiment'].upper()}] {article['title'][:60]}...")
            print(f"   Source: {article['source']}")
            print(f"   Score: {article['score']:.3f}")
        
        if len(data['articles']) > 5:
            print(f"\n... and {len(data['articles']) - 5} more articles")
        
        # Save full response to file
        with open('api_test_result.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n\nFull response saved to: api_test_result.json")
        
    else:
        print(f'ERROR: {response.status_code}')
        print(response.text)
        
except requests.exceptions.ConnectionError as e:
    print(f'\nERROR: Cannot connect to backend server at {url}')
    print('Make sure the backend is running on port 8000')
except requests.exceptions.Timeout:
    print(f'\nERROR: Request timed out. Model may still be loading.')
except Exception as e:
    print(f'\nERROR: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('Test Complete')
print('=' * 60)
