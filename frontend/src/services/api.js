import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds timeout for model loading
});

export const analyzeStock = async (ticker, companyName) => {
  try {
    const response = await api.post('/api/analyze', {
      ticker,
      company_name: companyName,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || error.message || 'Failed to analyze stock';
  }
};

export const checkHealth = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    return {
      status: 'unreachable',
      news_api: 'unknown',
      finnhub: 'unknown',
      model_loaded: false,
    };
  }
};

export const getSources = async () => {
  try {
    const response = await api.get('/api/sources');
    return response.data;
  } catch (error) {
    return { sources: [], model: { loaded: false } };
  }
};

export const getHistory = async (ticker, limit = 90) => {
  try {
    const response = await api.get(`/api/history/${encodeURIComponent(ticker)}`, { params: { limit } });
    return response.data;
  } catch (error) {
    return { ticker, snapshots: [], count: 0 };
  }
};
