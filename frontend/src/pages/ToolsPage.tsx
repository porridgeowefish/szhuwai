import React from 'react';
import { Link } from 'react-router-dom';
import {
  Route,
  Cloud,
  Navigation,
  Search,
  ArrowRight,
  Mountain,
  Compass,
} from 'lucide-react';

const ToolsPage: React.FC = () => {
  const tools = [
    {
      name: '轨迹分析',
      description: '上传 GPX/KML 文件，分析轨迹长度、爬升、难度等指标',
      path: '/tools/track',
      icon: Route,
      color: 'bg-emerald-500',
      gradient: 'from-emerald-500 to-teal-600',
    },
    {
      name: '天气查询',
      description: '查询目的地实时天气和未来预报，为出行做好准备',
      path: '/tools/weather',
      icon: Cloud,
      color: 'bg-blue-500',
      gradient: 'from-blue-500 to-cyan-600',
    },
    {
      name: '交通方案',
      description: '搜索目的地交通方式，提供多种出行方案对比',
      path: '/tools/transport',
      icon: Navigation,
      color: 'bg-purple-500',
      gradient: 'from-purple-500 to-violet-600',
    },
    {
      name: '周边搜索',
      description: '搜索目的地周边的住宿、餐饮、景点等配套服务',
      path: '/tools/search',
      icon: Search,
      color: 'bg-orange-500',
      gradient: 'from-orange-500 to-red-600',
    },
  ];

  return (
    <div className="space-y-8">
      {/* 标题区 */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--forest)] to-[var(--forest-dark)] text-white mb-4 shadow-lg">
          <Compass size={32} />
        </div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          户外工具箱
        </h1>
        <p className="text-zinc-600 max-w-2xl mx-auto">
          为户外出行精心设计的实用工具集合，帮助您更好地规划每一次旅程
        </p>
      </div>

      {/* 工具卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <Link
              key={tool.path}
              to={tool.path}
              className="group relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm hover:shadow-xl transition-all duration-300 border border-zinc-100 hover:border-[var(--forest)]/30"
            >
              {/* 背景装饰 */}
              <div className={`absolute inset-0 bg-gradient-to-br ${tool.gradient} opacity-0 group-hover:opacity-5 transition-opacity`} />

              {/* 内容 */}
              <div className="relative">
                {/* 图标 */}
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${tool.color} text-white mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon size={24} />
                </div>

                {/* 标题和描述 */}
                <h3 className="text-lg font-bold text-zinc-900 mb-2 group-hover:text-[var(--forest)] transition-colors">
                  {tool.name}
                </h3>
                <p className="text-sm text-zinc-600 mb-4">
                  {tool.description}
                </p>

                {/* 箭头指示 */}
                <div className="flex items-center text-sm font-medium text-[var(--forest)]">
                  <span className="mr-2">开始使用</span>
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* 底部提示 */}
      <div className="glass rounded-2xl p-6 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Mountain size={20} className="text-[var(--forest)]" />
          <span className="font-semibold text-zinc-900">提示</span>
        </div>
        <p className="text-sm text-zinc-600">
          所有工具均可独立使用。如需生成完整的出行策划书，请前往
          <Link to="/" className="text-[var(--forest)] font-medium mx-1 hover:underline">
            首页
          </Link>
          上传轨迹文件。
        </p>
      </div>
    </div>
  );
};

export default ToolsPage;
