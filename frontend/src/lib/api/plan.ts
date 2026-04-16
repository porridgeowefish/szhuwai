/**
 * 计划生成相关 API
 */
import apiClient from './client';
import { ApiResponse } from './types';
import { PlanData } from '../../types';

export const planAPI = {
  /**
   * 生成户外活动计划
   */
  generate: (formData: FormData) =>
    apiClient.post<ApiResponse<{ plan: PlanData }>>('/plan/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
};
