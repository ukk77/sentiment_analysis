import React, { useState } from 'react';
import { BarChart3, AlertCircle } from 'lucide-react';

import SearchForm from './components/SearchForm';
import SentimentGauge from './components/SentimentGauge';
import SentimentBar from './components/SentimentBar';
import ArticleCard from './components/ArticleCard';
import MetricsCard from './components/MetricsCard';
import HealthStatus from './components/HealthStatus';
import PriceSentimentChart from './components/PriceSentimentChart';
import KeywordsPanel from './components/KeywordsPanel';
import AnalystRatings from './components/AnalystRatings';
import SentimentHistory from './components/SentimentHistory';
import { analyzeStock } from './services/api';
import { FileText, Database, Activity, TrendingUp } from 'lucide-react';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [articleSort, setArticleSort] = useState('recent');
  const [selectedDate, setSelectedDate] = useState(null);

  const handleAnalyze = async (ticker, companyName) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedDate(null);

    try {
      const data = await analyzeStock(ticker, companyName);
      setResult(data);
    } catch (err) {
      setError(err.toString());
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-400';
      case 'negative':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-gray-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-xl">
                <BarChart3 className="w-7 h-7 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Stock Sentiment Analyzer
                </h1>
                <p className="text-xs text-gray-400">Powered by FinBERT, NewsAPI & Finnhub</p>
              </div>
            </div>
            <HealthStatus />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Search Form */}
        <SearchForm onSubmit={handleAnalyze} isLoading={loading} />

        {/* Error Message */}
        {error && (
          <div className="mt-6 card border-red-500/50 bg-red-500/10 flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-400 shrink-0" />
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 space-y-6 animate-fade-in">
            {/* Header with Ticker */}
            <div className="text-center">
              <h2 className="text-3xl font-bold text-white">
                {result.ticker}
                <span className="text-gray-400 text-xl ml-2">({result.company_name})</span>
              </h2>
              <p className={`text-lg font-semibold mt-2 capitalize ${getSentimentColor(result.overall_sentiment)}`}>
                {result.overall_sentiment} Sentiment
              </p>
            </div>

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Sentiment Gauge */}
              <div className="card flex flex-col items-center justify-center">
                <h3 className="text-lg font-semibold text-gray-300 mb-4">Overall Sentiment</h3>
                <SentimentGauge 
                  sentiment={result.overall_sentiment} 
                  confidence={result.confidence} 
                />
              </div>

              {/* Metrics */}
              <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricsCard
                  title="Total Articles"
                  value={result.metrics.total_articles}
                  subtitle="Analyzed"
                  icon={FileText}
                  color="blue"
                />
                <MetricsCard
                  title="Positive"
                  value={result.metrics.positive_count}
                  subtitle="Articles"
                  icon={TrendingUp}
                  color="green"
                />
                <MetricsCard
                  title="Negative"
                  value={result.metrics.negative_count}
                  subtitle="Articles"
                  icon={TrendingUp}
                  color="red"
                />
                <MetricsCard
                  title="Avg Score"
                  value={(result.metrics.avg_sentiment * 100).toFixed(1)}
                  subtitle="Sentiment Score"
                  icon={Activity}
                  color="purple"
                />
              </div>
            </div>

            {/* Price & Sentiment Correlation Chart */}
            {result.price_data && (
              <PriceSentimentChart
                priceData={result.price_data}
                avgSentiment={result.metrics.avg_sentiment}
                selectedDate={selectedDate}
                onDateClick={(dateKey) => setSelectedDate(prev => prev === dateKey ? null : dateKey)}
                correlation={result.correlation ?? null}
                articles={result.articles}
                dailySentiment={(() => {
                  const map = {};
                  result.articles.forEach(a => {
                    if (!a.published_at || a.score == null) return;
                    try {
                      const day = new Date(a.published_at).toISOString().split('T')[0];
                      if (!map[day]) map[day] = { sum: 0, count: 0 };
                      map[day].sum += a.score;
                      map[day].count += 1;
                    } catch (_) {}
                  });
                  return Object.fromEntries(
                    Object.entries(map).map(([day, { sum, count }]) => [day, sum / count])
                  );
                })()}
              />
            )}

            {/* Analyst Ratings */}
            {result.analyst_ratings && (
              <AnalystRatings ratings={result.analyst_ratings} />
            )}

            {/* Keywords / Topic Extraction */}
            {result.topics && result.topics.length > 0 && (
              <KeywordsPanel topics={result.topics} />
            )}

            {/* Historical Tracking */}
            <SentimentHistory ticker={result.ticker} />

            {/* Sentiment Distribution */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-300 mb-4">Sentiment Distribution</h3>
              <SentimentBar
                positive={result.metrics.positive_count}
                negative={result.metrics.negative_count}
                neutral={result.metrics.neutral_count}
                total={result.metrics.total_articles}
              />
              <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
                <span>Sources:</span>
                <div className="flex gap-4 flex-wrap">
                  <span>NewsAPI: {result.metrics.sources_breakdown.newsapi}</span>
                  <span>Finnhub: {result.metrics.sources_breakdown.finnhub}</span>
                  <span>Google: {result.metrics.sources_breakdown.googlenews}</span>
                  <span>Yahoo: {result.metrics.sources_breakdown.yahoofinance}</span>
                  <span>Finviz: {result.metrics.sources_breakdown.finviz}</span>
                  <span>SEC: {result.metrics.sources_breakdown.secedgar}</span>
                </div>
              </div>
            </div>

            {/* Articles List */}
            <div>
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <h3 className="text-xl font-semibold text-white">
                    Articles ({selectedDate
                      ? result.articles.filter(a => {
                          try { return new Date(a.published_at).toISOString().split('T')[0] === selectedDate; } catch { return false; }
                        }).length
                      : result.articles.length})
                  </h3>
                  {result.metrics.filter_stats && result.metrics.filter_stats.input > 0 && (() => {
                    const fs = result.metrics.filter_stats;
                    const totalDropped = fs.dedup_dropped + fs.domain_dropped + fs.title_dropped + fs.finbert_relevance_dropped;
                    const pct = Math.round((totalDropped / fs.input) * 100);
                    if (totalDropped === 0) return null;
                    const tooltip = [
                      `${fs.input} articles fetched from all sources`,
                      `  − ${fs.dedup_dropped} duplicates (cross-source)`,
                      `  − ${fs.domain_dropped} untrusted domains/publishers`,
                      `  − ${fs.title_dropped} missing ticker/company in title`,
                      `  − ${fs.finbert_relevance_dropped} low FinBERT confidence`,
                      `  = ${fs.output} relevant articles`,
                    ].join('\n');
                    return (
                      <span
                        title={tooltip}
                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 cursor-help"
                      >
                        🔍 {totalDropped} filtered ({pct}%)
                      </span>
                    );
                  })()}
                  {selectedDate && (
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/20 border border-blue-500/40 text-blue-300">
                        📅 {new Date(selectedDate + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                      <button
                        onClick={() => setSelectedDate(null)}
                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-700 border border-gray-600 text-gray-300 hover:bg-gray-600 transition-colors"
                      >
                        ✕ Reset
                      </button>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-400">Sort by:</span>
                  {['recent', 'impact', 'score'].map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setArticleSort(opt)}
                      className={`px-3 py-1 rounded-full capitalize transition-colors border ${
                        articleSort === opt
                          ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300'
                      }`}
                    >
                      {opt === 'impact' ? '⚡ Impact' : opt === 'score' ? '📊 Score' : '🕐 Recent'}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[...result.articles]
                  .filter(a => {
                    if (!selectedDate) return true;
                    try { return new Date(a.published_at).toISOString().split('T')[0] === selectedDate; } catch { return false; }
                  })
                  .sort((a, b) => {
                    if (articleSort === 'impact') return (b.impact_score || 0) - (a.impact_score || 0);
                    if (articleSort === 'score') return Math.abs(b.score || 0) - Math.abs(a.score || 0);
                    return (b.published_at || '').localeCompare(a.published_at || '');
                  })
                  .map((article, index) => (
                    <ArticleCard key={index} article={article} />
                  ))}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!result && !loading && !error && (
          <div className="mt-16 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-800 mb-4">
              <BarChart3 className="w-10 h-10 text-gray-600" />
            </div>
            <p className="text-gray-400 text-lg">
              Enter a stock ticker and company name to analyze sentiment
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Try popular stocks like AAPL, MSFT, GOOGL, or TSLA
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-16">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-500">
            Data sourced from NewsAPI and Finnhub • Powered by FinBERT sentiment analysis model
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
