import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const SentimentGauge = ({ sentiment, confidence }) => {
  // Determine color based on sentiment
  const getColor = () => {
    switch (sentiment) {
      case 'positive':
        return '#10b981';
      case 'negative':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  // Calculate gauge position (0 = negative, 0.5 = neutral, 1 = positive)
  const getGaugePosition = () => {
    switch (sentiment) {
      case 'positive':
        return 0.75;
      case 'negative':
        return 0.25;
      default:
        return 0.5;
    }
  };

  const data = [
    { name: 'Filled', value: getGaugePosition() * 100 },
    { name: 'Empty', value: 100 - getGaugePosition() * 100 },
  ];

  const color = getColor();

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-40">
        <ResponsiveContainer width="100%" height="85%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={55}
              outerRadius={75}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              <Cell fill={color} />
              <Cell fill="rgba(107, 114, 128, 0.2)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        
        {/* Center Label - positioned below the gauge */}
        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 text-center w-full">
          <div 
            className="text-2xl font-bold capitalize leading-tight"
            style={{ color }}
          >
            {sentiment}
          </div>
          <div className="text-xs text-gray-400 mt-0.5">
            {(confidence * 100).toFixed(1)}% confidence
          </div>
        </div>
      </div>
    </div>
  );
};

export default SentimentGauge;
