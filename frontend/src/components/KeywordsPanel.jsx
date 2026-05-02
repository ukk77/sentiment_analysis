import React, { useState } from 'react';
import { Tag } from 'lucide-react';

const SENTIMENT_COLOR = (avg) => {
  if (avg > 0.1)  return { bg: 'bg-green-500/15 border-green-500/30', text: 'text-green-300', dot: 'bg-green-400' };
  if (avg < -0.1) return { bg: 'bg-red-500/15 border-red-500/30',   text: 'text-red-300',   dot: 'bg-red-400'   };
  return           { bg: 'bg-gray-700/50 border-gray-600/40',        text: 'text-gray-300',  dot: 'bg-gray-500'  };
};

const KeywordsPanel = ({ topics }) => {
  const [filter, setFilter] = useState('all');

  if (!topics || topics.length === 0) return null;

  const filtered = topics.filter((t) => {
    if (filter === 'positive') return t.avg_sentiment > 0.1;
    if (filter === 'negative') return t.avg_sentiment < -0.1;
    return true;
  });

  const maxCount = Math.max(...topics.map((t) => t.count), 1);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-purple-400" />
          <h3 className="text-lg font-semibold text-gray-300">Top Keywords & Topics</h3>
          <span className="text-xs text-gray-500 ml-1">({topics.length} extracted)</span>
        </div>
        <div className="flex items-center gap-1 text-xs">
          {['all', 'positive', 'negative'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded-full capitalize transition-colors border ${
                filter === f
                  ? 'bg-purple-500/20 border-purple-500/40 text-purple-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {filtered.map((topic) => {
          const colors = SENTIMENT_COLOR(topic.avg_sentiment);
          const widthPct = Math.max(20, Math.round((topic.count / maxCount) * 100));
          return (
            <div
              key={topic.keyword}
              title={`Appears in ${topic.count} articles · avg sentiment ${topic.avg_sentiment.toFixed(3)}`}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium cursor-default ${colors.bg} ${colors.text}`}
              style={{ fontSize: `${Math.max(11, Math.min(15, 11 + (widthPct / 20)))}px` }}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
              {topic.keyword}
              <span className="opacity-60 text-[10px]">×{topic.count}</span>
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block" /> positive topic</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> negative topic</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-500 inline-block" /> neutral topic</span>
      </div>
    </div>
  );
};

export default KeywordsPanel;
