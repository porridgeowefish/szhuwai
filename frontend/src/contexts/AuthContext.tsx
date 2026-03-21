import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../lib/api/auth';
import { User, LoginRequest, LoginResponse } from '../lib/api/types';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (credentials: LoginRequest & { _token?: string }) => Promise<void>;
  logout: () => void;
  updateUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // 初始化：从 localStorage 恢复登录状态
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        // 解析失败，清除存储
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    setIsInitialized(true);
  }, []);

  const login = useCallback(async (credentials: LoginRequest & { _token?: string }) => {
    // 如果已提供 token（注册后直接登录），直接使用
    if (credentials._token) {
      // 获取用户信息
      const tempToken = credentials._token;
      localStorage.setItem('access_token', tempToken);

      const response = await authAPI.getCurrentUser();
      const userData = response.data;

      setToken(tempToken);
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return;
    }

    // 否则调用登录 API
    const response = await (credentials.username
      ? authAPI.login({ username: credentials.username, password: credentials.password })
      : authAPI.loginWithPhone({ phone: credentials.phone, code: credentials.code })) as any;

    const { access_token, user: userData } = response;

    // 保存到 state
    setToken(access_token);
    setUser(userData);

    // 保存到 localStorage
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }, []);

  const updateUser = useCallback(async () => {
    const response = await authAPI.getCurrentUser();
    const userData = response.data;
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  const value: AuthContextType = {
    isAuthenticated: !!token && !!user,
    user,
    token,
    login,
    logout,
    updateUser,
  };

  // 未初始化时不渲染子组件
  if (!isInitialized) {
    return null;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
