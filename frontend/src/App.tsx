import React, { lazy, Suspense, type ReactNode } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Activity, Map, Settings } from 'lucide-react';
import HomePage from './pages/HomePage';
import AISettingsPage from './pages/AISettingsPage';
const ReportDetailPage = lazy(() => import('./pages/ReportDetailPage'));
const MonitorPage = lazy(() => import('./pages/MonitorPage'));

class ErrorBoundary extends React.Component<{ children: ReactNode }, { hasError: boolean; message: string }> {
  declare props: { children: ReactNode };
  declare setState: (state: { hasError: boolean; message: string }) => void;

  state = { hasError: false, message: '' };

  static getDerivedStateFromError(error: unknown) {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : '页面渲染异常',
    };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="mx-auto flex min-h-[70vh] max-w-xl items-center justify-center px-4">
          <section className="rounded-2xl border border-red-200 bg-white p-6 text-center">
            <h1 className="text-xl font-bold text-[var(--danger)]">页面渲染失败</h1>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{this.state.message}</p>
            <button type="button" className="primary-button mt-5" onClick={() => this.setState({ hasError: false, message: '' })}>
              重新渲染
            </button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

function Shell() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--text)]">
      <header className="border-b border-[var(--border)] bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)] text-white">
              <Map size={19} />
            </span>
            户外策划
          </Link>
          <nav aria-label="主导航" className="flex items-center gap-1 text-sm">
            <Link
              to="/"
              className={location.pathname === '/' ? 'nav-link nav-link-active' : 'nav-link'}
            >
              开始策划
            </Link>
            <Link
              to="/settings"
              className={location.pathname === '/settings' ? 'nav-link nav-link-active' : 'nav-link'}
            >
              <Settings size={16} />
              API 指南
            </Link>
            <Link
              to="/moniter"
              className={location.pathname === '/moniter' || location.pathname === '/monitor' ? 'nav-link nav-link-active' : 'nav-link'}
            >
              <Activity size={16} />
              监控
            </Link>
          </nav>
        </div>
      </header>
      <ErrorBoundary>
        <Suspense fallback={<div className="flex min-h-[60vh] items-center justify-center text-sm text-[var(--muted)]">正在加载…</div>}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/settings" element={<AISettingsPage />} />
            <Route path="/moniter" element={<MonitorPage />} />
            <Route path="/monitor" element={<Navigate to="/moniter" replace />} />
            <Route path="/result" element={<ReportDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
