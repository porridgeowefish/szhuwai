import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { User, Lock, Phone, Shield, Eye } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../lib/api/auth';
import { cn } from '../utils/cn';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const from = (location.state as any)?.from?.pathname || '/';

  const [loginType, setLoginType] = useState<'username' | 'phone'>('username');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    phone: '',
    code: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (loginType === 'username') {
        await login({ username: formData.username, password: formData.password });
      } else {
        await login({ phone: formData.phone, code: formData.code });
      }
      // 如果 from 是根路径或登录/注册页，跳转到报告中心，否则跳转到原页面
      const redirectPath = from === '/' || from.startsWith('/auth') ? '/reports' : from;
      navigate(redirectPath, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || '登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!formData.phone || !/^1[3-9]\d{9}$/.test(formData.phone)) {
      setError('请输入正确的手机号');
      return;
    }

    try {
      await authAPI.sendSms(formData.phone, 'login');
      setError(null);
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.message || '发送验证码失败');
    }
  };

  return (
    <div className="min-h-screen bg-[var(--sand)] flex items-center justify-center px-4 py-12">
      {/* 背景装饰 */}
      <div className="absolute inset-0 mountain-gradient opacity-50" />
      <div className="absolute inset-0 nature-texture opacity-20" />

      {/* 登录卡片 */}
      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--forest)] text-white mb-4">
            <Shield size={32} />
          </div>
          <h1 className="text-2xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            欢迎回来
          </h1>
          <p className="text-sm text-zinc-500 mt-2">登录您的账户继续使用</p>
        </div>

        <div className="glass rounded-3xl p-8 shadow-2xl">
          {/* 登录方式切换 */}
          <div className="flex mb-6 bg-[var(--sand)] rounded-xl p-1">
            <button
              onClick={() => setLoginType('username')}
              className={cn(
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                loginType === 'username'
                  ? 'bg-white text-[var(--forest)] shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-700'
              )}
            >
              账号密码登录
            </button>
            <button
              onClick={() => setLoginType('phone')}
              className={cn(
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                loginType === 'phone'
                  ? 'bg-white text-[var(--forest)] shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-700'
              )}
            >
              验证码登录
            </button>
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
                {error}
              </div>
            )}

            {loginType === 'username' ? (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-zinc-700">用户名</label>
                  <div className="relative">
                    <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                      placeholder="请输入用户名"
                      disabled={loading}
                    />
                  </div>
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
                      placeholder="请输入密码"
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                    >
                      {showPassword ? <Eye size={18} /> : <Eye size={18} className="opacity-50" />}
                    </button>
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
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                      placeholder="请输入手机号"
                      disabled={loading}
                    />
                  </div>
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
              {loading ? '登录中...' : '登录'}
            </button>
          </form>

          {/* 底部链接 */}
          <div className="mt-6 text-center text-sm">
            <span className="text-zinc-500">还没有账户？</span>
            <Link to="/auth/register" className="text-[var(--forest)] font-medium hover:underline ml-1">
              立即注册
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
