/**
 * API 通用类型定义
 */

/** API 响应包装 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 分页参数 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** 用户信息 */
export interface User {
  id: number;
  username: string | null;
  phone?: string;
  role: 'user' | 'admin';
  status: 'active' | 'disabled';
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
}

/** 额度信息 */
export interface QuotaInfo {
  used: number;
  total: number;
  remaining: number;
  reset_at: string;
}

/** 登录请求 */
export interface LoginRequest {
  username?: string;
  password?: string;
  phone?: string;
  code?: string;
}

/** 登录响应 */
export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}

/** 注册请求 */
export interface RegisterRequest {
  username?: string;
  password?: string;
  phone?: string;
  code?: string;
}

/** 报告文档 */
export interface ReportDocument {
  id: string;
  userId: number;
  planName: string;
  tripDate: string;
  overallRating: string;
  content: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}
