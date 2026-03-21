import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Trash2, Calendar, Search, Filter } from 'lucide-react';
import { reportsAPI } from '../lib/api/reports';
import { ReportDocument } from '../lib/api/types';
import { cn } from '../utils/cn';

const ReportListPage: React.FC = () => {
  const [reports, setReports] = useState<ReportDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchReports();
  }, [page]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await reportsAPI.list({ page, page_size: 20 }) as any;
      setReports(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('获取报告列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这份报告吗？')) return;
    try {
      await reportsAPI.delete(reportId);
      setReports(reports.filter(r => r.id !== reportId));
      setTotal(total - 1);
    } catch (err) {
      console.error('删除报告失败:', err);
    }
  };

  const filteredReports = reports.filter(r =>
    r.plan_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            我的报告
          </h1>
          <p className="text-sm text-zinc-500 mt-1">共 {total} 份报告</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索报告..."
              className="pl-10 pr-4 py-2 rounded-xl input-nature w-64"
            />
          </div>
        </div>
      </div>

      {/* 报告列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-[var(--stone)] border-t-[var(--forest)] rounded-full animate-spin" />
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed border-[var(--stone)] rounded-2xl">
          <FileText size={48} className="mx-auto text-zinc-300 mb-4" />
          <p className="text-zinc-500 font-medium">还没有报告</p>
          <p className="text-sm text-zinc-400 mt-1">去首页生成您的第一份计划吧</p>
          <Link
            to="/"
            className="inline-block mt-4 px-6 py-2 btn-forest rounded-xl text-white font-bold"
          >
            开始规划
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="bg-white border border-[var(--stone)] rounded-2xl p-6 card-hover"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-zinc-900 line-clamp-2">{report.plan_name}</h3>
                  <div className="flex items-center gap-2 mt-2 text-xs text-zinc-500">
                    <Calendar size={14} />
                    <span>{new Date(report.trip_date).toLocaleDateString('zh-CN')}</span>
                  </div>
                </div>
                <span className={cn(
                  'px-2 py-1 rounded-full text-xs font-medium',
                  report.overall_rating === '推荐'
                    ? 'bg-green-50 text-green-700'
                    : report.overall_rating === '谨慎推荐'
                    ? 'bg-amber-50 text-amber-700'
                    : 'bg-red-50 text-red-700'
                )}>
                  {report.overall_rating}
                </span>
              </div>
              <div className="flex items-center justify-between pt-4 border-t border-[var(--stone)]">
                <span className="text-xs text-zinc-400">
                  {new Date(report.created_at).toLocaleString('zh-CN')}
                </span>
                <div className="flex items-center gap-2">
                  <Link
                    to={`/reports/${report.id}`}
                    className="text-xs font-medium text-[var(--forest)] hover:underline"
                  >
                    查看详情
                  </Link>
                  <button
                    onClick={() => handleDelete(report.id)}
                    className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > 20 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded-lg bg-white border border-[var(--stone)] disabled:opacity-50"
          >
            上一页
          </button>
          <span className="px-4 py-2 text-sm text-zinc-600">
            第 {page} 页
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page * 20 >= total}
            className="px-4 py-2 rounded-lg bg-white border border-[var(--stone)] disabled:opacity-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default ReportListPage;
