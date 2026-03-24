import React from 'react';
import { Link } from 'react-router-dom';
import { User, Phone, Lock, MapPin, Calendar, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useQuota } from '../contexts/QuotaContext';
import { cn } from '../utils/cn';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const { quota, getTimeUntilReset } = useQuota();
  const isAdmin = user.role === 'admin';
  const isQuotaExhausted = quota && quota.remaining === 0;

  const handleLogout = () => {
    logout();
    window.location.href = '/auth/login';
  };

  if (!user) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          个人中心
        </h1>
      </div>

      {/* 用户信息卡片 */}
      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-2xl bg-[var(--forest)] flex items-center justify-center text-white text-2xl font-bold">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-zinc-900">{user.username}</h2>
            <div className="flex items-center gap-4 mt-2 text-sm text-zinc-500">
              <span className="flex items-center gap-1">
                <Phone size={14} />
                {user.phone || '未绑定手机'}
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={14} />
                {new Date(user.createdAt).toLocaleDateString('zh-CN')} 加入
              </span>
            </div>
          </div>
          <span className={cn(
            'px-3 py-1 rounded-full text-sm font-medium',
            user.role === 'admin' ? 'bg-purple-50 text-purple-700' : 'bg-zinc-100 text-zinc-600'
          )}>
            {user.role === 'admin' ? '管理员' : '用户'}
          </span>
        </div>
      </div>

      {/* 额度显示 */}
      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <h3 className="font-bold text-zinc-900 mb-4 flex items-center gap-2">
          <Shield size={18} className="text-[var(--forest)]" />
          今日额度
        </h3>

        {isAdmin ? (
          <div className="flex items-center justify-center py-4">
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600">∞</div>
              <div className="text-sm text-zinc-500 mt-1">管理员无限额度</div>
            </div>
          </div>
        ) : quota && (
          <>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-zinc-500">已使用</span>
                  <span className={cn(
                    "font-medium",
                    isQuotaExhausted ? "text-red-600" : "text-zinc-900"
                  )}>
                    {quota.used}/{quota.total} 次
                  </span>
                </div>
                <div className="h-3 bg-[var(--sand)] rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full transition-all",
                      isQuotaExhausted ? "bg-red-500" : "bg-[var(--forest)]"
                    )}
                    style={{ width: `${(quota.used / quota.total) * 100}%` }}
                  />
                </div>
              </div>
              <div className="text-right">
                <div className={cn(
                  "text-2xl font-bold",
                  isQuotaExhausted ? "text-red-600" : "text-[var(--forest)]"
                )}>
                  {quota.remaining}
                </div>
                <div className="text-xs text-zinc-500">剩余次数</div>
              </div>
            </div>
            <p className={cn(
              "text-xs mt-3",
              isQuotaExhausted ? "text-red-500" : "text-zinc-400"
            )}>
              {isQuotaExhausted
                ? `额度已用完，${getTimeUntilReset()}`
                : `${getTimeUntilReset()}`
              }
            </p>
          </>
        )}
      </div>

      {/* 快捷操作 */}
      <div className="bg-white border border-[var(--stone)] rounded-2xl divide-y divide-[var(--stone)]">
        <Link
          to="/profile/password"
          className="flex items-center justify-between p-4 hover:bg-[var(--sand)] transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[var(--sand)] rounded-lg">
              <Lock size={18} className="text-zinc-600" />
            </div>
            <span className="font-medium text-zinc-900">修改密码</span>
          </div>
          <span className="text-zinc-400">→</span>
        </Link>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-between p-4 hover:bg-red-50 transition-colors text-left"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-50 rounded-lg">
              <Shield size={18} className="text-red-600" />
            </div>
            <span className="font-medium text-red-600">退出登录</span>
          </div>
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;
