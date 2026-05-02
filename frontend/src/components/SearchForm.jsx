import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const SearchForm = ({ onSubmit, isLoading }) => {
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (ticker.trim() && companyName.trim()) {
      onSubmit(ticker.trim().toUpperCase(), companyName.trim());
    }
  };

  // Auto-fill common companies
  const popularStocks = [
    { ticker: 'AAPL', name: 'Apple Inc.' },
    { ticker: 'MSFT', name: 'Microsoft Corporation' },
    { ticker: 'GOOGL', name: 'Alphabet Inc.' },
    { ticker: 'META', name: 'Meta Platforms Inc.' },
    { ticker: 'NVDA', name: 'NVIDIA Corporation' },
    { ticker: 'AMZN', name: 'Amazon.com Inc.' },
    { ticker: 'TSLA', name: 'Tesla Inc.' },
    { ticker: 'JPM', name: 'JPMorgan Chase & Co.' },
    { ticker: 'XOM', name: 'Exxon Mobil Corporation' },
    { ticker: 'LLY', name: 'Eli Lilly and Company' },
    { ticker: 'UNH', name: 'UnitedHealth Group Inc.' },
    { ticker: 'WMT', name: 'Walmart Inc.' },
    { ticker: 'CAT', name: 'Caterpillar Inc.' },
  ];

  const handleStockClick = (stock) => {
    setTicker(stock.ticker);
    setCompanyName(stock.name);
  };

  return (
    <div className="card animate-slide-up">
      <h2 className="text-xl font-semibold text-white mb-4">Analyze Stock Sentiment</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Stock Ticker
            </label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g., AAPL"
              className="input-field"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Company Name
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Apple Inc."
              className="input-field"
              disabled={isLoading}
            />
          </div>
        </div>
        
        <button
          type="submit"
          disabled={isLoading || !ticker.trim() || !companyName.trim()}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Analyze Sentiment</span>
            </>
          )}
        </button>
      </form>
      
      <div className="mt-4">
        <p className="text-xs text-gray-500 mb-2">Popular stocks:</p>
        <div className="flex flex-wrap gap-2">
          {popularStocks.map((stock) => (
            <button
              key={stock.ticker}
              onClick={() => handleStockClick(stock)}
              disabled={isLoading}
              className="px-3 py-1 text-xs rounded-full bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
            >
              {stock.ticker}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SearchForm;
