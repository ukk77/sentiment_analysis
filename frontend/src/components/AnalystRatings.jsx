import React from 'react';
import { Users, Target, TrendingUp } from 'lucide-react';

const REC_STYLES = {
  'strong_buy': { label: 'Strong Buy',  bg: 'bg-emerald-500/20 border-emerald-500/40', text: 'text-emerald-300' },
  'buy':        { label: 'Buy',          bg: 'bg-green-500/20 border-green-500/40',     text: 'text-green-300'   },
  'outperform': { label: 'Outperform',   bg: 'bg-green-500/20 border-green-500/40',     text: 'text-green-300'   },
  'hold':       { label: 'Hold',         bg: 'bg-yellow-500/20 border-yellow-500/40',   text: 'text-yellow-300'  },
  'neutral':    { label: 'Neutral',      bg: 'bg-gray-700/50 border-gray-600/40',       text: 'text-gray-300'    },
  'underperform':{ label: 'Underperform',bg: 'bg-orange-500/20 border-orange-500/40',  text: 'text-orange-300'  },
  'sell':       { label: 'Sell',         bg: 'bg-red-500/20 border-red-500/40',         text: 'text-red-300'     },
  'strong_sell':{ label: 'Strong Sell',  bg: 'bg-red-600/20 border-red-600/40',         text: 'text-red-400'     },
};

const recStyle = (key) =>
  REC_STYLES[key?.toLowerCase()] || { label: key || 'N/A', bg: 'bg-gray-700/50 border-gray-600/40', text: 'text-gray-300' };

const AnalystRatings = ({ ratings }) => {
  if (!ratings) return null;

  const { recommendation, target_mean_price, target_high_price, target_low_price,
          num_analysts, strong_buy, buy, hold, sell, strong_sell } = ratings;

  const totalVotes = strong_buy + buy + hold + sell + strong_sell;
  const bullish = strong_buy + buy;
  const bearish = sell + strong_sell;
  const style = recStyle(recommendation);

  const Bar = ({ label, count, color }) => {
    if (!count) return null;
    const pct = totalVotes > 0 ? Math.round((count / totalVotes) * 100) : 0;
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="w-16 text-gray-400 shrink-0">{label}</span>
        <div className="flex-1 bg-gray-700/50 rounded-full h-2 overflow-hidden">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="w-6 text-right text-gray-400">{count}</span>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-4 h-4 text-blue-400" />
        <h3 className="text-lg font-semibold text-gray-300">Analyst Ratings</h3>
        {num_analysts > 0 && (
          <span className="text-xs text-gray-500 ml-1">({num_analysts} analysts)</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left — consensus + target */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1.5 rounded-full border text-sm font-semibold ${style.bg} ${style.text}`}>
              {style.label}
            </span>
            {totalVotes > 0 && (
              <span className="text-xs text-gray-400">
                {Math.round((bullish / totalVotes) * 100)}% bullish
              </span>
            )}
          </div>

          {target_mean_price && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-xs text-gray-400">Price Target</span>
              </div>
              <div className="flex items-center gap-3">
                {target_low_price  && <span className="text-xs text-red-400">${target_low_price.toFixed(2)} low</span>}
                <span className="text-base font-bold text-white">${target_mean_price.toFixed(2)}</span>
                {target_high_price && <span className="text-xs text-green-400">${target_high_price.toFixed(2)} high</span>}
              </div>
              {target_low_price && target_high_price && (
                <div className="mt-1.5 h-1.5 bg-gray-700 rounded-full overflow-hidden relative">
                  <div
                    className="h-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500 rounded-full"
                    style={{ width: '100%' }}
                  />
                  <div
                    className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-white rounded-full border-2 border-blue-400 shadow"
                    style={{
                      left: `${Math.round(
                        ((target_mean_price - target_low_price) /
                          (target_high_price - target_low_price)) *
                          100
                      )}%`,
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right — breakdown bars */}
        {totalVotes > 0 && (
          <div className="space-y-1.5">
            <Bar label="Strong Buy"  count={strong_buy}  color="bg-emerald-500" />
            <Bar label="Buy"         count={buy}          color="bg-green-500"   />
            <Bar label="Hold"        count={hold}         color="bg-yellow-500"  />
            <Bar label="Sell"        count={sell}         color="bg-orange-500"  />
            <Bar label="Strong Sell" count={strong_sell}  color="bg-red-500"     />
          </div>
        )}
      </div>

      {totalVotes === 0 && !target_mean_price && (
        <p className="text-xs text-gray-500 italic mt-2">Detailed breakdown not available for this ticker.</p>
      )}
    </div>
  );
};

export default AnalystRatings;
