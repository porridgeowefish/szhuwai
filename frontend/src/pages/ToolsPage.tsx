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
  CheckCircle2,
  Wrench,
} from 'lucide-react';
import { cn } from '../utils/cn';

interface ToolInfo {
  name: string;
  description: string;
  extendedDescription: string;
  path: string;
  icon: React.ElementType;
  color: string;
  gradient: string;
  status: 'available' | 'maintenance';
}

const ToolsPage: React.FC = () => {
  const tools: ToolInfo[] = [
    {
      name: '轨迹分析',
      description: '上传 GPX/KML 文件，分析轨迹长度、爬升、难度等指标',
      extendedDescription: '支持 GPX 和 KML 格式，自动计算海拔变化、坡度分析、云海概率评估，并生成可视化的海拔剖面图',
      path: '/tools/track',
      icon: Route,
      color: 'bg-emerald-500',
      gradient: 'from-emerald-500 to-teal-600',
      status: 'available',
    },
    {
      name: '天气查询',
      description: '查询目的地实时天气和未来预报，为出行做好准备',
      extendedDescription: '提供 7 天天气预报、逐小时趋势、关键节点格点数据，含风寒指数与紫外线提醒',
      path: '/tools/weather',
      icon: Cloud,
      color: 'bg-blue-500',
      gradient: 'from-blue-500 to-cyan-600',
      status: 'available',
    },
    {
      name: '交通方案',
      description: '搜索目的地交通方式，提供多种出行方案对比',
      extendedDescription: '综合对比驾车、公交、步行方案，包含费用估算、耗时对比与推荐路线标记',
      path: '/tools/transport',
      icon: Navigation,
      color: 'bg-purple-500',
      gradient: 'from-purple-500 to-violet-600',
      status: 'available',
    },
    {
      name: '周边搜索',
      description: '搜索目的地周边的住宿、餐饮、景点等配套服务',
      extendedDescription: '基于高德地图 POI 数据，按分类搜索周边设施，含距离排序与评分信息',
      path: '/tools/search',
      icon: Search,
      color: 'bg-orange-500',
      gradient: 'from-orange-500 to-red-600',
      status: 'available',
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
          const isMaintenance = tool.status === 'maintenance';
          return (
            <Link
              key={tool.path}
              to={isMaintenance ? '#' : tool.path}
              onClick={isMaintenance ? (e) => e.preventDefault() : undefined}
              className={cn(
                'group relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm hover:shadow-xl transition-all duration-300 border border-zinc-100',
                isMaintenance
                  ? 'opacity-60 cursor-not-allowed'
                  : 'hover:border-[var(--forest)]/30'
              )}
            >
              {/* 背景装饰 */}
              <div className={cn(
                `absolute inset-0 bg-gradient-to-br ${tool.gradient} opacity-0 group-hover:opacity-5 transition-opacity`,
                isMaintenance && 'hidden'
              )} />

              {/* 维护中标签 */}
              {isMaintenance && (
                <div className="absolute top-4 right-4 px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-bold rounded-full flex items-center gap-1">
                  <Wrench size={12} />
                  维护中
                </div>
              )}

              {/* 内容 */}
              <div className="relative">
                {/* 图标 + 状态 */}
                <div className="flex items-center justify-between mb-4">
                  <div className={cn(
                    `inline-flex items-center justify-center w-12 h-12 rounded-xl ${tool.color} text-white group-hover:scale-110 transition-transform`,
                    isMaintenance && 'grayscale'
                  )}>
                    <Icon size={24} />
                  </div>
                  {tool.status === 'available' && (
                    <span className="flex items-center gap-1 text-[10px] text-[var(--forest)] bg-[var(--forest)]/10 px-2 py-0.5 rounded-full font-medium">
                      <CheckCircle2 size={10} />
                      可用
                    </span>
                  )}
                </div>

                {/* 标题和描述 */}
                <h3 className={cn(
                  'text-lg font-bold mb-2 transition-colors',
                  isMaintenance ? 'text-zinc-400' : 'text-zinc-900 group-hover:text-[var(--forest)]'
                )}>
                  {tool.name}
                </h3>
                <p className="text-sm text-zinc-600 mb-1">
                  {tool.description}
                </p>
                {/* hover 时显示更多描述（移动端始终可见） */}
                <p className={cn(
                  'text-xs text-zinc-400 leading-relaxed overflow-hidden transition-all duration-300',
                  'max-h-20 mt-2 lg:max-h-0 lg:group-hover:max-h-20 lg:group-hover:mt-2 lg:opacity-0 lg:group-hover:opacity-100'
                )}>
                  {tool.extendedDescription}
                </p>

                {/* 箭头指示 */}
                {!isMaintenance && (
                  <div className="flex items-center text-sm font-medium text-[var(--forest)] mt-3">
                    <span className="mr-2">开始使用</span>
                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                  </div>
                )}
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
