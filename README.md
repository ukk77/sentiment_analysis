# Stock Sentiment Analysis Bot

A web application for analyzing stock sentiment using real-time news data and FinBERT machine learning model.

## Features

- **Real-time News Analysis**: Fetches live news from NewsAPI and Finnhub
- **AI-Powered Sentiment**: Uses FinBERT (Hugging Face) model trained specifically for financial text
- **Detailed Metrics**: Overall sentiment, confidence scores, article breakdown by source
- **Interactive Dashboard**: Modern React frontend with Tailwind CSS
- **No Mock Data**: All data comes from real APIs

## Architecture

```
sentiment_analysis/
├── backend/           # FastAPI Python server
│   ├── app/
│   │   ├── services/  # NewsAPI, Finnhub, FinBERT clients
│   │   ├── models/    # Pydantic models
│   │   ├── utils/     # Text processing
│   │   └── main.py    # FastAPI app with endpoints
│   └── requirements.txt
└── frontend/          # React + Vite + Tailwind
    ├── src/
    │   ├── components/ # UI components
    │   └── services/   # API client
    └── package.json
```

## API Sources

| Source | Type | API Key Required | Description |
|--------|------|------------------|-------------|
| NewsAPI | News | Yes (provided) | 80,000+ news sources globally |
| Finnhub | Financial | Yes (provided) | Stock news and company data |

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

The backend will start on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`

## API Endpoints

- `POST /api/analyze` - Analyze stock sentiment
  - Input: `{ "ticker": "AAPL", "company_name": "Apple Inc." }`
  - Output: Sentiment analysis with article breakdown

- `GET /api/health` - Health check
- `GET /api/sources` - Data source information

## Usage

1. Open the web interface at `http://localhost:5173`
2. Enter a stock ticker (e.g., `AAPL`) and company name (e.g., `Apple Inc.`)
3. Click "Analyze Sentiment"
4. View the dashboard with overall sentiment, article-by-article breakdown, and metrics

## Output Format

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "overall_sentiment": "positive",
  "confidence": 0.72,
  "metrics": {
    "total_articles": 25,
    "positive_count": 18,
    "negative_count": 4,
    "neutral_count": 3,
    "avg_sentiment": 0.65,
    "sources_breakdown": {
      "newsapi": 15,
      "finnhub": 10
    }
  },
  "articles": [
    {
      "title": "Apple Reports Strong Q4 Earnings",
      "source": "Bloomberg",
      "published_at": "2024-01-15T10:00:00Z",
      "sentiment": "positive",
      "score": 0.89,
      "url": "...",
      "summary": "Apple exceeded expectations..."
    }
  ]
}
```

## Configuration

API keys are configured in `backend/.env`:
```
NEWS_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
```

## Additional Free Sources (Recommended)

| Source | API Key | Best For |
|--------|---------|----------|
| Yahoo Finance (yfinance) | No | Price correlation, volume data |
| Reddit API (PRAW) | Free registration | r/wallstreetbets retail sentiment |
| SEC EDGAR | No | 10-K/10-Q filings sentiment |

## License

MIT
