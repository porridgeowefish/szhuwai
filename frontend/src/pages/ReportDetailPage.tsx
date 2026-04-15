import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  ShieldAlert, CloudSun, MapPin, Backpack, Navigation, PhoneCall, Clock,
  Thermometer, Wind, Droplets, Sun, Eye, AlertTriangle, CheckCircle2, Info,
  Mountain, ArrowUp, ArrowDown, Cloud, Timer, Gauge, Trees, Landmark,
  Snowflake, Download, Tent, Map as MapIcon, List, FileText
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { PlanData, SafetyIssue, EquipmentItem, TransitRoute } from '../types';
import { calculateWindChill, windScaleToSpeed, getWindChillRisk } from '../utils/weather';
import { exportToPDF } from '../utils/pdf';
import { cn } from '../utils/cn';
import { reportsAPI } from '../lib/api/reports';
import EmptyState from '../components/common/EmptyState';
import { RouteBrief } from '../components/RouteBrief';
import { TrackDetailSection } from '../components/TrackDetailSection';

// 格式化日期时间
function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

const SectionTitle = ({ title, icon: Icon, colorClass = 'text-zinc-900' }: {
  title: string;
  icon: React.ElementType;
  colorClass?: string;
}) => (
  <div className="flex items-center gap-3 mb-6 relative pl-5 section-title-decoration">
    <div className={cn('p-2 rounded-lg bg-[var(--sand)]', colorClass)}>
      <Icon size={20} />
    </div>
    <h2 className="text-xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
      {title}
    </h2>
  </div>
);

const Card = ({ children, className, ...props }: {
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('bg-white border border-[var(--stone)] rounded-2xl p-6 shadow-sm card-hover', className)} {...props}>
    {children}
  </div>
);

const Badge = ({ children, variant = 'default' }: {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
}) => {
  const variants = {
    default: 'bg-zinc-100 text-zinc-600',
    success: 'bg-[var(--forest)]/10 text-[var(--forest)] border-[var(--forest)]/20',
    warning: 'bg-amber-50 text-amber-700 border-amber-100',
    error: 'bg-rose-50 text-rose-700 border-rose-100'
  };
  return (
    <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium border', variants[variant])}>
      {children}
    </span>
  );
};

// 目录导航项配置
interface TocItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

const ReportDetailPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [activeSection, setActiveSection] = useState<string>('');

  // 从路由 state 获取计划数据，或从 API 获取
  const statePlan = location.state?.plan as PlanData | null;
  const [plan, setPlan] = useState<PlanData | null>(statePlan);
  const [loading, setLoading] = useState(!statePlan);
  const [weatherTab, setWeatherTab] = useState<'overview' | 'hourly'>('overview');

  // 当没有 route state 时，从 API 获取报告数据
  useEffect(() => {
    if (!statePlan && id) {
      setLoading(true);
      reportsAPI.get(id)
        .then((data) => {
          setPlan(data as unknown as PlanData);
        })
        .catch((err) => {
          console.error('获取报告失败:', err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [id, statePlan]);

  // 根据实际内容动态生成目录项
  const tocItems = useMemo<TocItem[]>(() => {
    if (!plan) return [];
    const items: TocItem[] = [
      { id: 'section-route-brief', label: '线路简介', icon: Navigation },
      { id: 'section-scenic', label: '沿途风光', icon: MapIcon },
    ];
    if (plan.trackDetail) {
      items.push({ id: 'section-track-detail', label: '线路详情', icon: Mountain });
    }
    if (plan.transportScheme) {
      items.push({ id: 'section-transport', label: '交通方案', icon: MapPin });
    }
    items.push(
      { id: 'section-safety', label: '安全评估', icon: ShieldAlert },
      { id: 'section-weather', label: '天气预报', icon: CloudSun },
      { id: 'section-equipment', label: '装备清单', icon: Backpack },
    );
    return items;
  }, [plan]);

  // IntersectionObserver 实现 scroll spy
  useEffect(() => {
    if (!plan || tocItems.length === 0) return;

    const observers: IntersectionObserver[] = [];
    const visibleSections = new Set<string>();

    tocItems.forEach((item) => {
      const el = document.getElementById(item.id);
      if (!el) return;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              visibleSections.add(item.id);
            } else {
              visibleSections.delete(item.id);
            }
          });
          // 选择最靠近顶部的可见 section
          if (visibleSections.size > 0) {
            let topId = item.id;
            let topY = Infinity;
            visibleSections.forEach((sid) => {
              const sel = document.getElementById(sid);
              if (sel) {
                const rect = sel.getBoundingClientRect();
                if (rect.top < topY) {
                  topY = rect.top;
                  topId = sid;
                }
              }
            });
            setActiveSection(topId);
          }
        },
        { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
      );
      observer.observe(el);
      observers.push(observer);
    });

    return () => observers.forEach((o) => o.disconnect());
  }, [plan, tocItems]);

  // 平滑滚动到指定 section
  const scrollToSection = useCallback((sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--sand)] flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-[var(--stone)] border-t-[var(--forest)] rounded-full animate-spin" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-[var(--sand)] flex items-center justify-center">
        <EmptyState
          icon={FileText}
          title="报告不存在"
          description="该报告可能已被删除或链接无效"
          action={{ label: '返回首页', onClick: () => navigate('/') }}
          className="border-none py-0"
        />
      </div>
    );
  }

  const getRatingVariant = (rating: string) => {
    if (rating === '推荐') return 'success';
    if (rating === '谨慎推荐') return 'warning';
    return 'error';
  };

  return (
    <div className="min-h-screen bg-[var(--sand)] text-zinc-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-[var(--stone)] sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                {plan.planName}
              </h1>
              <Badge variant={getRatingVariant(plan.overallRating)}>{plan.overallRating}</Badge>
            </div>
            <div className="flex items-center gap-4 text-xs text-zinc-500 font-mono">
              <span className="flex items-center gap-1"><Clock size={12} /> {formatDateTime(plan.createdAt)}</span>
              <span className="flex items-center gap-1">ID: {plan.planId}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                if (mainContentRef.current && plan) {
                  try {
                    await exportToPDF(mainContentRef.current, plan.planName);
                  } catch (err) {
                    console.error('PDF导出错误:', err);
                    alert('PDF导出失败');
                  }
                }
              }}
              className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-sm font-bold hover:bg-zinc-800 transition-colors flex items-center gap-2"
            >
              <Download size={16} /> 导出策划书
            </button>
          </div>
        </div>
      </header>

      {/* 移动端横向目录 */}
      <div className="lg:hidden sticky top-[73px] z-40 bg-white/95 backdrop-blur-sm border-b border-[var(--stone)]">
        <div className="max-w-5xl mx-auto px-4 py-2 flex gap-1 overflow-x-auto scrollbar-none">
          {tocItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors shrink-0',
                  activeSection === item.id
                    ? 'bg-[var(--forest)]/10 text-[var(--forest)]'
                    : 'text-zinc-500 hover:text-zinc-700 hover:bg-zinc-100'
                )}
              >
                <Icon size={12} />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 flex gap-8">
        {/* 桌面端侧边目录 */}
        <aside className="hidden lg:block w-48 shrink-0">
          <nav className="sticky top-24 space-y-1">
            <div className="flex items-center gap-2 px-3 py-2 text-xs font-bold text-zinc-400 uppercase tracking-widest">
              <List size={14} />
              目录
            </div>
            {tocItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-all text-left',
                    activeSection === item.id
                      ? 'bg-[var(--forest)]/10 text-[var(--forest)] font-medium border-l-2 border-[var(--forest)]'
                      : 'text-zinc-500 hover:text-zinc-700 hover:bg-white border-l-2 border-transparent'
                  )}
                >
                  <Icon size={14} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* 主内容 */}
        <main className="flex-1 min-w-0 space-y-8">
          <div ref={mainContentRef} className="pdf-export-container space-y-8">
          {/* 1. 线路简介 */}
          <section id="section-route-brief">
            <RouteBrief
              planName={plan.planName}
              trackDetail={plan.trackDetail}
              overallRating={plan.overallRating}
            />
          </section>

          {/* 2. 线路详情 */}
          {plan.trackDetail && (
            <section id="section-track-detail">
              <SectionTitle title="线路详情" icon={Mountain} colorClass="text-[var(--forest)]" />
              <TrackDetailSection trackDetail={plan.trackDetail} />
            </section>
          )}

          {/* 3. 沿途风光 */}
          <section id="section-scenic">
            <SectionTitle title="沿途风光" icon={MapIcon} colorClass="text-indigo-600" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plan.scenicSpots.map((spot, idx) => (
                <Card key={idx} className="group hover:border-indigo-200 transition-all">
                  <div className="flex gap-4">
                    <div className={cn(
                      'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                      spot.spotType === '自然风光'
                        ? 'bg-[var(--forest)]/10 text-[var(--forest)] group-hover:bg-[var(--forest)] group-hover:text-white'
                        : 'bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white'
                    )}>
                      {spot.spotType === '自然风光' ? <Trees size={24} /> : <Landmark size={24} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-sm">{spot.name}</h4>
                        <span className={cn(
                          'text-[10px] px-2 py-0.5 rounded-full',
                          spot.spotType === '自然风光'
                            ? 'bg-[var(--forest)]/10 text-[var(--forest)]'
                            : 'bg-amber-50 text-amber-600'
                        )}>
                          {spot.spotType}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-600 leading-relaxed">{spot.description}</p>
                    </div>
                  </div>
                </Card>
              ))}
              {plan.scenicSpots.length === 0 && (
                <div className="col-span-full p-6 border-2 border-dashed border-[var(--stone)] rounded-2xl flex flex-col items-center justify-center text-zinc-400 gap-2">
                  <MapPin size={24} />
                  <span className="text-xs font-medium">沿途风光等待探索...</span>
                </div>
              )}
            </div>
          </section>

          {/* 4. 交通方案 */}
          {plan.transportScheme && (
            <section id="section-transport">
              <SectionTitle title="交通方案" icon={MapPin} colorClass="text-amber-600" />
              <div className="space-y-4">
                {plan.transportScheme.summary && (
                  <Card className="p-4 bg-[var(--sand)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[var(--stone)] rounded-lg">
                          <MapIcon size={20} className="text-zinc-600" />
                        </div>
                        <div>
                          <div className="text-sm text-zinc-500">从 {plan.transportScheme.origin?.address || '起点'}</div>
                          <div className="text-sm text-zinc-500">到 {plan.transportScheme.destination?.address || '终点'}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        {plan.transportScheme.summary.totalDistance && (
                          <div className="text-lg font-bold text-zinc-900">{plan.transportScheme.summary.totalDistance}</div>
                        )}
                        {plan.transportScheme.summary.totalTime && (
                          <div className="text-xs text-zinc-500">约 {plan.transportScheme.summary.totalTime}</div>
                        )}
                      </div>
                    </div>
                  </Card>
                )}
                {plan.transportScheme.outbound?.driving && (
                  <Card className={cn(
                    'p-4 border-l-4',
                    plan.transportScheme.recommendedMode === '驾车' ? 'border-l-amber-500 bg-amber-50/50' : 'border-l-[var(--stone)]'
                  )}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-100 rounded-lg">
                          <Navigation size={20} className="text-amber-600" />
                        </div>
                        <div>
                          <h3 className="font-bold text-zinc-900">驾车</h3>
                          <p className="text-xs text-zinc-500">自驾前往</p>
                        </div>
                      </div>
                      {plan.transportScheme.recommendedMode === '驾车' && (
                        <span className="px-2 py-1 bg-amber-500 text-white text-xs font-bold rounded-full">推荐</span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transportScheme.outbound.driving.distanceKm}km</div>
                        <div className="text-xs text-zinc-500">距离</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transportScheme.outbound.driving.durationMin}分钟</div>
                        <div className="text-xs text-zinc-500">预计时间</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transportScheme.outbound.driving.tollsYuan}元</div>
                        <div className="text-xs text-zinc-500">过路费</div>
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            </section>
          )}

          {/* 5. 安全评估 */}
          <section id="section-safety">
            <SectionTitle title="安全与应急模块" icon={ShieldAlert} colorClass="text-rose-600" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-rose-50 rounded-xl border border-rose-100">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-rose-500 text-white rounded-lg">
                      <AlertTriangle size={20} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-rose-900">
                        综合风险定级: {plan.safetyAssessment.overallRisk || '未知'}
                      </div>
                      <p className="text-xs text-rose-700">{plan.safetyAssessment.conditions || '暂无详细描述'}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {plan.riskFactors.map((factor, idx) => (
                      <span key={idx} className="px-2 py-1 bg-white text-rose-600 text-[10px] font-black uppercase tracking-tighter rounded border border-rose-200">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">具体安全隐患</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {plan.safetyIssues.map((issue: SafetyIssue, idx: number) => (
                      <div key={idx} className="p-4 border border-[var(--stone)] rounded-xl hover:border-zinc-200 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-bold text-sm flex items-center gap-2">
                            <div className={cn(
                              'w-2 h-2 rounded-full',
                              issue.severity === '高' ? 'bg-rose-500' : issue.severity === '中' ? 'bg-amber-500' : 'bg-[var(--forest)]'
                            )} />
                            {issue.type}
                          </div>
                          <Badge variant={issue.severity === '高' ? 'error' : issue.severity === '中' ? 'warning' : 'success'}>
                            严重程度: {issue.severity}
                          </Badge>
                        </div>
                        <p className="text-xs text-zinc-600 mb-3 leading-relaxed">{issue.description}</p>
                        <div className="flex items-start gap-2 p-2 bg-[var(--sand)] rounded-lg text-xs text-zinc-500 italic">
                          <Info size={14} className="mt-0.5 flex-shrink-0" />
                          <span>缓解措施: {issue.mitigation}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
              <Card className="bg-zinc-900 text-white border-none">
                <div className="flex items-center gap-2 mb-6 text-rose-400">
                  <PhoneCall size={20} />
                  <h3 className="font-bold">应急救援联络</h3>
                </div>
                <div className="space-y-4">
                  {plan.emergencyRescueContacts.map((contact, idx) => (
                    <div key={idx} className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-xs text-zinc-400 mb-1">{contact.name}</div>
                      <div className="text-lg font-mono font-bold text-white tracking-wider">{contact.phone}</div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </section>

          {/* 6. 天气预报 */}
          <section id="section-weather">
            <SectionTitle title="动态天气看板" icon={CloudSun} colorClass="text-blue-600" />
            <Card className="p-0 overflow-hidden">
              <div className="flex border-b border-[var(--stone)]">
                <button
                  onClick={() => setWeatherTab('overview')}
                  className={cn(
                    'flex-1 py-4 text-sm font-bold transition-colors',
                    weatherTab === 'overview' ? 'bg-[var(--sand)] text-zinc-900 border-b-2 border-[var(--forest)]' : 'text-zinc-400 hover:text-zinc-600'
                  )}
                >
                  详情与格点
                </button>
                <button
                  onClick={() => setWeatherTab('hourly')}
                  className={cn(
                    'flex-1 py-4 text-sm font-bold transition-colors',
                    weatherTab === 'hourly' ? 'bg-[var(--sand)] text-zinc-900 border-b-2 border-[var(--forest)]' : 'text-zinc-400 hover:text-zinc-600'
                  )}
                >
                  逐小时预报
                </button>
              </div>
              <div className="p-6">
                <AnimatePresence mode="wait">
                  {weatherTab === 'overview' ? (
                    <motion.div
                      key="overview"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="grid grid-cols-1 lg:grid-cols-2 gap-8"
                    >
                      <div className="space-y-6">
                        <div className="flex items-end gap-4">
                          <div className="text-5xl font-black tracking-tighter">
                            {plan.tripDateWeather.tempMax}°<span className="text-zinc-300">/</span>{plan.tripDateWeather.tempMin}°
                          </div>
                          <div className="pb-1">
                            <div className="text-sm font-bold">{plan.tripDateWeather.textDay}</div>
                            <div className="text-xs text-zinc-500">日期: {plan.tripDateWeather.fxDate}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                          <div className="flex items-center gap-2 text-zinc-600">
                            <Wind size={16} className="text-zinc-400" />
                            <span className="text-xs font-medium">风力: {plan.tripDateWeather.windScaleDay}级</span>
                          </div>
                          <div className="flex items-center gap-2 text-zinc-600">
                            <Droplets size={16} className="text-zinc-400" />
                            <span className="text-xs font-medium">降水: {plan.tripDateWeather.precip}mm</span>
                          </div>
                          {plan.tripDateWeather.uvIndex != null && (
                            <div className="flex items-center gap-2 text-zinc-600">
                              <Sun size={16} className="text-zinc-400" />
                              <span className="text-xs font-medium">紫外线: {plan.tripDateWeather.uvIndex}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="bg-[var(--sand)] rounded-xl p-4 space-y-3">
                        <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-2">关键节点格点数据</div>
                        {plan.criticalGridWeather.map((grid, idx) => {
                          const windSpeed = windScaleToSpeed(grid.windScale);
                          const windChill = calculateWindChill(grid.temp, windSpeed.avg);
                          return (
                            <div key={idx} className={cn(
                              'flex items-center justify-between p-3 rounded-lg border',
                              grid.pointType === '最高点' ? 'bg-white border-amber-200 shadow-sm' : 'bg-transparent border-[var(--stone)]'
                            )}>
                              <div className="flex items-center gap-2">
                                {grid.pointType === '最高点' ? <ArrowUp size={14} className="text-amber-500" /> : <MapPin size={14} className="text-zinc-400" />}
                                <span className="text-sm font-bold">{grid.pointType}</span>
                              </div>
                              <div className="flex items-center gap-4 text-xs font-mono">
                                <span className="flex items-center gap-1"><Thermometer size={12} /> {grid.temp}°C</span>
                                <span className="flex items-center gap-1"><Wind size={12} /> {grid.windScale}</span>
                                <span className="flex items-center gap-1"><Droplets size={12} /> {grid.humidity}%</span>
                                {grid.pointType === '最高点' && windChill !== null && (
                                  <span className={cn('flex items-center gap-1', getWindChillRisk(windChill)?.color)}>
                                    <Snowflake size={12} />
                                    体感 {windChill}°C
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="hourly"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="h-[300px] w-full"
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={plan.hourlyWeather.map(h => {
                          let timeLabel = '';
                          if (h.fxTime.includes('T')) {
                            const timePart = h.fxTime.split('T')[1];
                            if (timePart) {
                              timeLabel = timePart.substring(0, 5);
                            }
                          } else {
                            timeLabel = h.fxTime;
                          }
                          return { ...h, time: timeLabel };
                        })}>
                          <defs>
                            <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f1f1" />
                          <XAxis
                            dataKey="time"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 10, fill: '#94a3b8' }}
                            interval="preserveStartEnd"
                          />
                          <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
                          <Tooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                            labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
                            formatter={(value: number) => [`${value}°C`, '温度']}
                          />
                          <Area
                            type="monotone"
                            dataKey="temp"
                            stroke="#3b82f6"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorTemp)"
                            name="温度"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </Card>
          </section>

          {/* 7. 装备建议 */}
          <section id="section-equipment">
            <SectionTitle title="行前准备" icon={Backpack} colorClass="text-[var(--earth-dark)]" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <Card>
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">装备清单</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {plan.equipmentRecommendations.map((item: EquipmentItem, i: number) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl border border-[var(--stone)] hover:border-zinc-200 hover:shadow-sm transition-all group cursor-pointer"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-8 h-8 rounded-lg bg-[var(--sand)] flex items-center justify-center text-zinc-400 group-hover:bg-[var(--forest)]/10 group-hover:text-[var(--forest)] transition-colors">
                            <CheckCircle2 size={16} />
                          </div>
                          <span className="text-[10px] text-zinc-400 bg-[var(--sand)] px-1.5 py-0.5 rounded">{item.category}</span>
                        </div>
                        <div className="text-sm font-medium">{item.name}</div>
                        {item.description && (
                          <div className="text-[10px] text-zinc-400 mt-1 line-clamp-2">{item.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
              <Card className="bg-gradient-to-br from-[var(--forest)]/5 to-[var(--forest)]/10 border-[var(--forest)]/20">
                <h3 className="text-sm font-bold text-[var(--forest-dark)] uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Navigation size={16} /> 向导建议
                </h3>
                <div className="text-sm text-[var(--forest-dark)] leading-relaxed whitespace-pre-line">
                  {plan.hikingAdvice || '暂无向导建议'}
                </div>
              </Card>
            </div>
          </section>
        </div>
      </main>
      </div>

      {/* Footer */}
      <footer className="max-w-5xl mx-auto px-4 py-12 border-t border-[var(--stone)]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 text-zinc-400">
            <ShieldAlert size={16} />
            <span className="text-xs">本策划书由 AI 辅助生成，仅供参考。</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ReportDetailPage;
