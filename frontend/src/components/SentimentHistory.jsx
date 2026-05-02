import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { History, TrendingUp, TrendingDown } from 'lucide-react';
import { getHistory } from '../services/api';

const SENTIMENT_COLOR = (v) => {
  if (v > 0.1)  return '#10b981';
  if (v < -0.1) return '#ef4444';
  return '#6b7280';
};

const SentimentHistory = ({ ticker }) => {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    getHistory(ticker)
      .then((res) => setData(res))
      .catch(() => setError('Could not load history'))
      .finally(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return (
      <div className="card flex items-center justify-center h-40">
        <p className="text-gray-400 text-sm animate-pulse">Loading history…</p>
      </div>
    );
  }

  if (error || !data || data.count === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <History className="w-4 h-4 text-indigo-400" />
          <h3 className="text-lg font-semibold text-gray-300">Historical Tracking</h3>
        </div>
        <p className="text-xs text-gray-500 italic">
          {data?.count === 0
            ? 'No history yet — re-run the analysis to start building a trend.'
            : error || 'Unavailable'}
        </p>
      </div>
    );
  }

  // Reverse so oldest → newest on the X axis
  const chartData = [...data.snapshots].reverse().map((s, i) => ({
    idx: i + 1,
    date: new Date(s.captured_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    avg_sentiment: parseFloat(s.avg_sentiment.toFixed(3)),
    overall: s.overall_sentiment,
    articles: s.total_articles,
  }));

  const latest  = chartData[chartData.length - 1];
  const prev    = chartData[chartData.length - 2];
  const trend   = prev ? latest.avg_sentiment - prev.avg_sentiment : 0;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-400" />
          <h3 className="text-lg font-semibold text-gray-300">Historical Tracking</h3>
          <span className="text-xs text-gray-500">({data.count} runs)</span>
        </div>
        {latest && (
          <div className="flex items-center gap-1.5 text-sm">
            <span style={{ color: SENTIMENT_COLOR(latest.avg_sentiment) }} className="font-semibold">
              {latest.avg_sentiment > 0 ? '+' : ''}{latest.avg_sentiment.toFixed(3)}
            </span>
            {trend !== 0 && (
              <span className={`flex items-center gap-0.5 text-xs ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {trend > 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                {trend > 0 ? '+' : ''}{trend.toFixed(3)} vs prev
              </span>
            )}
          </div>
        )}
      </div>

      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={10} tickLine={false} />
            <YAxis
              stroke="#6b7280"
              fontSize={10}
              domain={[-1, 1]}
              ticks={[-1, -0.5, 0, 0.5, 1]}
              tickFormatter={(v) => v.toFixed(1)}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }}
              formatter={(value, name) => [value.toFixed(3), 'Avg Sentiment']}
              labelFormatter={(label) => `Run: ${label}`}
            />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 4" strokeWidth={1} />
            <Line
              type="monotone"
              dataKey="avg_sentiment"
              stroke="#818cf8"
              strokeWidth={2}
              dot={(props) => {
                const { cx, cy, payload } = props;
                return (
                  <circle
                    key={payload.idx}
                    cx={cx} cy={cy} r={3}
                    fill={SENTIMENT_COLOR(payload.avg_sentiment)}
                    stroke="none"
                  />
                );
              }}
              activeDot={{ r: 5 }}
              name="Avg Sentiment"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-2 text-xs text-gray-500 italic">
        One data point per analysis run · stored in local SQLite DB
      </p>
    </div>
  );
};

export default SentimentHistory;
