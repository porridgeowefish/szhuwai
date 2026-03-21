import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Tent, Home, FileText, Wrench, User, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useQuota } from '../contexts/QuotaContext';
import { cn } from '../utils/cn';

const ProtectedLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const { quota } = useQuota();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navigation = [
    { name: '首页', href: '/', icon: Home },
    { name: '报告中心', href: '/reports', icon: FileText },
    { name: '工具', href: '/tools', icon: Wrench },
    { name: '个人中心', href: '/profile', icon: User },
  ];

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  return (
    <div className="min-h-screen bg-[var(--sand)]">
      {/* 顶部导航栏 */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-[var(--stone)]">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo + 导航 */}
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[var(--forest)] flex items-center justify-center">
                  <Tent size={18} className="text-white" />
                </div>
                <span className="text-lg font-bold hidden sm:block" style={{ fontFamily: 'Playfair Display, serif' }}>
                  户外出行智能策划
                </span>
              </Link>

              {/* 桌面导航 */}
              <nav className="hidden lg:flex items-center gap-6">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href !== '/' && location.pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={cn(
                        'flex items-center gap-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'text-[var(--forest)]'
                          : 'text-zinc-600 hover:text-[var(--forest)]'
                      )}
                    >
                      <item.icon size={16} />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* 右侧：额度 + 用户菜单 */}
            <div className="flex items-center gap-4">
              {/* 额度显示 */}
              {quota && (
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[var(--forest)]/10 rounded-lg">
                  <span className="text-xs text-zinc-500">今日额度</span>
                  <span className="text-sm font-bold text-[var(--forest)]">
                    {quota.remaining}/{quota.total}
                  </span>
                </div>
              )}

              {/* 用户信息 */}
              <div className="flex items-center gap-3">
                <div className="hidden sm:block text-right">
                  <div className="text-sm font-medium text-zinc-900">{user?.username}</div>
                  <div className="text-xs text-zinc-500">{user?.phone || '未绑定手机'}</div>
                </div>
                <div className="w-9 h-9 rounded-full bg-[var(--forest)] flex items-center justify-center text-white font-bold">
                  {user?.username?.charAt(0).toUpperCase()}
                </div>
              </div>

              {/* 移动端菜单按钮 */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 hover:bg-[var(--sand)] rounded-lg"
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>

          {/* 移动端导航 */}
          {mobileMenuOpen && (
            <nav className="lg:hidden py-4 border-t border-[var(--stone)] mt-4">
              <div className="space-y-2">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href !== '/' && location.pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-[var(--forest)]/10 text-[var(--forest)]'
                          : 'text-zinc-600 hover:bg-[var(--sand)]'
                      )}
                    >
                      <item.icon size={18} />
                      {item.name}
                    </Link>
                  );
                })}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut size={18} />
                  退出登录
                </button>
              </div>
            </nav>
          )}
        </div>
      </header>

      {/* 主内容区 */}
      <main className="pt-20 pb-12">
        <div className="max-w-7xl mx-auto px-4">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--stone)] py-8">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-zinc-400">
            © 2026 户外出行智能策划系统. 由 AI 驱动，为户外爱好者提供智能规划服务。
          </p>
        </div>
      </footer>
    </div>
  );
};

export default ProtectedLayout;
