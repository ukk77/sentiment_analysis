import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, Activity } from 'lucide-react';
import { checkHealth } from '../services/api';

const HealthStatus = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch {
        setHealth({
          status: 'unreachable',
          news_api: 'unknown',
          finnhub: 'unknown',
          model_loaded: false,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'unreachable':
      case 'invalid_api_key':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Activity className="w-4 h-4 animate-pulse" />
        <span>Checking services...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-1.5">
        {getStatusIcon(health?.news_api)}
        <span className={`${health?.news_api === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
          NewsAPI
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        {getStatusIcon(health?.finnhub)}
        <span className={`${health?.finnhub === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
          Finnhub
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        {health?.model_loaded ? (
          <CheckCircle className="w-4 h-4 text-green-500" />
        ) : (
          <XCircle className="w-4 h-4 text-red-500" />
        )}
        <span className={health?.model_loaded ? 'text-green-400' : 'text-red-400'}>
          FinBERT
        </span>
      </div>
    </div>
  );
};

export default HealthStatus;
