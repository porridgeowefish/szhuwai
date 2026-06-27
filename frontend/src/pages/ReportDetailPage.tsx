import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldAlert, CloudSun, MapPin, Backpack, Navigation, PhoneCall, Clock,
  Thermometer, Wind, Droplets, Sun, AlertTriangle, CheckCircle2, Info,
  Mountain, ArrowUp, Snowflake, Download, Image as ImageIcon, Map as MapIcon,
  List, ClipboardCheck
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { PlanData, SafetyIssue, EquipmentItem } from '../types';
import type { PlanningRunReport } from '../lib/api/plan';
import { calculateFeelsLike, calculateWindChill, windScaleToSpeed, getWindChillRisk } from '../utils/weather';
import { exportToLongImage, exportToPDF } from '../utils/pdf';
import { cn } from '../utils/cn';
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

const EmptyModule = ({ icon: Icon, title, description }: {
  icon: React.ElementType;
  title: string;
  description: string;
}) => (
  <div className="rounded-xl border border-dashed border-[var(--stone)] bg-[var(--sand)] p-5 text-center">
    <Icon className="mx-auto text-zinc-400" size={24} />
    <div className="mt-2 text-sm font-bold text-zinc-700">{title}</div>
    <p className="mt-1 text-xs leading-5 text-zinc-500">{description}</p>
  </div>
);

const WeatherMetric = ({ icon: Icon, label, value }: {
  icon: React.ElementType;
  label: string;
  value: string;
}) => (
  <div className="rounded-xl border border-[var(--stone)] bg-white px-3 py-3">
    <div className="flex items-center gap-1.5 text-xs text-zinc-500">
      <Icon size={14} className="text-zinc-400" />
      {label}
    </div>
    <div className="mt-1 text-sm font-bold text-zinc-900">{value}</div>
  </div>
);

// 目录导航项配置
interface TocItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

const ReportDetailPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState<null | 'image' | 'pdf'>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('');

  // 从路由 state 获取计划数据，或从 API 获取
  const statePlan = location.state?.plan as PlanData | null;
  const stateRunReport = location.state?.runReport as PlanningRunReport | null;
  const storedPlan = useMemo<PlanData | null>(() => {
    if (statePlan) return statePlan;
    try {
      const raw = sessionStorage.getItem('latest-plan');
      return raw ? JSON.parse(raw) as PlanData : null;
    } catch {
      return null;
    }
  }, [statePlan]);
  const runReport = useMemo<PlanningRunReport | null>(() => {
    if (stateRunReport) return stateRunReport;
    try {
      const raw = sessionStorage.getItem('latest-run-report');
      return raw ? JSON.parse(raw) as PlanningRunReport : null;
    } catch {
      return null;
    }
  }, [stateRunReport]);
  const plan = storedPlan;

  // 根据实际内容动态生成目录项
  const tocItems = useMemo<TocItem[]>(() => {
    if (!plan) return [];
    const items: TocItem[] = [
      { id: 'section-route-brief', label: '线路简介', icon: Navigation },
    ];
    if (plan.trackDetail) {
      items.push({ id: 'section-track-detail', label: '线路详情', icon: Mountain });
    }
    items.push({ id: 'section-weather', label: '天气预报', icon: CloudSun });
    items.push({ id: 'section-guide', label: '出行攻略', icon: ClipboardCheck });
    if (plan.transportScheme) {
      items.push({ id: 'section-transport', label: '交通方案', icon: MapPin });
    }
    items.push(
      { id: 'section-safety', label: '安全评估', icon: ShieldAlert },
      { id: 'section-equipment', label: '装备清单', icon: Backpack },
    );
    return items;
  }, [plan]);

  // IntersectionObserver 实现 scroll spy（单一 observer 监听所有 section）
  useEffect(() => {
    if (!plan || tocItems.length === 0) return;

    const visibleSections = new Set<string>();

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            visibleSections.add(entry.target.id);
          } else {
            visibleSections.delete(entry.target.id);
          }
        });
        // 选择最靠近顶部的可见 section
        if (visibleSections.size > 0) {
          let topId = '';
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
          if (topId) setActiveSection(topId);
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
    );

    tocItems.forEach((item) => {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [plan, tocItems]);

  // 平滑滚动到指定 section
  const scrollToSection = useCallback((sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  if (!plan) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="max-w-md rounded-2xl border border-[var(--border)] bg-white p-8 text-center">
          <h1 className="text-xl font-bold">暂无策划结果</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">请先从两步路线路 URL 生成一份策划。</p>
          <button className="primary-button mt-5" onClick={() => navigate('/')}>返回开始策划</button>
        </div>
      </div>
    );
  }

  const defaultWeather = {
    fxDate: '未选择日期',
    tempMax: 0,
    tempMin: 0,
    textDay: '暂无天气数据',
    windScaleDay: '未知',
    windSpeedDay: 0,
    humidity: 0,
    precip: 0,
    pressure: 0,
  };
  const tripDateWeather = plan.tripDateWeather || defaultWeather;
  const hourlyWeather = plan.hourlyWeather || [];
  const criticalGridWeather = plan.criticalGridWeather || [];
  const webReferences = plan.webReferences || [];
  const equipmentRecommendations = plan.equipmentRecommendations || [];
  const safetyIssues = plan.safetyIssues || [];
  const riskFactors = plan.riskFactors || [];
  const rescueContacts = plan.emergencyRescueContacts || [];
  const hasRealWeather = tripDateWeather.textDay !== '暂无天气数据' && Boolean(plan.tripDateWeather);
  const webSummary = plan.webSummary?.trim();
  const weatherBasePoint = criticalGridWeather.find((grid) => grid.pointType === '地区基准') || criticalGridWeather[0];
  const representativeTemp = weatherBasePoint?.temp ?? Math.round((tripDateWeather.tempMax + tripDateWeather.tempMin) / 2);
  const dailyWindSpeed = windScaleToSpeed(tripDateWeather.windScaleDay);
  const dailyFeelsLike = calculateFeelsLike(representativeTemp, dailyWindSpeed.avg, tripDateWeather.humidity);
  const dailyWindChill = calculateWindChill(representativeTemp, dailyWindSpeed.avg);
  const estimatedWeatherPoints = criticalGridWeather.filter((grid) =>
    ['起点', '最高点', '终点'].includes(grid.pointType)
  );

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
            </div>
            <div className="flex items-center gap-4 text-xs text-zinc-500 font-mono">
              <span className="flex items-center gap-1"><Clock size={12} /> {formatDateTime(plan.createdAt)}</span>
              <span className="flex items-center gap-1">ID: {plan.planId}</span>
            </div>
          </div>
          <div className="no-print flex flex-wrap items-center gap-2">
            <button
              onClick={async () => {
                if (!mainContentRef.current || !plan || exporting) return;
                setExporting('image');
                setExportError(null);
                try {
                  await exportToLongImage(mainContentRef.current, plan.planName);
                } catch (err) {
                  console.error('长图导出错误:', err);
                  setExportError('长图导出失败：页面可能过长或地图瓦片跨域受限，建议缩小窗口或改用 PDF。');
                } finally {
                  setExporting(null);
                }
              }}
              disabled={exporting !== null}
              className="px-4 py-2 bg-white text-zinc-900 rounded-xl text-sm font-bold hover:bg-zinc-100 transition-colors flex items-center gap-2 border border-[var(--stone)] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <ImageIcon size={16} /> {exporting === 'image' ? '生成中…' : '导出长图'}
            </button>
            <button
              onClick={async () => {
                if (!plan || exporting) return;
                setExporting('pdf');
                setExportError(null);
                try {
                  await exportToPDF();
                } catch (err) {
                  console.error('PDF导出错误:', err);
                  setExportError('PDF 打印启动失败：请检查浏览器是否拦截了打印弹窗，或换用桌面端浏览器。');
                } finally {
                  setExporting(null);
                }
              }}
              disabled={exporting !== null}
              className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-sm font-bold hover:bg-zinc-800 transition-colors flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Download size={16} /> {exporting === 'pdf' ? '准备打印…' : '导出 PDF'}
            </button>
            {exportError ? (
              <span className="text-xs font-semibold text-red-600">{exportError}</span>
            ) : null}
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
          <section id="section-route-brief" className="scroll-mt-32 lg:scroll-mt-24">
            <RouteBrief
              planName={plan.planName}
              trackDetail={plan.trackDetail}
            />
          </section>

          {runReport && (
            <section className="scroll-mt-32 lg:scroll-mt-24">
              <Card className="p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-bold text-zinc-900">运行回执</div>
                    <div className="mt-1 text-xs text-zinc-500">Run {runReport.run_id} · {runReport.total_duration_ms}ms</div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {runReport.stages.map((stage) => (
                      <span
                        key={`${stage.stage}-${stage.title}`}
                        className={cn(
                          'rounded-full border px-2.5 py-1 text-[11px] font-bold',
                          stage.status === 'success' && 'border-emerald-200 bg-emerald-50 text-emerald-700',
                          stage.status === 'degraded' && 'border-amber-200 bg-amber-50 text-amber-700',
                          stage.status === 'skipped' && 'border-zinc-200 bg-zinc-50 text-zinc-500',
                          stage.status === 'failed' && 'border-rose-200 bg-rose-50 text-rose-700',
                        )}
                      >
                        {stage.title}
                      </span>
                    ))}
                  </div>
                </div>
                {runReport.warnings.length > 0 && (
                  <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
                    {runReport.warnings.join('；')}
                  </div>
                )}
              </Card>
            </section>
          )}

          {/* 2. 线路详情 */}
          {plan.trackDetail && (
            <section id="section-track-detail" className="scroll-mt-32 lg:scroll-mt-24">
              <SectionTitle title="线路详情" icon={Mountain} colorClass="text-[var(--forest)]" />
              <TrackDetailSection trackDetail={plan.trackDetail} />
            </section>
          )}

          {/* 3. 天气预报 */}
          <section id="section-weather" className="scroll-mt-32 lg:scroll-mt-24">
            <SectionTitle title="天气预报" icon={CloudSun} colorClass="text-blue-600" />
            <Card className="space-y-5">
              {hasRealWeather ? (
                <>
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(280px,1fr)]">
                    <div>
                      <div className="flex flex-wrap items-end gap-4">
                        <div className="text-5xl font-black tracking-tight">
                          {tripDateWeather.tempMax}°<span className="text-zinc-300">/</span>{tripDateWeather.tempMin}°
                        </div>
                        <div className="pb-1">
                          <div className="text-sm font-bold text-zinc-900">{tripDateWeather.textDay}</div>
                          <div className="text-xs text-zinc-500">{tripDateWeather.fxDate}</div>
                        </div>
                      </div>
                      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <WeatherMetric icon={Wind} label="风力" value={`${tripDateWeather.windScaleDay}级`} />
                        <WeatherMetric icon={Droplets} label="降水" value={`${tripDateWeather.precip}mm`} />
                        <WeatherMetric icon={Thermometer} label="体感" value={`${dailyFeelsLike}°C`} />
                        <WeatherMetric icon={Sun} label="紫外线" value={tripDateWeather.uvIndex != null ? `${tripDateWeather.uvIndex} · ${weatherBasePoint?.uvLevel || '待评估'}` : '暂无'} />
                      </div>
                      {dailyWindChill !== null ? (
                        <div className={cn('mt-3 inline-flex items-center gap-2 rounded-full bg-zinc-50 px-3 py-1 text-xs font-medium', getWindChillRisk(dailyWindChill).color)}>
                          <Snowflake size={13} />
                          风寒 {dailyWindChill}°C，{getWindChillRisk(dailyWindChill).description}
                        </div>
                      ) : null}
                      {weatherBasePoint ? (
                        <div className="mt-4 rounded-xl border border-[var(--stone)] bg-[var(--sand)] p-3 text-xs leading-5 text-zinc-600">
                          <div className="font-bold text-zinc-900">地区基准：{weatherBasePoint.temp}°C</div>
                          <div>风力 {weatherBasePoint.windScale} · 湿度 {weatherBasePoint.humidity}% · 紫外线 {weatherBasePoint.uvLevel || '待评估'}</div>
                          {weatherBasePoint.note ? <div className="mt-1 text-zinc-500">{weatherBasePoint.note}</div> : null}
                        </div>
                      ) : null}
                    </div>

                    <div className="rounded-xl bg-[var(--sand)] p-4">
                      <div className="mb-3 text-xs font-bold uppercase tracking-widest text-zinc-400">海拔估算节点</div>
                      <div className="space-y-2">
                        {estimatedWeatherPoints.length > 0 ? estimatedWeatherPoints.map((grid, idx) => (
                          <div key={`${grid.pointType}-${idx}`} className="rounded-lg border border-[var(--stone)] bg-white/70 p-3">
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-2 text-sm font-bold text-zinc-900">
                                {grid.pointType === '最高点' ? <ArrowUp size={14} className="text-amber-600" /> : <MapPin size={14} className="text-zinc-400" />}
                                {grid.pointType}
                                {grid.estimated ? <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] text-amber-700">估算</span> : null}
                              </div>
                              <div className="font-mono text-sm font-bold">{grid.temp}°C</div>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-500">
                              <span>风力 {grid.windScale}</span>
                              <span>湿度 {grid.humidity}%</span>
                              {grid.feelsLike != null ? <span>体感 {grid.feelsLike}°C</span> : null}
                              {grid.windChill != null ? <span>风寒 {grid.windChill}°C</span> : null}
                              {grid.uvLevel ? <span>紫外线 {grid.uvLevel}</span> : null}
                            </div>
                            {grid.note ? <p className="mt-2 text-[11px] leading-5 text-amber-700">{grid.note}</p> : null}
                          </div>
                        )) : (
                          <EmptyModule icon={MapPin} title="暂无估算节点天气" description="后端没有返回起点、最高点或终点海拔数据，请检查轨迹文件。" />
                        )}
                      </div>
                    </div>
                  </div>
                  {hourlyWeather.length > 0 ? (
                    <div>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="text-xs font-bold uppercase tracking-widest text-zinc-400">出行日白天逐小时</div>
                        <div className="text-xs text-zinc-400">06:00-20:00</div>
                      </div>
                      <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={hourlyWeather.map(h => ({
                            ...h,
                            time: h.fxTime.includes('T') ? h.fxTime.split('T')[1]?.substring(0, 5) || h.fxTime : h.fxTime,
                          }))}>
                            <defs>
                              <linearGradient id="colorTempInline" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.16} />
                                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eeeeee" />
                            <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#71717a' }} interval="preserveStartEnd" />
                            <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
                            <Tooltip formatter={(value: number) => [`${value}°C`, '温度']} />
                            <Area type="monotone" dataKey="temp" stroke="#2563eb" strokeWidth={2.5} fill="url(#colorTempInline)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ) : (
                    <EmptyModule icon={Clock} title="暂无出行日白天逐小时预报" description="当前 24 小时预报未覆盖出行日 06:00-20:00，系统不使用凌晨或其他日期数据替代。" />
                  )}
                </>
              ) : (
                <EmptyModule
                  icon={CloudSun}
                  title="天气数据未启用"
                  description="填写出行日期并配置和风天气 Key 后，系统会展示天气、体感、风寒和关键点估算。"
                />
              )}
            </Card>
          </section>

          {/* 4. 出行攻略 */}
          <section id="section-guide" className="scroll-mt-32 lg:scroll-mt-24">
            <SectionTitle title="出行攻略" icon={ClipboardCheck} colorClass="text-[var(--forest)]" />
            <Card>
              <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-400">沿途风光与网络洞察</h3>
                  {webSummary ? <p className="mt-2 text-sm leading-7 text-zinc-700">{webSummary}</p> : null}
                </div>
                {webReferences.length > 0 ? (
                  <span className="shrink-0 rounded-full bg-[var(--forest)]/10 px-3 py-1 text-xs font-bold text-[var(--forest)]">
                    {webReferences.length} 条来源
                  </span>
                ) : null}
              </div>
              {webSummary || webReferences.length > 0 ? (
                webReferences.length > 0 ? (
                  <ul className="grid gap-3 md:grid-cols-2">
                    {webReferences.map((item) => (
                      <li key={item.url} className="rounded-xl border border-[var(--stone)] p-3">
                        <a href={item.url} target="_blank" rel="noreferrer" className="text-sm font-bold text-zinc-900 hover:text-[var(--forest)] break-all">
                          {item.title}
                        </a>
                        {item.source ? <div className="mt-0.5 text-xs text-zinc-400">{item.source}</div> : null}
                        {item.snippet ? <p className="mt-1 text-xs leading-5 text-zinc-500">{item.snippet}</p> : null}
                      </li>
                    ))}
                  </ul>
                ) : null
              ) : (
                <EmptyModule icon={List} title="暂无网络洞察" description="未配置搜索或 AI key 时，此处不会编造沿途风光和攻略信息。" />
              )}
            </Card>
          </section>

          {/* 4. 交通方案 */}
          {plan.transportScheme && (
            <section id="section-transport" className="scroll-mt-32 lg:scroll-mt-24">
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
                  <Card className="p-4 border-l-4 border-l-amber-500 bg-amber-50/50">
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
                {(plan.transportScheme.transitRoutes?.length || plan.transportScheme.outbound?.transit) ? (
                  <Card className="p-4 border-l-4 border-l-sky-500 bg-sky-50/50">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-sky-100 p-2">
                          <MapIcon size={20} className="text-sky-700" />
                        </div>
                        <div>
                          <h3 className="font-bold text-zinc-900">公共交通</h3>
                          <p className="text-xs text-zinc-500">含地铁/公交换乘方案</p>
                        </div>
                      </div>
                      <div className="text-right text-xs text-zinc-500">
                        {(plan.transportScheme.transitRoutes || [plan.transportScheme.outbound.transit]).filter(Boolean).length} 个方案
                      </div>
                    </div>
                    <div className="space-y-3">
                      {(plan.transportScheme.transitRoutes || [plan.transportScheme.outbound.transit]).filter(Boolean).slice(0, 3).map((route, routeIdx) => route ? (
                        <div key={routeIdx} className="rounded-xl border border-sky-100 bg-white p-3">
                          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-bold text-zinc-900">方案 {routeIdx + 1}</div>
                            <div className="flex gap-3 text-xs text-zinc-500">
                              <span>{route.distanceKm.toFixed(1)}km</span>
                              <span>{route.durationMin}分钟</span>
                              <span>{route.costYuan}元</span>
                              <span>步行 {route.walkingDistance}m</span>
                            </div>
                          </div>
                          {route.segments && route.segments.length > 0 ? (
                            <div className="space-y-2">
                              {route.segments.map((segment, segIdx) => (
                                <div key={`${segment.lineName}-${segIdx}`} className="flex items-start gap-2 text-xs leading-5 text-zinc-600">
                                  <span className={cn(
                                    'mt-0.5 shrink-0 rounded-full px-2 py-0.5 font-bold',
                                    segment.type === 'subway' ? 'bg-emerald-100 text-emerald-700' : 'bg-sky-100 text-sky-700'
                                  )}>
                                    {segment.type === 'subway' ? '地铁' : '公交'}
                                  </span>
                                  <span>
                                    <strong className="text-zinc-900">{segment.lineName}</strong>
                                    {' '}从 {segment.departureStop || '上车站'} 到 {segment.arrivalStop || '下车站'}
                                    {' '}· {segment.durationMin}分钟 · {(segment.distanceM / 1000).toFixed(1)}km
                                  </span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-xs text-zinc-500">地图接口未返回逐段换乘详情，请以高德地图复核。</div>
                          )}
                        </div>
                      ) : null)}
                    </div>
                  </Card>
                ) : (
                  <Card className="p-4 border-l-4 border-l-zinc-300">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-zinc-100 p-2">
                        <MapIcon size={20} className="text-zinc-500" />
                      </div>
                      <div>
                        <h3 className="font-bold text-zinc-900">公共交通</h3>
                        <p className="text-xs text-zinc-500">地图接口未返回可用公交/地铁方案。</p>
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            </section>
          )}

          {/* 5. 安全评估 */}
          <section id="section-safety" className="scroll-mt-32 lg:scroll-mt-24">
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
                    {riskFactors.length > 0 ? (
                      riskFactors.map((factor, idx) => (
                        <span key={idx} className="px-2 py-1 bg-white text-rose-600 text-[10px] font-black uppercase tracking-tighter rounded border border-rose-200">
                          {factor}
                        </span>
                      ))
                    ) : (
                      <span className="px-2 py-1 bg-white text-rose-600 text-[10px] font-black uppercase tracking-tighter rounded border border-rose-200">
                        待补充
                      </span>
                    )}
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">具体安全隐患</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {safetyIssues.length > 0 ? (
                      safetyIssues.map((issue: SafetyIssue, idx: number) => (
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
                      ))
                    ) : (
                      <EmptyModule icon={ShieldAlert} title="暂无安全隐患清单" description="当前报告没有返回结构化安全隐患，建议按轨迹海拔、路况、天气和撤退点人工复核。" />
                    )}
                  </div>
                </div>
              </Card>
              <Card className="bg-zinc-900 text-white border-none">
                <div className="flex items-center gap-2 mb-6 text-rose-400">
                  <PhoneCall size={20} />
                  <h3 className="font-bold">应急救援联络</h3>
                </div>
                <div className="space-y-4">
                  {rescueContacts.length > 0 ? (
                    rescueContacts.map((contact, idx) => (
                      <div key={idx} className="p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="text-xs text-zinc-400 mb-1">{contact.name}</div>
                        <div className="text-lg font-mono font-bold text-white tracking-wider">{contact.phone}</div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-xs text-zinc-400 mb-1">通用紧急电话</div>
                      <div className="text-lg font-mono font-bold text-white tracking-wider">110 / 120 / 119</div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </section>

          {/* 7. 装备建议 */}
          <section id="section-equipment" className="scroll-mt-32 lg:scroll-mt-24">
            <SectionTitle title="行前准备" icon={Backpack} colorClass="text-[var(--earth-dark)]" />
            <Card>
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">装备清单</h3>
              {equipmentRecommendations.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {equipmentRecommendations.map((item: EquipmentItem, i: number) => (
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
              ) : (
                <EmptyModule icon={Backpack} title="暂无装备清单" description="当前报告没有返回装备条目；建议至少携带水、补给、雨具、头灯、急救包和离线地图。" />
              )}
            </Card>
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
