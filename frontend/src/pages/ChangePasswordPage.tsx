import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Shield, Check } from 'lucide-react';
import { authAPI } from '../lib/api/auth';
import { cn } from '../utils/cn';

const ChangePasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (formData.new_password.length < 6) {
      setError('新密码长度至少6位');
      setLoading(false);
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError('两次输入的新密码不一致');
      setLoading(false);
      return;
    }

    try {
      await authAPI.changePassword({
        old_password: formData.old_password,
        new_password: formData.new_password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/profile'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || '修改密码失败');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-16">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <Check size={32} className="text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-zinc-900 mb-2">密码修改成功</h2>
        <p className="text-sm text-zinc-500">正在跳转...</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          修改密码
        </h1>
        <p className="text-sm text-zinc-500 mt-1">为了账户安全，请定期更换密码</p>
      </div>

      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">当前密码</label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.old_password}
                onChange={(e) => setFormData({ ...formData, old_password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="请输入当前密码"
                disabled={loading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">新密码</label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.new_password}
                onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="请输入新密码（至少6位）"
                disabled={loading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">确认新密码</label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.confirm_password}
                onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 rounded-xl input-nature"
                placeholder="请再次输入新密码"
                disabled={loading}
              />
              {formData.confirm_password && formData.new_password === formData.confirm_password && (
                <Check size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500" />
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={cn(
              'w-full py-3 rounded-xl text-white font-bold btn-forest',
              loading && 'opacity-70 cursor-not-allowed'
            )}
          >
            {loading ? '提交中...' : '确认修改'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordPage;
