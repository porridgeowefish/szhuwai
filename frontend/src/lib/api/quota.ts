/**
 * 额度相关 API
 */
import apiClient from './client';
import { ApiResponse, QuotaInfo } from './types';

export const quotaAPI = {
  /**
   * 获取今日额度信息
   */
  getQuota: () =>
    apiClient.get<ApiResponse<QuotaInfo>>('/quota'),
};
