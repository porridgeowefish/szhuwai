import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../lib/api/auth';
import { User, LoginRequest } from '../lib/api/types';
import { STORAGE_KEYS } from '../utils/constants';

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

  useEffect(() => {
    const storedToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
      }
    }
    setIsInitialized(true);
  }, []);

  const login = useCallback(async (credentials: LoginRequest & { _token?: string }) => {
    if (credentials._token) {
      const tempToken = credentials._token;
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tempToken);

      const userData = await authAPI.getCurrentUser() as unknown as User;

      setToken(tempToken);
      setUser(userData);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      return;
    }

    const response = await (credentials.username
      ? authAPI.login({ username: credentials.username, password: credentials.password })
      : authAPI.loginWithPhone({ phone: credentials.phone!, code: credentials.code! })) as unknown as { accessToken: string; user: User };

    const { accessToken, user: userData } = response;

    if (!accessToken || !userData) {
      throw new Error('登录响应格式错误');
    }

    setToken(accessToken);
    setUser(userData);
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, []);

  const updateUser = useCallback(async () => {
    const userData = await authAPI.getCurrentUser() as unknown as User;
    setUser(userData);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
  }, []);

  const value: AuthContextType = {
    isAuthenticated: !!token && !!user,
    user,
    token,
    login,
    logout,
    updateUser,
  };

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
