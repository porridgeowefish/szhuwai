import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { quotaAPI } from '../lib/api/quota';
import { QuotaInfo } from '../lib/api/types';

interface QuotaContextType {
  quota: QuotaInfo | null;
  loading: boolean;
  error: string | null;
  fetchQuota: () => Promise<void>;
}

const QuotaContext = createContext<QuotaContextType | undefined>(undefined);

export const QuotaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuota = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await quotaAPI.getQuota();
      setQuota(response.data);
    } catch (err: any) {
      setError(err.message || '获取额度信息失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 每 60 秒刷新一次额度
  useEffect(() => {
    fetchQuota();
    const interval = setInterval(fetchQuota, 60000);
    return () => clearInterval(interval);
  }, [fetchQuota]);

  const value: QuotaContextType = {
    quota,
    loading,
    error,
    fetchQuota,
  };

  return <QuotaContext.Provider value={value}>{children}</QuotaContext.Provider>;
};

export const useQuota = () => {
  const context = useContext(QuotaContext);
  if (context === undefined) {
    throw new Error('useQuota must be used within a QuotaProvider');
  }
  return context;
};
