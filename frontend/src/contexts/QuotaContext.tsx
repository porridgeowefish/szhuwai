import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { quotaAPI } from '../lib/api/quota';
import { QuotaInfo } from '../lib/api/types';
import { useAuth } from './AuthContext';

interface QuotaContextType {
  quota: QuotaInfo | null;
  loading: boolean;
  error: string | null;
  fetchQuota: () => Promise<void>;
  /** 计算距离下次刷新（凌晨）的倒计时字符串 */
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
      // 响应拦截器已解包，直接是额度数据
      const data = await quotaAPI.getQuota() as any;
      setQuota(data);
    } catch (err: any) {
      // 401 错误不显示（由拦截器统一处理）
      if (!err.message?.includes('401')) {
        setError(err.message || '获取额度信息失败');
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // 计算距离凌晨的倒计时
  const getTimeUntilReset = useCallback((): string => {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);

    const diff = tomorrow.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    return `${hours}小时${minutes}分钟后刷新`;
  }, []);

  // 只在已认证时请求额度
  useEffect(() => {
    if (isAuthenticated) {
      fetchQuota();
      const interval = setInterval(fetchQuota, 60000);
      return () => clearInterval(interval);
    } else {
      // 未认证时清空额度
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
