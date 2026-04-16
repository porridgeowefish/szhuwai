/**
 * 认证相关 API
 */
import apiClient from './client';
import {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from './types';

export const authAPI = {
  /**
   * 用户名密码登录
   */
  login: (data: Pick<LoginRequest, 'username' | 'password'>) =>
    apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data),

  /**
   * 手机号验证码登录
   */
  loginWithPhone: (data: Pick<LoginRequest, 'phone' | 'code'>) =>
    apiClient.post<ApiResponse<LoginResponse>>('/auth/sms/login', data),

  /**
   * 用户名注册
   * 返回 UserWithToken: { user, accessToken, tokenType, expiresIn }
   */
  register: (data: Pick<RegisterRequest, 'username' | 'password'>) =>
    apiClient.post<ApiResponse<{ user: User; accessToken: string; tokenType: string; expiresIn: number }>>('/auth/register', data),

  /**
   * 手机号注册
   * 返回 UserWithToken: { user, accessToken, tokenType, expiresIn }
   */
  registerWithPhone: (data: Pick<RegisterRequest, 'phone' | 'code' | 'password'>) =>
    apiClient.post<ApiResponse<{ user: User; accessToken: string; tokenType: string; expiresIn: number }>>('/auth/sms/register', data),

  /**
   * 发送短信验证码
   */
  sendSms: (phone: string, scene: 'register' | 'login' | 'bind' | 'unbind' | 'reset_password' = 'login') =>
    apiClient.post<ApiResponse<void>>('/auth/sms/send', { phone, scene }),

  /**
   * 获取当前用户信息
   */
  getCurrentUser: () =>
    apiClient.get<ApiResponse<User>>('/auth/me'),

  /**
   * 修改密码
   */
  changePassword: (data: { old_password: string; new_password: string }) =>
    apiClient.post<ApiResponse<void>>('/auth/password/change', data),

  /**
   * 重置密码
   */
  resetPassword: (data: { phone: string; code: string; new_password: string }) =>
    apiClient.post<ApiResponse<void>>('/auth/password/reset', data),

  /**
   * 绑定手机号
   */
  bindPhone: (data: { phone: string; code: string }) =>
    apiClient.post<ApiResponse<void>>('/auth/phone/bind', data),

  /**
   * 解绑手机号
   */
  unbindPhone: (data: { code: string }) =>
    apiClient.post<ApiResponse<void>>('/auth/phone/unbind', data),

  /**
   * 检查用户名或手机号是否已存在
   * 注意：响应拦截器会自动解包，返回的 data 直接是 { exists, field }
   */
  checkExists: (data: { username?: string; phone?: string }) =>
    apiClient.post<{ exists: boolean; field: string }>('/auth/check-exists', data),
};
