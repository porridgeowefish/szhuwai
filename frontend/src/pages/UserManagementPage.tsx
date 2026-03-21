import React, { useEffect, useState } from 'react';
import { Shield, Check, X, Search } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../lib/api/client';
import { cn } from '../utils/cn';

interface UserInfo {
  id: number;
  username: string;
  phone: string | null;
  role: 'user' | 'admin';
  status: 'active' | 'disabled';
  createdAt: string;
  lastLoginAt: string | null;
}

interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

const UserManagementPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [pagination, setPagination] = useState<Pagination>({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'disabled'>('all');

  const fetchUsers = async (page: number = 1) => {
    setLoading(true);
    try {
      const response: any = await apiClient.get<any>('/users', {
        params: { page, page_size: pagination.pageSize },
      });
      // 后端返回 { code, message, data: { list, pagination } }
      // 拦截器解包后返回 data，即 { list, pagination }
      setUsers(response.list || []);
      setPagination(response.pagination || { page: 1, pageSize: 20, total: 0, totalPages: 0 });
    } catch (error) {
      console.error('获取用户列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'disabled' : 'active';
    try {
      await apiClient.patch(`/users/${userId}/status`, { status: newStatus });
      // 刷新列表
      fetchUsers(pagination.page);
    } catch (error: any) {
      console.error('更新用户状态失败:', error);
      alert(error.response?.data?.message || '操作失败');
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // 过滤用户
  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.phone?.includes(searchTerm);
    const matchesStatus = statusFilter === 'all' || u.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (currentUser?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-[var(--sand)] flex items-center justify-center">
        <div className="text-center">
          <Shield size={48} className="mx-auto text-zinc-400 mb-4" />
          <h1 className="text-xl font-bold text-zinc-900">权限不足</h1>
          <p className="text-zinc-500 mt-2">仅管理员可访问此页面</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--sand)] py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
            <Shield size={24} className="text-[var(--forest)]" />
            用户管理
          </h1>
          <p className="text-zinc-500 mt-1">管理系统用户和权限</p>
        </div>

        {/* 搜索和过滤 */}
        <div className="glass rounded-xl p-4 mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="搜索用户名或手机号..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg input-nature"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-2 rounded-lg input-nature"
          >
            <option value="all">全部状态</option>
            <option value="active">正常</option>
            <option value="disabled">已禁用</option>
          </select>
        </div>

        {/* 用户列表 */}
        <div className="glass rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[var(--stone)]/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">用户</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">手机号</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">角色</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">状态</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">注册时间</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-700">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--stone)]">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                      加载中...
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                      暂无用户数据
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-[var(--sand)]/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[var(--forest)] flex items-center justify-center text-white text-sm font-bold">
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium text-zinc-900">{user.username}</div>
                            <div className="text-xs text-zinc-500">ID: {user.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-zinc-600">{user.phone || '未绑定'}</td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                            user.role === 'admin'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-zinc-100 text-zinc-700'
                          )}
                        >
                          {user.role === 'admin' ? '管理员' : '用户'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                            user.status === 'active'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          )}
                        >
                          {user.status === 'active' ? '正常' : '已禁用'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600">
                        {new Date(user.createdAt).toLocaleDateString('zh-CN')}
                      </td>
                      <td className="px-4 py-3">
                        {user.id !== currentUser?.id && (
                          <button
                            onClick={() => handleToggleStatus(user.id, user.status)}
                            className={cn(
                              'p-2 rounded-lg transition-colors',
                              user.status === 'active'
                                ? 'hover:bg-red-50 text-red-600'
                                : 'hover:bg-green-50 text-green-600'
                            )}
                            title={user.status === 'active' ? '禁用用户' : '启用用户'}
                          >
                            {user.status === 'active' ? <X size={16} /> : <Check size={16} />}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {pagination.totalPages > 1 && (
            <div className="px-4 py-3 border-t border-[var(--stone)] flex items-center justify-between">
              <div className="text-sm text-zinc-500">
                共 {pagination.total} 个用户，第 {pagination.page} / {pagination.totalPages} 页
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => fetchUsers(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="px-3 py-1 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-[var(--stone)] text-zinc-700 hover:bg-[var(--stone)]/70"
                >
                  上一页
                </button>
                <button
                  onClick={() => fetchUsers(pagination.page + 1)}
                  disabled={pagination.page === pagination.totalPages}
                  className="px-3 py-1 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-[var(--forest)] text-white hover:bg-[var(--forest)]/80"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagementPage;
