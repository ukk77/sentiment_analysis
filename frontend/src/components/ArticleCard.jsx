import React from 'react';
import { format } from 'date-fns';
import { ExternalLink, TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react';

const ArticleCard = ({ article }) => {
  const { title, source, published_at, sentiment, score, url, summary, impact_score = 0 } = article;

  const impactPct = Math.round(impact_score * 100);

  const getImpactTier = () => {
    if (impactPct >= 30) return { label: 'High Impact', color: 'text-orange-400', bar: 'bg-orange-400', badge: 'bg-orange-400/20 text-orange-400 border-orange-400/30' };
    if (impactPct >= 15) return { label: 'Med Impact', color: 'text-yellow-400', bar: 'bg-yellow-400', badge: 'bg-yellow-400/20 text-yellow-400 border-yellow-400/30' };
    return { label: 'Low Impact', color: 'text-gray-500', bar: 'bg-gray-600', badge: 'bg-gray-700/50 text-gray-500 border-gray-600/30' };
  };

  const impact = getImpactTier();

  const getSentimentIcon = () => {
    switch (sentiment) {
      case 'positive': return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'negative': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default:         return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSentimentClass = () => {
    switch (sentiment) {
      case 'positive': return 'border-l-4 border-green-500 bg-green-500/5';
      case 'negative': return 'border-l-4 border-red-500 bg-red-500/5';
      default:         return 'border-l-4 border-gray-500 bg-gray-500/5';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  return (
    <div className={`card ${getSentimentClass()} animate-fade-in`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white mb-1 line-clamp-2">
            {title}
          </h3>

          <div className="flex items-center gap-3 text-sm text-gray-400 mb-2">
            <span className="font-medium">{source}</span>
            <span>•</span>
            <span>{formatDate(published_at)}</span>
          </div>

          {summary && (
            <p className="text-gray-300 text-sm line-clamp-2 mb-3">
              {summary}
            </p>
          )}

          {/* Impact bar */}
          <div className="mt-2">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1">
                <Zap className={`w-3 h-3 ${impact.color}`} />
                <span className={`text-xs font-medium ${impact.color}`}>{impact.label}</span>
              </div>
              <span className={`text-xs font-semibold ${impact.color}`}>{impactPct}%</span>
            </div>
            <div className="h-1 w-full rounded-full bg-gray-700/60">
              <div
                className={`h-1 rounded-full transition-all duration-500 ${impact.bar}`}
                style={{ width: `${Math.min(impactPct, 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className="flex items-center gap-2">
            {getSentimentIcon()}
            <span
              className={`text-sm font-semibold capitalize ${
                sentiment === 'positive' ? 'text-green-500' :
                sentiment === 'negative' ? 'text-red-500' : 'text-gray-500'
              }`}
            >
              {sentiment}
            </span>
          </div>
          <span className="text-xs text-gray-500">
            Score: {(score * 100).toFixed(1)}
          </span>
        </div>
      </div>

      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 transition-colors mt-2"
        >
          <span>Read article</span>
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </div>
  );
};

export default ArticleCard;
