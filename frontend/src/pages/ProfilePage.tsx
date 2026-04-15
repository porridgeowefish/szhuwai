import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Phone, Lock, Calendar, Shield, LogOut, Clock, Smartphone, SmartphoneNfc,
  CheckCircle2, XCircle, Loader2, Zap
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useQuota } from '../contexts/QuotaContext';
import { cn } from '../utils/cn';
import { getTimeUntilReset } from '../utils/time';
import { authAPI } from '../lib/api/auth';

const PHONE_REGEX = /^1[3-9]\d{9}$/;

/** 手机号脱敏：中间4位替换为 **** */
function maskPhone(phone: string | undefined | null): string {
  if (!phone) return '未绑定';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length >= 7) {
    return cleaned.slice(0, 3) + '****' + cleaned.slice(-4);
  }
  return phone;
}

/** 格式化登录时间 */
function formatLastLogin(dateStr: string | undefined | null): string {
  if (!dateStr) return '暂无记录';
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return '刚刚';
    if (diffMin < 60) return `${diffMin} 分钟前`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour} 小时前`;
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '暂无记录';
  }
}

const ProfilePage: React.FC = () => {
  const { user, logout, updateUser } = useAuth();
  const { quota } = useQuota();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';
  const isQuotaExhausted = quota && quota.remaining === 0;
  const hasPhone = !!user?.phone;

  // 手机绑定/解绑状态
  const [bindModal, setBindModal] = useState<'idle' | 'bind' | 'unbind'>('idle');
  const [phoneInput, setPhoneInput] = useState('');
  const [codeInput, setCodeInput] = useState('');
  const [smsCooldown, setSmsCooldown] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [bindError, setBindError] = useState('');
  const [phoneError, setPhoneError] = useState('');
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 组件卸载时清理计时器
  useEffect(() => {
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  // 发送验证码
  const handleSendCode = async () => {
    try {
      if (bindModal === 'bind') {
        if (!phoneInput) return;
        if (!PHONE_REGEX.test(phoneInput)) {
          setPhoneError('请输入正确的手机号');
          return;
        }
        setPhoneError('');
        await authAPI.sendSms(phoneInput, 'bind');
      } else {
        if (!user?.phone) return;
        await authAPI.sendSms(user.phone, 'unbind');
      }
      setSmsCooldown(60);
      if (countdownRef.current) clearInterval(countdownRef.current);
      countdownRef.current = setInterval(() => {
        setSmsCooldown(prev => {
          if (prev <= 1) {
            if (countdownRef.current) clearInterval(countdownRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch {
      setBindError('验证码发送失败');
    }
  };

  // 绑定/解绑提交
  const handleSubmitBindAction = async () => {
    setSubmitting(true);
    setBindError('');
    try {
      if (bindModal === 'bind') {
        await authAPI.bindPhone({ phone: phoneInput, code: codeInput });
      } else {
        await authAPI.unbindPhone({ code: codeInput });
      }
      await updateUser();
      setBindModal('idle');
      setPhoneInput('');
      setCodeInput('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      setBindError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) return null;

  const usedPercent = quota ? (quota.used / quota.total) * 100 : 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          个人中心
        </h1>
      </div>

      {/* 用户信息卡片 */}
      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-2xl bg-[var(--forest)] flex items-center justify-center text-white text-2xl font-bold">
            {(user.username || user.phone || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-zinc-900">{user.username || user.phone || '用户'}</h2>
            <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-zinc-500">
              <span className="flex items-center gap-1">
                <Phone size={14} />
                {maskPhone(user.phone)}
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={14} />
                {new Date(user.createdAt).toLocaleDateString('zh-CN')} 加入
              </span>
              <span className="flex items-center gap-1">
                <Clock size={14} />
                上次登录: {formatLastLogin(user.lastLoginAt)}
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

      {/* 额度卡片 */}
      <div className={cn(
        'bg-white border rounded-2xl p-6 transition-colors',
        isQuotaExhausted ? 'border-red-200 bg-red-50/30' : 'border-[var(--stone)]'
      )}>
        <h3 className="font-bold text-zinc-900 mb-4 flex items-center gap-2">
          <Zap size={18} className={isQuotaExhausted ? 'text-red-500' : 'text-[var(--forest)]'} />
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
          <div className="space-y-4">
            {/* 可视化额度卡片 */}
            <div className={cn(
              'rounded-xl p-4 flex items-center justify-between',
              isQuotaExhausted
                ? 'bg-red-50 border border-red-200'
                : 'bg-[var(--forest)]/5 border border-[var(--forest)]/20'
            )}>
              <div className="flex items-center gap-4">
                <div className={cn(
                  'w-14 h-14 rounded-xl flex items-center justify-center',
                  isQuotaExhausted ? 'bg-red-500' : 'bg-[var(--forest)]'
                )}>
                  {isQuotaExhausted
                    ? <XCircle size={28} className="text-white" />
                    : <CheckCircle2 size={28} className="text-white" />
                  }
                </div>
                <div>
                  <div className={cn(
                    'text-2xl font-bold',
                    isQuotaExhausted ? 'text-red-600' : 'text-[var(--forest)]'
                  )}>
                    {quota.remaining} <span className="text-sm font-normal text-zinc-500">次剩余</span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {isQuotaExhausted
                      ? `额度已用完，${getTimeUntilReset()}`
                      : `今日可用 ${quota.total} 次，${getTimeUntilReset()}`
                    }
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-zinc-500">已使用</div>
                <div className="text-lg font-bold text-zinc-900">{quota.used}<span className="text-xs font-normal text-zinc-400">/{quota.total}</span></div>
              </div>
            </div>

            {/* 进度条 */}
            <div className="h-2 bg-[var(--sand)] rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  isQuotaExhausted ? "bg-red-500" : usedPercent > 90 ? "bg-amber-500" : "bg-[var(--forest)]"
                )}
                style={{ width: `${Math.min(usedPercent, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 手机绑定操作 */}
      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <h3 className="font-bold text-zinc-900 mb-4 flex items-center gap-2">
          <Smartphone size={18} className="text-[var(--forest)]" />
          手机绑定
        </h3>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center',
              hasPhone ? 'bg-[var(--forest)]/10 text-[var(--forest)]' : 'bg-zinc-100 text-zinc-400'
            )}>
              {hasPhone ? <SmartphoneNfc size={20} /> : <Phone size={20} />}
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">
                {hasPhone ? maskPhone(user.phone) : '未绑定手机号'}
              </p>
              <p className="text-xs text-zinc-400">
                {hasPhone ? '已绑定，可接收安全通知' : '绑定后可使用手机号登录'}
              </p>
            </div>
          </div>
          {hasPhone ? (
            <button
              onClick={() => { setBindModal('unbind'); setBindError(''); }}
              className="px-4 py-2 rounded-xl text-sm font-medium border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
            >
              解绑手机
            </button>
          ) : (
            <button
              onClick={() => { setBindModal('bind'); setBindError(''); }}
              className="px-4 py-2 rounded-xl text-sm font-medium bg-[var(--forest)] text-white hover:bg-[var(--forest)]/90 transition-colors"
            >
              绑定手机
            </button>
          )}
        </div>

        {/* 绑定/解绑弹窗 */}
        {bindModal !== 'idle' && (
          <div className="mt-4 p-4 bg-[var(--sand)] rounded-xl border border-[var(--stone)] space-y-3">
            <h4 className="text-sm font-bold text-zinc-900">
              {bindModal === 'bind' ? '绑定手机号' : '解绑手机号'}
            </h4>
            {bindModal === 'bind' && (
              <>
                <input
                  type="tel"
                  value={phoneInput}
                  onChange={(e) => { setPhoneInput(e.target.value.replace(/\D/g, '').slice(0, 11)); setPhoneError(''); }}
                  placeholder="请输入手机号"
                  className="w-full px-4 py-2 rounded-xl input-nature text-sm"
                />
                {phoneError && <p className="text-xs text-red-500">{phoneError}</p>}
              </>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                placeholder="验证码"
                maxLength={6}
                className="flex-1 px-4 py-2 rounded-xl input-nature text-sm"
              />
              <button
                onClick={handleSendCode}
                disabled={smsCooldown > 0 || (bindModal === 'bind' && !phoneInput)}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors',
                  smsCooldown > 0 || (bindModal === 'bind' && !phoneInput)
                    ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
                    : 'bg-[var(--forest)] text-white hover:bg-[var(--forest)]/90'
                )}
              >
                {smsCooldown > 0 ? `${smsCooldown}s` : '获取验证码'}
              </button>
            </div>
            {bindError && (
              <p className="text-xs text-red-500">{bindError}</p>
            )}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setBindModal('idle'); setPhoneInput(''); setCodeInput(''); setBindError(''); }}
                className="px-4 py-2 rounded-xl text-sm text-zinc-500 hover:bg-zinc-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSubmitBindAction}
                disabled={submitting || !codeInput || (bindModal === 'bind' && !phoneInput)}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium text-white transition-colors',
                  submitting || !codeInput || (bindModal === 'bind' && !phoneInput)
                    ? 'bg-zinc-300 cursor-not-allowed'
                    : 'bg-[var(--forest)] hover:bg-[var(--forest)]/90'
                )}
              >
                {submitting ? <Loader2 size={16} className="animate-spin" /> : '确认'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 操作列表 */}
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
              <LogOut size={18} className="text-red-600" />
            </div>
            <span className="font-medium text-red-600">退出登录</span>
          </div>
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;
