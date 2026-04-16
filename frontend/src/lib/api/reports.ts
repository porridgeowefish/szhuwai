/**
 * 报告相关 API
 */
import apiClient from './client';
import { ApiResponse, PaginatedResponse, PaginationParams, ReportDocument } from './types';

export const reportsAPI = {
  /**
   * 获取我的报告列表
   */
  list: (params?: PaginationParams) =>
    apiClient.get<ApiResponse<PaginatedResponse<ReportDocument>>>('/reports', { params }),

  /**
   * 获取报告详情
   */
  get: (reportId: string) =>
    apiClient.get<ApiResponse<ReportDocument>>(`/reports/${reportId}`),

  /**
   * 删除报告
   */
  delete: (reportId: string) =>
    apiClient.delete<ApiResponse<void>>(`/reports/${reportId}`),
};
