import React from 'react';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Info, AlertTriangle } from 'lucide-react';

const PEARSON_COLOR = (r) => {
  if (r === null || r === undefined) return 'text-gray-400';
  if (r > 0.3)  return 'text-green-400';
  if (r < -0.3) return 'text-red-400';
  return 'text-yellow-400';
};

const PriceSentimentChart = ({
  priceData,
  avgSentiment,
  dailySentiment = {},
  selectedDate,
  onDateClick,
  correlation = null,
  articles = [],
}) => {
  if (!priceData || !priceData.history || priceData.history.length === 0) {
    return (
      <div className="card flex items-center justify-center h-64">
        <p className="text-gray-400">No price data available</p>
      </div>
    );
  }

  // Build 3-day rolling sentiment from dailySentiment map
  const sortedSentDates = Object.keys(dailySentiment).sort();
  const rolling3d = (dateKey) => {
    const window = sortedSentDates.filter((d) => d <= dateKey).slice(-3);
    if (window.length === 0) return null;
    const avg = window.reduce((s, d) => s + dailySentiment[d], 0) / window.length;
    return parseFloat(avg.toFixed(3));
  };

  // Build high-impact article dates (impact_score >= 0.3)
  const highImpactDates = new Set(
    articles
      .filter((a) => (a.impact_score || 0) >= 0.3 && a.published_at)
      .map((a) => {
        try { return new Date(a.published_at).toISOString().split('T')[0]; } catch { return null; }
      })
      .filter(Boolean)
  );

  // Map price history to chart data
  const chartData = priceData.history.map((day) => {
    const dateKey = new Date(day.date).toISOString().split('T')[0];
    const sentimentScore = dailySentiment[dateKey] ?? null;
    const rollingScore   = rolling3d(dateKey);
    return {
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      dateKey,
      price:     day.close,
      sentiment: sentimentScore !== null ? parseFloat(sentimentScore.toFixed(3)) : null,
      rolling3d: rollingScore,
      volume:    day.volume / 1_000_000,
      highImpact: highImpactDates.has(dateKey),
    };
  });

  const daysWithSentiment = chartData.filter((d) => d.sentiment !== null).length;
  const totalDays          = chartData.length;

  const selectedLabel = selectedDate
    ? chartData.find((d) => d.dateKey === selectedDate)?.date ?? null
    : null;

  const handleChartClick = (data) => {
    if (data?.activePayload?.length > 0) {
      const dateKey = data.activePayload[0].payload.dateKey;
      if (dateKey && onDateClick) onDateClick(dateKey);
    }
  };

  const currentPrice   = priceData.current_price;
  const priceChange    = priceData.price_change;
  const priceChangePct = priceData.price_change_percent;
  const isPositive     = priceChange >= 0;

  const pearsonR        = correlation?.pearson_r ?? null;
  const divergenceAlert = correlation?.divergence_alert ?? false;
  const divDirection    = correlation?.divergence_direction ?? null;
  const leadLag         = correlation?.lead_lag ?? [];

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-300">Price & Sentiment Correlation</h3>

            {/* Pearson r badge */}
            {pearsonR !== null && (
              <span
                title="Pearson r: correlation between same-day price returns and sentiment scores. Range −1 to +1."
                className={`px-2 py-0.5 rounded-full text-xs font-semibold border bg-gray-800 border-gray-600 cursor-help ${PEARSON_COLOR(pearsonR)}`}
              >
                r = {pearsonR > 0 ? '+' : ''}{pearsonR.toFixed(2)}
              </span>
            )}

            {/* Divergence alert */}
            {divergenceAlert && (
              <span
                title={divDirection === 'price_up_sentiment_down'
                  ? 'Price rising while sentiment is falling — potential reversal signal'
                  : 'Price falling while sentiment is rising — potential recovery signal'}
                className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border bg-yellow-500/15 border-yellow-500/40 text-yellow-300 cursor-help"
              >
                <AlertTriangle className="w-3 h-3" />
                Divergence
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 mt-0.5">
            <Info className="w-3 h-3 text-gray-500" />
            <span className="text-xs text-gray-500">
              Sentiment data: {daysWithSentiment} of {totalDays} days
              {daysWithSentiment === 0 && ' — no articles with parseable dates'}
            </span>
          </div>
        </div>

        <div className="text-right">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-gray-400" />
            <span className="text-2xl font-bold text-white">${currentPrice.toFixed(2)}</span>
          </div>
          <div className={`flex items-center gap-1 text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%)</span>
          </div>
        </div>
      </div>

      <p className="text-xs text-gray-500 mb-2 italic">Click any point on the chart to filter articles by that day</p>

      {/* Chart */}
      <div className="h-72 mt-2" style={{ cursor: 'pointer' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }} onClick={handleChartClick}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={10} tickLine={false} />
            <YAxis
              yAxisId="price"
              orientation="left"
              stroke="#3b82f6"
              fontSize={10}
              tickFormatter={(v) => `$${v.toFixed(0)}`}
            />
            <YAxis
              yAxisId="sentiment"
              orientation="right"
              stroke="#10b981"
              fontSize={10}
              domain={[-1, 1]}
              tickFormatter={(v) => v.toFixed(1)}
              ticks={[-1, -0.5, 0, 0.5, 1]}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }}
              formatter={(value, name) => {
                if (name === 'price')     return [`$${value.toFixed(2)}`, 'Stock Price'];
                if (name === 'sentiment') return [value?.toFixed(3), 'Daily Avg Sentiment'];
                if (name === 'rolling3d') return [value?.toFixed(3), '3-Day Rolling Avg'];
                if (name === 'volume')    return [`${value.toFixed(1)}M`, 'Volume'];
                return [value, name];
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />

            {/* Zero line */}
            <ReferenceLine yAxisId="sentiment" y={0} stroke="#6b7280" strokeDasharray="2 4" strokeWidth={1} />

            {/* Selected date */}
            {selectedLabel && (
              <ReferenceLine
                yAxisId="price"
                x={selectedLabel}
                stroke="#60a5fa"
                strokeWidth={2}
                strokeDasharray="4 3"
                label={{ value: '▼', position: 'insideTop', fill: '#60a5fa', fontSize: 12 }}
              />
            )}

            {/* High-impact article markers */}
            {chartData
              .filter((d) => d.highImpact)
              .map((d) => (
                <ReferenceLine
                  key={d.dateKey}
                  yAxisId="price"
                  x={d.date}
                  stroke="#f59e0b"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  label={{ value: '⚡', position: 'insideTop', fill: '#f59e0b', fontSize: 10 }}
                />
              ))}

            {/* Volume bars */}
            <Bar yAxisId="price" dataKey="volume" fill="rgba(107,114,128,0.15)" name="Volume (M)" />

            {/* Price line */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="price"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Stock Price"
            />

            {/* Daily sentiment (dashed) */}
            <Line
              yAxisId="sentiment"
              type="monotone"
              dataKey="sentiment"
              stroke="#10b981"
              strokeWidth={1.5}
              dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
              connectNulls={false}
              name="Daily Sentiment"
              strokeDasharray="5 5"
            />

            {/* 3-Day rolling avg (solid) */}
            <Line
              yAxisId="sentiment"
              type="monotone"
              dataKey="rolling3d"
              stroke="#34d399"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name="3-Day Rolling Avg"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Footer legend */}
      <div className="mt-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-0.5 bg-blue-500 rounded" />
            <span>Price (left)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4" style={{ borderTop: '2px dashed #10b981' }} />
            <span>Sentiment</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-0.5 bg-emerald-400 rounded" />
            <span>3d Rolling Avg</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-2.5 rounded-sm" style={{ background: 'rgba(107,114,128,0.3)' }} />
            <span>Volume</span>
          </div>
          {highImpactDates.size > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-amber-400 text-xs">⚡</span>
              <span>High-impact article</span>
            </div>
          )}
        </div>
        <div className="text-xs text-gray-500 italic">
          Sentiment = avg of all articles published that day
        </div>
      </div>

      {/* Lead / Lag table */}
      {leadLag.length > 0 && (
        <div className="mt-4 border-t border-gray-700/50 pt-3">
          <p className="text-xs font-semibold text-gray-400 mb-2">Lead / Lag Analysis — does today's sentiment predict future price?</p>
          <div className="flex gap-3 flex-wrap">
            {leadLag.map((ll) => {
              const color = ll.correlation > 0.2 ? 'text-green-400' : ll.correlation < -0.2 ? 'text-red-400' : 'text-gray-400';
              return (
                <div key={ll.offset_days} className="flex flex-col items-center px-3 py-1.5 rounded-lg bg-gray-800/60 border border-gray-700/50 min-w-[70px]">
                  <span className="text-xs text-gray-500">+{ll.offset_days}d</span>
                  <span className={`text-sm font-bold ${color}`}>
                    {ll.correlation > 0 ? '+' : ''}{ll.correlation.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-600 mt-1.5 italic">
            +1d = correlation between today's sentiment and tomorrow's price return
          </p>
        </div>
      )}
    </div>
  );
};

export default PriceSentimentChart;
