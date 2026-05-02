import React from 'react';

const SentimentBar = ({ positive, negative, neutral, total }) => {
  const positivePercent = total > 0 ? (positive / total) * 100 : 0;
  const negativePercent = total > 0 ? (negative / total) * 100 : 0;
  const neutralPercent = total > 0 ? (neutral / total) * 100 : 0;

  return (
    <div className="w-full">
      <div className="flex h-4 rounded-full overflow-hidden bg-gray-700">
        {positive > 0 && (
          <div
            className="bg-sentiment-positive"
            style={{ width: `${positivePercent}%` }}
            title={`Positive: ${positive} (${positivePercent.toFixed(1)}%)`}
          />
        )}
        {neutral > 0 && (
          <div
            className="bg-sentiment-neutral"
            style={{ width: `${neutralPercent}%` }}
            title={`Neutral: ${neutral} (${neutralPercent.toFixed(1)}%)`}
          />
        )}
        {negative > 0 && (
          <div
            className="bg-sentiment-negative"
            style={{ width: `${negativePercent}%` }}
            title={`Negative: ${negative} (${negativePercent.toFixed(1)}%)`}
          />
        )}
      </div>
      <div className="flex justify-between mt-2 text-sm">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sentiment-positive" />
          <span className="text-gray-300">{positive} Positive</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sentiment-neutral" />
          <span className="text-gray-300">{neutral} Neutral</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sentiment-negative" />
          <span className="text-gray-300">{negative} Negative</span>
        </div>
      </div>
    </div>
  );
};

export default SentimentBar;
