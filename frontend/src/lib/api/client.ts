import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse } from './types';

/**
 * API 客户端
 * baseURL: /api/v1
 * timeout: 30秒
 */
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器 - 自动添加 Token
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 防止 401 跳转循环
let isRedirecting = false;

/**
 * 响应拦截器 - 统一错误处理
 * 自动解包 response.data.data
 */
apiClient.interceptors.response.use(
  (response: any) => {
    const res = response.data;
    // 检查业务层错误码（后端用 HTTP 200 返回业务错误）
    if (res?.code && res.code !== 200) {
      const error: any = new Error(res.message || '请求失败');
      error.code = res.code;
      return Promise.reject(error);
    }
    return res?.data;
  },
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;

      // 401 未授权 - 清除 Token 并跳转登录
      if (status === 401 && !isRedirecting) {
        isRedirecting = true;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        // 延迟重置标志，确保跳转完成
        setTimeout(() => { isRedirecting = false; }, 1000);
        if (window.location.pathname !== '/auth/login' && window.location.pathname !== '/auth/register') {
          window.location.href = '/auth/login';
        }
      }

      // 403 禁止访问
      if (status === 403) {
        console.error('权限不足');
      }

      // 404 未找到
      if (status === 404) {
        console.error('请求的资源不存在');
      }

      // 500 服务器错误
      if (status >= 500) {
        console.error('服务器错误，请稍后重试');
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
