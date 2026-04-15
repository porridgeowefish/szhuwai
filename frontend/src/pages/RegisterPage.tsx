import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User as UserIcon, Lock, Phone, Shield, Eye, EyeOff, Check, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../lib/api/auth';
import type { User } from '../lib/api/types';
import { cn } from '../utils/cn';

const PHONE_REGEX = /^1[3-9]\d{9}$/;

type PasswordStrengthLevel = 'weak' | 'medium' | 'strong';

interface PasswordStrengthInfo {
  level: PasswordStrengthLevel;
  score: number; // 0-3
  label: string;
}

function getPasswordStrength(password: string): PasswordStrengthInfo {
  if (!password) return { level: 'weak', score: 0, label: '' };

  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasDigit = /\d/.test(password);
  const hasSpecial = /[^a-zA-Z0-9]/.test(password);

  // 弱：< 6 位 或 纯数字/纯字母
  if (password.length < 6) {
    return { level: 'weak', score: 1, label: '弱' };
  }
  const isOnlyDigits = /^\d+$/.test(password);
  const isOnlyLetters = /^[a-zA-Z]+$/.test(password);
  if (isOnlyDigits || isOnlyLetters) {
    return { level: 'weak', score: 1, label: '弱' };
  }

  // 强：8+ 位，包含大小写字母、数字和特殊字符
  if (password.length >= 8 && hasUpper && hasLower && hasDigit && hasSpecial) {
    return { level: 'strong', score: 3, label: '强' };
  }

  // 中：6+ 位，包含字母和数字
  return { level: 'medium', score: 2, label: '中' };
}

const PasswordStrengthBar: React.FC<{ password: string }> = ({ password }) => {
  const strength = useMemo(() => getPasswordStrength(password), [password]);

  if (!password) return null;

  const colorMap: Record<PasswordStrengthLevel, string> = {
    weak: 'bg-red-500',
    medium: 'bg-amber-400',
    strong: 'bg-green-500',
  };

  const textColorMap: Record<PasswordStrengthLevel, string> = {
    weak: 'text-red-500',
    medium: 'text-amber-500',
    strong: 'text-green-600',
  };

  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex gap-1">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={cn(
              'h-1.5 w-4 rounded-full transition-colors',
              i <= strength.score ? colorMap[strength.level] : 'bg-zinc-200'
            )}
          />
        ))}
      </div>
      <span className={cn('text-xs font-medium', textColorMap[strength.level])}>
        {strength.label}
      </span>
    </div>
  );
};

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [registerType, setRegisterType] = useState<'username' | 'phone'>('username');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    phone: '',
    code: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  // 新增：实时验证状态
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'exists' | 'available'>('idle');
  const [phoneStatus, setPhoneStatus] = useState<'idle' | 'checking' | 'exists' | 'available'>('idle');
  const checkUsernameRef = useRef<NodeJS.Timeout | null>(null);
  const checkPhoneRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (checkUsernameRef.current) clearTimeout(checkUsernameRef.current);
      if (checkPhoneRef.current) clearTimeout(checkPhoneRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, []);

  // 防抖检查用户名是否存在
  const checkUsernameExists = useCallback(async (username: string) => {
    if (!username || username.length < 3) {
      setUsernameStatus('idle');
      return;
    }

    setUsernameStatus('checking');
    try {
      const result = await authAPI.checkExists({ username }) as unknown as { exists: boolean; field?: string };
      if (result?.exists) {
        setUsernameStatus('exists');
      } else {
        setUsernameStatus('available');
      }
    } catch {
      // 忽略错误，保持 idle 状态
      setUsernameStatus('idle');
    }
  }, []);

  // 防抖检查手机号是否存在
  const checkPhoneExists = useCallback(async (phone: string) => {
    if (!phone || !PHONE_REGEX.test(phone)) {
      setPhoneStatus('idle');
      return;
    }

    setPhoneStatus('checking');
    try {
      const result = await authAPI.checkExists({ phone }) as unknown as { exists: boolean; field?: string };
      if (result?.exists) {
        setPhoneStatus('exists');
      } else {
        setPhoneStatus('available');
      }
    } catch {
      // 忽略错误，保持 idle 状态
      setPhoneStatus('idle');
    }
  }, []);

  // 监听用户名输入变化
  useEffect(() => {
    if (checkUsernameRef.current) {
      clearTimeout(checkUsernameRef.current);
    }
    checkUsernameRef.current = setTimeout(() => {
      checkUsernameExists(formData.username);
    }, 500);
    return () => {
      if (checkUsernameRef.current) {
        clearTimeout(checkUsernameRef.current);
      }
    };
  }, [formData.username, checkUsernameExists]);

  // 监听手机号输入变化
  useEffect(() => {
    if (checkPhoneRef.current) {
      clearTimeout(checkPhoneRef.current);
    }
    checkPhoneRef.current = setTimeout(() => {
      checkPhoneExists(formData.phone);
    }, 500);
    return () => {
      if (checkPhoneRef.current) {
        clearTimeout(checkPhoneRef.current);
      }
    };
  }, [formData.phone, checkPhoneExists]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // 验证
    if (registerType === 'username') {
      if (usernameStatus === 'exists') {
        setError('该用户名已被注册，请更换');
        setLoading(false);
        return;
      }
      if (formData.password.length < 6) {
        setError('密码长度至少6位');
        setLoading(false);
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        setError('两次输入的密码不一致');
        setLoading(false);
        return;
      }
    } else {
      if (phoneStatus === 'exists') {
        setError('该手机号已被注册，请直接登录');
        setLoading(false);
        return;
      }
      if (!formData.phone || !PHONE_REGEX.test(formData.phone)) {
        setError('请输入正确的手机号');
        setLoading(false);
        return;
      }
      if (!formData.code) {
        setError('请输入验证码');
        setLoading(false);
        return;
      }
    }

    try {
      if (registerType === 'username') {
        const registerResult = await authAPI.register({ username: formData.username, password: formData.password }) as unknown as { accessToken: string; user?: User };
        // 注册成功后使用返回的 token 直接登录
        await login({ username: formData.username, password: formData.password, _token: registerResult.accessToken });
      } else {
        const registerResult = await authAPI.registerWithPhone({ phone: formData.phone, code: formData.code, password: formData.password || undefined }) as unknown as { accessToken: string; user?: User };
        // 手机号注册后使用返回的 token 直接登录
        await login({ phone: formData.phone, code: formData.code, _token: registerResult.accessToken });
      }
      // 注册成功后跳转到报告中心
      navigate('/reports', { replace: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '注册失败，请稍后重试';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!formData.phone || !PHONE_REGEX.test(formData.phone)) {
      setError('请输入正确的手机号');
      return;
    }

    try {
      await authAPI.sendSms(formData.phone, 'register');
      setError(null);
      setCountdown(60);
      // 清除旧定时器
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
      }
      countdownTimerRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            if (countdownTimerRef.current) {
              clearInterval(countdownTimerRef.current);
              countdownTimerRef.current = null;
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '发送验证码失败';
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--sand)] flex items-center justify-center px-4 py-12">
      {/* 背景装饰 */}
      <div className="absolute inset-0 mountain-gradient opacity-50" />
      <div className="absolute inset-0 nature-texture opacity-20" />

      {/* 注册卡片 */}
      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--forest)] text-white mb-4">
            <Shield size={32} />
          </div>
          <h1 className="text-2xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            创建账户
          </h1>
          <p className="text-sm text-zinc-500 mt-2">开始您的户外智能规划之旅</p>
        </div>

        <div className="glass rounded-3xl p-8 shadow-2xl">
          {/* 注册方式切换 */}
          <div className="flex mb-6 bg-[var(--sand)] rounded-xl p-1">
            <button
              onClick={() => setRegisterType('username')}
              className={cn(
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                registerType === 'username'
                  ? 'bg-white text-[var(--forest)] shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-700'
              )}
            >
              用户名注册
            </button>
            <button
              onClick={() => setRegisterType('phone')}
              className={cn(
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                registerType === 'phone'
                  ? 'bg-white text-[var(--forest)] shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-700'
              )}
            >
              手机号注册
            </button>
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
                {error}
              </div>
            )}

            {registerType === 'username' ? (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">用户名</label>
                  <div className="relative">
                    <UserIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className={cn(
                        'w-full pl-10 pr-10 py-3 rounded-xl input-nature',
                        usernameStatus === 'exists' && 'border-red-300 focus:border-red-500'
                      )}
                      placeholder="请输入用户名"
                      disabled={loading}
                    />
                    {usernameStatus === 'checking' && (
                      <Loader2 size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 animate-spin" />
                    )}
                    {usernameStatus === 'exists' && (
                      <AlertCircle size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500" />
                    )}
                    {usernameStatus === 'available' && (
                      <Check size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500" />
                    )}
                  </div>
                  {usernameStatus === 'exists' && (
                    <p className="text-xs text-red-500">该用户名已被注册</p>
                  )}
                  {usernameStatus === 'available' && (
                    <p className="text-xs text-green-600">该用户名可用</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">密码</label>
                  <div className="relative">
                    <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-10 pr-10 py-3 rounded-xl input-nature"
                      placeholder="请输入密码（至少6位）"
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                    >
                      {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
                    </button>
                  </div>
                  <PasswordStrengthBar password={formData.password} />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">确认密码</label>
                  <div className="relative">
                    <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                      className="w-full pl-10 pr-10 py-3 rounded-xl input-nature"
                      placeholder="请再次输入密码"
                      disabled={loading}
                    />
                    {formData.confirmPassword && formData.password === formData.confirmPassword && (
                      <Check size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500" />
                    )}
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">手机号</label>
                  <div className="relative">
                    <Phone size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, '').slice(0, 11) })}
                      className={cn(
                        'w-full pl-10 pr-10 py-3 rounded-xl input-nature',
                        phoneStatus === 'exists' && 'border-red-300 focus:border-red-500'
                      )}
                      placeholder="请输入手机号"
                      disabled={loading}
                    />
                    {phoneStatus === 'checking' && (
                      <Loader2 size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 animate-spin" />
                    )}
                    {phoneStatus === 'exists' && (
                      <AlertCircle size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500" />
                    )}
                    {phoneStatus === 'available' && (
                      <Check size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500" />
                    )}
                  </div>
                  {phoneStatus === 'exists' && (
                    <p className="text-xs text-red-500">该手机号已注册</p>
                  )}
                  {phoneStatus === 'available' && (
                    <p className="text-xs text-green-600">该手机号可用</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">验证码</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                      <input
                        type="text"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                        placeholder="请输入验证码"
                        disabled={loading}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={handleSendCode}
                      disabled={countdown > 0 || loading}
                      className={cn(
                        'px-4 py-3 rounded-xl text-sm font-medium whitespace-nowrap transition-all',
                        countdown > 0
                          ? 'bg-[var(--stone)] text-zinc-400 cursor-not-allowed'
                          : 'bg-[var(--forest)] text-white hover:bg-[var(--forest-dark)]'
                      )}
                    >
                      {countdown > 0 ? `${countdown}秒` : '发送验证码'}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">设置密码（可选）</label>
                  <div className="relative">
                    <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-10 pr-10 py-3 rounded-xl input-nature"
                      placeholder="可稍后在个人中心设置"
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                    >
                      {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
                    </button>
                  </div>
                  <PasswordStrengthBar password={formData.password} />
                  {!formData.password && (
                    <p className="text-xs text-zinc-400 mt-1">不设密码将使用手机号 + 验证码登录</p>
                  )}
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className={cn(
                'w-full py-4 rounded-xl text-white font-bold text-lg btn-forest',
                loading && 'opacity-70 cursor-not-allowed'
              )}
            >
              {loading ? '注册中...' : '注册'}
            </button>
          </form>

          {/* 底部链接 */}
          <div className="mt-6 text-center text-sm">
            <span className="text-zinc-500">已有账户？</span>
            <Link to="/auth/login" className="text-[var(--forest)] font-medium hover:underline ml-1">
              立即登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
