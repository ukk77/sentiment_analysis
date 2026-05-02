import React from 'react';
import { FileText, Database, Activity, TrendingUp } from 'lucide-react';

const MetricsCard = ({ title, value, subtitle, icon: Icon, color = 'blue' }) => {
  const getColorClass = () => {
    switch (color) {
      case 'green':
        return 'text-green-400';
      case 'red':
        return 'text-red-400';
      case 'purple':
        return 'text-purple-400';
      default:
        return 'text-blue-400';
    }
  };

  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl bg-opacity-10 ${getColorClass()} bg-current`}>
        <Icon className={`w-6 h-6 ${getColorClass()}`} />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-gray-400">{title}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div>}
      </div>
    </div>
  );
};

export default MetricsCard;
