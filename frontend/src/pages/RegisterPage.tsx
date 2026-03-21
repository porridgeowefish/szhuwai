import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Lock, Phone, Shield, Eye, Check } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../lib/api/auth';
import { cn } from '../utils/cn';

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // 验证
    if (registerType === 'username') {
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
      if (!formData.phone || !/^1[3-9]\d{9}$/.test(formData.phone)) {
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
        await authAPI.register({ username: formData.username, password: formData.password });
        // 注册成功后自动登录
        await login({ username: formData.username, password: formData.password });
      } else {
        await authAPI.registerWithPhone({ phone: formData.phone, code: formData.code });
        // 手机号注册后需要设置密码或直接登录
        await login({ phone: formData.phone, code: formData.code });
      }
      navigate('/', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || '注册失败，请稍后重试');
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
      await authAPI.sendSms(formData.phone, 'register');
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
                      placeholder="请输入密码（至少6位）"
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
                      {showPassword ? <Eye size={18} /> : <Eye size={18} className="opacity-50" />}
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
