import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { quotaAPI } from '../lib/api/quota';
import { QuotaInfo } from '../lib/api/types';
import { useAuth } from './AuthContext';
import { getTimeUntilReset } from '../utils/time';

interface QuotaContextType {
  quota: QuotaInfo | null;
  loading: boolean;
  error: string | null;
  fetchQuota: () => Promise<void>;
  getTimeUntilReset: () => string;
}

const QuotaContext = createContext<QuotaContextType | undefined>(undefined);

export const QuotaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuota = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const data = await quotaAPI.getQuota() as unknown as QuotaInfo;
      setQuota(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取额度信息失败';
      if (!message.includes('401')) {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchQuota();
      const interval = setInterval(fetchQuota, 60000);
      return () => clearInterval(interval);
    } else {
      setQuota(null);
    }
  }, [isAuthenticated, fetchQuota]);

  const value: QuotaContextType = {
    quota,
    loading,
    error,
    fetchQuota,
    getTimeUntilReset,
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
