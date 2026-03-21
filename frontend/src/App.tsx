import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { QuotaProvider } from './contexts/QuotaContext';
import PublicLayout from './layouts/PublicLayout';
import ProtectedLayout from './layouts/ProtectedLayout';
import ProtectedRoute from './components/common/ProtectedRoute';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ReportDetailPage from './pages/ReportDetailPage';

// Lazy load pages
const ReportListPage = React.lazy(() => import('./pages/ReportListPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const ChangePasswordPage = React.lazy(() => import('./pages/ChangePasswordPage'));
const TrackAnalysisPage = React.lazy(() => import('./pages/TrackAnalysisPage'));
const WeatherQueryPage = React.lazy(() => import('./pages/WeatherQueryPage'));
const TransportPage = React.lazy(() => import('./pages/TransportPage'));
const SearchPage = React.lazy(() => import('./pages/SearchPage'));

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <QuotaProvider>
          <React.Suspense fallback={<div className="min-h-screen bg-[var(--sand)] flex items-center justify-center">加载中...</div>}>
            <Routes>
              {/* 公开路由 */}
              <Route element={<PublicLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/auth/login" element={<LoginPage />} />
                <Route path="/auth/register" element={<RegisterPage />} />
              </Route>

              {/* 需认证路由 */}
              <Route
                element={
                  <ProtectedRoute>
                    <ProtectedLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/reports" element={<ReportListPage />} />
                <Route path="/reports/:id" element={<ReportDetailPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/profile/password" element={<ChangePasswordPage />} />
                <Route path="/tools/track" element={<TrackAnalysisPage />} />
                <Route path="/tools/weather" element={<WeatherQueryPage />} />
                <Route path="/tools/transport" element={<TransportPage />} />
                <Route path="/tools/search" element={<SearchPage />} />
              </Route>

              {/* 404 重定向 */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </React.Suspense>
        </QuotaProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
