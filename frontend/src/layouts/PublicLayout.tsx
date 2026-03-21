import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Tent, User, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const PublicLayout: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[var(--sand)]">
      {/* 顶部栏 */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-[var(--stone)]">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[var(--forest)] flex items-center justify-center">
              <Tent size={18} className="text-white" />
            </div>
            <span className="text-lg font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
              户外出行智能策划
            </span>
          </Link>
          <nav className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/reports"
                  className="text-sm font-medium text-zinc-600 hover:text-[var(--forest)] transition-colors"
                >
                  报告中心
                </Link>
                {user?.role === 'admin' && (
                  <Link
                    to="/admin/users"
                    className="text-sm font-medium text-zinc-600 hover:text-[var(--forest)] transition-colors"
                  >
                    用户管理
                  </Link>
                )}
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-[var(--forest)] flex items-center justify-center text-white text-sm font-bold">
                    {user?.username?.charAt(0).toUpperCase()}
                  </div>
                  <Link
                    to="/profile"
                    className="text-sm font-medium text-zinc-600 hover:text-[var(--forest)] transition-colors"
                  >
                    {user?.username}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="text-sm font-medium text-red-600 hover:text-red-700 transition-colors flex items-center gap-1"
                  >
                    <LogOut size={14} />
                    退出
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link
                  to="/auth/login"
                  className="text-sm font-medium text-zinc-600 hover:text-[var(--forest)] transition-colors"
                >
                  登录
                </Link>
                <Link
                  to="/auth/register"
                  className="btn-forest px-4 py-2 rounded-lg text-white text-sm font-bold"
                >
                  注册
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="pt-16">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--stone)] py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-zinc-400">
            © 2026 户外出行智能策划系统. 由 AI 驱动，为户外爱好者提供智能规划服务。
          </p>
        </div>
      </footer>
    </div>
  );
};

export default PublicLayout;
