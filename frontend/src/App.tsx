import React, { useState, useRef } from 'react';
import {
  ShieldAlert,
  CloudSun,
  MapPin,
  Backpack,
  Navigation,
  PhoneCall,
  Clock,
  Thermometer,
  Wind,
  Droplets,
  Sun,
  Eye,
  AlertTriangle,
  CheckCircle2,
  Info,
  Mountain,
  ArrowUp,
  ArrowDown,
  Cloud,
  Timer,
  Gauge,
  Trees,
  Landmark,
  Snowflake,
  Download,
  Tent,
  Map as MapIcon
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import {
  PlanData,
  PlanResponse,
  SafetyIssue,
  HourlyWeather,
  EquipmentItem,
  TransitRoute
} from './types';
import {
  calculateWindChill,
  windScaleToSpeed,
  getWindChillRisk
} from './utils/weather';
import { exportToPDF } from './utils/pdf';
import { cn } from './utils/cn';

// 新组件
import { HeroSection } from './components/HeroSection';
import { RouteBrief } from './components/RouteBrief';
import { TrackDetailSection } from './components/TrackDetailSection';
import { ElevationChart } from './components/ElevationChart';

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

const SectionTitle = ({ title, icon: Icon, colorClass = 'text-zinc-900' }: { title: string; icon: React.ElementType; colorClass?: string }) => (
  <div className="flex items-center gap-3 mb-6 relative pl-5 section-title-decoration">
    <div className={cn('p-2 rounded-lg bg-[var(--sand)]', colorClass)}>
      <Icon size={20} />
    </div>
    <h2 className="text-xl font-bold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
      {title}
    </h2>
  </div>
);

const Card = ({ children, className, ...props }: { children: React.ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('bg-white border border-[var(--stone)] rounded-2xl p-6 shadow-sm card-hover', className)} {...props}>
    {children}
  </div>
);

const Badge = ({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'success' | 'warning' | 'error' }) => {
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

export default function App() {
  const [tripDate, setTripDate] = useState('');
  const [departurePoint, setDeparturePoint] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [weatherTab, setWeatherTab] = useState<'overview' | 'hourly'>('overview');
  const fileInputRef2 = useRef<HTMLInputElement>(null);
  const mainContentRef = useRef<HTMLDivElement>(null);

  // 线路名称和核心目的地
  const [planTitle, setPlanTitle] = useState('');
  const [destination1, setDestination1] = useState('');
  const [destination2, setDestination2] = useState('');
  const [destination3, setDestination3] = useState('');

  const handleGenerate = async () => {
    // 强拦截逻辑：校验必须字段
    if (!file || !tripDate || !departurePoint) {
      setError('必须选择日期、填写出发点并上传轨迹文件！');
      return;
    }

    if (!planTitle.trim()) {
      setError('请输入线路名称！');
      return;
    }

    const destinations = [destination1, destination2, destination3].filter(d => d.trim());
    if (destinations.length === 0) {
      setError('请至少填写一个核心目的地！');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('trip_date', tripDate);
      formData.append('departure_point', departurePoint);
      formData.append('additional_info', additionalInfo);
      formData.append('file', file);
      formData.append('plan_title', planTitle);
      formData.append('key_destinations', destinations.join(','));

      const response = await fetch('/api/v1/generate-plan', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const responseData: PlanResponse = await response.json();
      setPlan(responseData.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成策划书失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      if (ext === 'gpx' || ext === 'kml') {
        setFile(selectedFile);
      } else {
        setError('请选择 GPX 或 KML 格式的文件');
      }
    }
    if (fileInputRef2.current) {
      fileInputRef2.current.value = '';
    }
  };

  const clearFile = () => {
    setFile(null);
    if (fileInputRef2.current) {
      fileInputRef2.current.value = '';
    }
  };

  const getRatingVariant = (rating: string) => {
    if (rating === '推荐') return 'success';
    if (rating === '谨慎推荐') return 'warning';
    return 'error';
  };

  const getRiskVariant = (level: string) => {
    if (level === '低') return 'success';
    if (level === '中') return 'warning';
    return 'error';
  };

  // 未生成计划时显示 Hero 入口页
  if (!plan && !isLoading) {
    return (
      <div className="min-h-screen bg-[var(--sand)]">
        <HeroSection
          tripDate={tripDate}
          setTripDate={setTripDate}
          departurePoint={departurePoint}
          setDeparturePoint={setDeparturePoint}
          planTitle={planTitle}
          setPlanTitle={setPlanTitle}
          destination1={destination1}
          setDestination1={setDestination1}
          destination2={destination2}
          setDestination2={setDestination2}
          destination3={destination3}
          setDestination3={setDestination3}
          additionalInfo={additionalInfo}
          setAdditionalInfo={setAdditionalInfo}
          file={file}
          setFile={setFile}
          isLoading={isLoading}
          onGenerate={handleGenerate}
          error={error}
        />
      </div>
    );
  }

  // 加载中状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--sand)] flex flex-col items-center justify-center py-20 space-y-6">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-[var(--stone)] rounded-full" />
          <div className="absolute inset-0 w-20 h-20 border-4 border-[var(--forest)] rounded-full border-t-transparent animate-spin" />
        </div>
        <div className="text-center space-y-2">
          <p className="text-lg font-bold text-zinc-900">Agent 正在分析轨迹与天气数据...</p>
          <p className="text-sm text-zinc-500">这可能需要几秒钟，请稍候</p>
        </div>
      </div>
    );
  }

  // 已有计划 - 显示详情页
  return (
    <div className="min-h-screen bg-[var(--sand)] text-zinc-900 font-sans">
      {/* Header - 已有策划 */}
      <header className="bg-white border-b border-[var(--stone)] sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-black tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                {plan.plan_name}
              </h1>
              <Badge variant={getRatingVariant(plan.overall_rating)}>{plan.overall_rating}</Badge>
            </div>
            <div className="flex items-center gap-4 text-xs text-zinc-500 font-mono">
              <span className="flex items-center gap-1"><Clock size={12} /> {formatDateTime(plan.created_at)}</span>
              <span className="flex items-center gap-1">ID: {plan.plan_id}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
              placeholder="补充要求..."
              className="px-3 py-2 text-sm border border-[var(--stone)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--forest)] focus:border-transparent w-48 md:w-64"
              disabled={isLoading}
            />
            <div className="relative">
              <input
                ref={fileInputRef2}
                type="file"
                accept=".gpx,.kml"
                onChange={handleFileChange}
                className="hidden"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => fileInputRef2.current?.click()}
                disabled={isLoading}
                className={cn(
                  'p-2 border border-[var(--stone)] rounded-lg hover:border-[var(--forest)] hover:bg-[var(--sand)] transition-all text-zinc-600',
                  isLoading && 'opacity-50 cursor-not-allowed'
                )}
                title="上传 GPX/KML 文件"
              >
                <Navigation size={16} />
              </button>
              {file && (
                <div className="absolute -top-8 left-0 flex items-center gap-1 px-2 py-1 bg-[var(--sand)] border border-[var(--forest)]/30 rounded-lg text-xs text-[var(--forest)] whitespace-nowrap">
                  <span className="max-w-[80px] truncate">{file.name}</span>
                  <button
                    type="button"
                    onClick={clearFile}
                    className="p-0.5 hover:bg-[var(--stone)] rounded"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
            <button
              onClick={handleGenerate}
              disabled={isLoading}
              className={cn(
                'px-4 py-2 bg-[var(--forest)] text-white rounded-xl text-sm font-bold hover:bg-[var(--forest-dark)] transition-all flex items-center gap-2',
                isLoading && 'opacity-70 cursor-not-allowed'
              )}
            >
              {isLoading ? '生成中...' : '重新生成'}
            </button>
            <button
              onClick={async () => {
                if (mainContentRef.current && plan) {
                  try {
                    await exportToPDF(mainContentRef.current, plan.plan_name);
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

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div ref={mainContentRef} className="pdf-export-container space-y-8">
          {/* 1. 线路简介 */}
          <section>
            <RouteBrief
              planName={plan.plan_name}
              trackDetail={plan.track_detail}
              overallRating={plan.overall_rating}
            />
          </section>

          {/* 2. 线路详情 - 平面图/海拔图切换 */}
          {plan.track_detail && (
            <section>
              <SectionTitle title="线路详情" icon={Mountain} colorClass="text-[var(--forest)]" />
              <TrackDetailSection trackDetail={plan.track_detail} />
            </section>
          )}

          {/* 3. 沿途风光 */}
          <section>
            <SectionTitle title="沿途风光" icon={MapIcon} colorClass="text-indigo-600" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plan.scenic_spots.map((spot, idx) => (
                <Card key={idx} className="group hover:border-indigo-200 transition-all">
                  <div className="flex gap-4">
                    <div className={cn(
                      'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                      spot.spot_type === '自然风光'
                        ? 'bg-[var(--forest)]/10 text-[var(--forest)] group-hover:bg-[var(--forest)] group-hover:text-white'
                        : 'bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white'
                    )}>
                      {spot.spot_type === '自然风光' ? <Trees size={24} /> : <Landmark size={24} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-sm">{spot.name}</h4>
                        <span className={cn(
                          'text-[10px] px-2 py-0.5 rounded-full',
                          spot.spot_type === '自然风光'
                            ? 'bg-[var(--forest)]/10 text-[var(--forest)]'
                            : 'bg-amber-50 text-amber-600'
                        )}>
                          {spot.spot_type}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-600 leading-relaxed">{spot.description}</p>
                    </div>
                  </div>
                </Card>
              ))}
              {plan.scenic_spots.length === 0 && (
                <div className="col-span-full p-6 border-2 border-dashed border-[var(--stone)] rounded-2xl flex flex-col items-center justify-center text-zinc-400 gap-2">
                  <MapPin size={24} />
                  <span className="text-xs font-medium">沿途风光等待探索...</span>
                </div>
              )}
            </div>
          </section>

          {/* 4. 交通方案 */}
          {plan.transport_scheme && (
            <section>
              <SectionTitle title="交通方案" icon={MapPin} colorClass="text-amber-600" />
              <div className="space-y-4">
                {/* 路线汇总 */}
                {plan.transport_scheme.summary && (
                  <Card className="p-4 bg-[var(--sand)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[var(--stone)] rounded-lg">
                          <MapIcon size={20} className="text-zinc-600" />
                        </div>
                        <div>
                          <div className="text-sm text-zinc-500">从 {plan.transport_scheme.origin?.address || '起点'}</div>
                          <div className="text-sm text-zinc-500">到 {plan.transport_scheme.destination?.address || '终点'}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        {plan.transport_scheme.summary.total_distance && (
                          <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.summary.total_distance}</div>
                        )}
                        {plan.transport_scheme.summary.total_time && (
                          <div className="text-xs text-zinc-500">约 {plan.transport_scheme.summary.total_time}</div>
                        )}
                      </div>
                    </div>
                  </Card>
                )}

                {/* 驾车方案 */}
                {plan.transport_scheme.outbound?.driving && (
                  <Card className={cn(
                    'p-4 border-l-4',
                    plan.transport_scheme.recommended_mode === '驾车' ? 'border-l-amber-500 bg-amber-50/50' : 'border-l-[var(--stone)]'
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
                      <div className="flex gap-2">
                        {plan.transport_scheme.recommended_mode === '驾车' && (
                          <span className="px-2 py-1 bg-amber-500 text-white text-xs font-bold rounded-full">推荐</span>
                        )}
                        {plan.transport_scheme.fastest_mode === '驾车' && (
                          <span className="px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">最快</span>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.outbound.driving.distance_km}km</div>
                        <div className="text-xs text-zinc-500">距离</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.outbound.driving.duration_min}分钟</div>
                        <div className="text-xs text-zinc-500">预计时间</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.outbound.driving.tolls_yuan}元</div>
                        <div className="text-xs text-zinc-500">过路费</div>
                      </div>
                    </div>
                  </Card>
                )}

                {/* 公交方案 */}
                {plan.transport_scheme.transit_routes && plan.transport_scheme.transit_routes.length > 0 && (
                  <div className="space-y-3">
                    {plan.transport_scheme.transit_routes.map((route: TransitRoute, idx: number) => (
                      <Card key={idx} className={cn(
                        'p-4 border-l-4',
                        plan.transport_scheme.recommended_mode === '公交' && idx === 0 ? 'border-l-green-500 bg-green-50/50' : 'border-l-[var(--stone)]'
                      )}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-100 rounded-lg">
                              <MapPin size={20} className="text-green-600" />
                            </div>
                            <div>
                              <h3 className="font-bold text-zinc-900">公交方案 {idx + 1}</h3>
                              <p className="text-xs text-zinc-500">{route.line_name || '公共交通'}</p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {plan.transport_scheme.recommended_mode === '公交' && idx === 0 && (
                              <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">推荐</span>
                            )}
                            {plan.transport_scheme.cheapest_mode?.includes('公交') && idx === 0 && (
                              <span className="px-2 py-1 bg-[var(--forest)] text-white text-xs font-bold rounded-full">最省钱</span>
                            )}
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-4 text-center">
                          <div>
                            <div className="text-lg font-bold text-zinc-900">{route.distance_km}km</div>
                            <div className="text-xs text-zinc-500">距离</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-zinc-900">{route.duration_min}分钟</div>
                            <div className="text-xs text-zinc-500">预计时间</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-zinc-900">{route.cost_yuan}元</div>
                            <div className="text-xs text-zinc-500">票价</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-zinc-900">{route.walking_distance}m</div>
                            <div className="text-xs text-zinc-500">步行距离</div>
                          </div>
                        </div>
                        {route.segments && route.segments.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-[var(--stone)]">
                            <div className="flex flex-wrap gap-2">
                              {route.segments.map((seg, sidx) => (
                                <div key={sidx} className={cn(
                                  'px-3 py-1.5 rounded-full text-xs font-medium',
                                  seg.type === 'subway' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                                )}>
                                  {seg.line_name}
                                  <span className="text-zinc-400 mx-1">·</span>
                                  {seg.departure_stop} → {seg.arrival_stop}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}

          {/* 5. 安全评估 */}
          <section>
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
                        综合风险定级: {plan.safety_assessment.overall_risk || '未知'}
                      </div>
                      <p className="text-xs text-rose-700">{plan.safety_assessment.conditions || '暂无详细描述'}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {plan.risk_factors.map((factor, idx) => (
                      <span key={idx} className="px-2 py-1 bg-white text-rose-600 text-[10px] font-black uppercase tracking-tighter rounded border border-rose-200">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">具体安全隐患</h3>
                  <div className="grid grid-cols-1 gap-4">
                    {plan.safety_issues.map((issue: SafetyIssue, idx: number) => (
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
                  {plan.emergency_rescue_contacts.map((contact, idx) => (
                    <div key={idx} className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-xs text-zinc-400 mb-1">{contact.name}</div>
                      <div className="text-lg font-mono font-bold text-white tracking-wider">{contact.phone}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-8 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                  <p className="text-[10px] text-rose-300 leading-relaxed">
                    * 遇紧急情况请保持冷静，寻找有信号的高地拨打求救电话，并报告准确的经纬度坐标。
                  </p>
                </div>
              </Card>
            </div>
          </section>

          {/* 6. 天气预报 */}
          <section>
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
                      {/* Day Details */}
                      <div className="space-y-6">
                        <div className="flex items-end gap-4">
                          <div className="text-5xl font-black tracking-tighter">
                            {plan.trip_date_weather.tempMax}°<span className="text-zinc-300">/</span>{plan.trip_date_weather.tempMin}°
                          </div>
                          <div className="pb-1">
                            <div className="text-sm font-bold">{plan.trip_date_weather.textDay}</div>
                            <div className="text-xs text-zinc-500">日期: {plan.trip_date_weather.fxDate}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                          <div className="flex items-center gap-2 text-zinc-600">
                            <Wind size={16} className="text-zinc-400" />
                            <span className="text-xs font-medium">风力: {plan.trip_date_weather.windScaleDay}级</span>
                          </div>
                          <div className="flex items-center gap-2 text-zinc-600">
                            <Droplets size={16} className="text-zinc-400" />
                            <span className="text-xs font-medium">降水: {plan.trip_date_weather.precip}mm</span>
                          </div>
                          {plan.trip_date_weather.uvIndex != null && (
                            <div className="flex items-center gap-2 text-zinc-600">
                              <Sun size={16} className="text-zinc-400" />
                              <span className="text-xs font-medium">紫外线: {plan.trip_date_weather.uvIndex}</span>
                            </div>
                          )}
                          {plan.trip_date_weather.vis != null && (
                            <div className="flex items-center gap-2 text-zinc-600">
                              <Eye size={16} className="text-zinc-400" />
                              <span className="text-xs font-medium">能见度: {plan.trip_date_weather.vis}km</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Critical Grids */}
                      <div className="bg-[var(--sand)] rounded-xl p-4 space-y-3">
                        <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-2">关键节点格点数据</div>
                        {plan.critical_grid_weather.map((grid, idx) => {
                          const windSpeed = windScaleToSpeed(grid.wind_scale);
                          const windChill = calculateWindChill(grid.temp, windSpeed.avg);
                          const windChillRisk = windChill !== null ? getWindChillRisk(windChill) : null;

                          return (
                            <div key={idx} className={cn(
                              'flex items-center justify-between p-3 rounded-lg border',
                              grid.point_type === '最高点' ? 'bg-white border-amber-200 shadow-sm' : 'bg-transparent border-[var(--stone)]'
                            )}>
                              <div className="flex items-center gap-2">
                                {grid.point_type === '最高点' ? <ArrowUp size={14} className="text-amber-500" /> : <MapPin size={14} className="text-zinc-400" />}
                                <span className="text-sm font-bold">{grid.point_type}</span>
                              </div>
                              <div className="flex items-center gap-4 text-xs font-mono">
                                <span className="flex items-center gap-1"><Thermometer size={12} /> {grid.temp}°C</span>
                                <span className="flex items-center gap-1"><Wind size={12} /> {grid.wind_scale}</span>
                                <span className="flex items-center gap-1"><Droplets size={12} /> {grid.humidity}%</span>
                                {grid.point_type === '最高点' && windChill !== null && (
                                  <span className={cn('flex items-center gap-1', windChillRisk?.color)}>
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
                        <AreaChart data={plan.hourly_weather.map(h => {
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
                      <div className="flex justify-between mt-4 px-1">
                        {plan.hourly_weather.filter((_, i) => i % 3 === 0).map((h, i) => {
                          const timeLabel = h.fxTime.includes('T')
                            ? h.fxTime.split('T')[1]?.substring(0, 5) || h.fxTime
                            : h.fxTime;
                          return (
                            <div key={i} className="text-center min-w-[40px]">
                              <div className="text-[10px] font-bold text-zinc-500 mb-1">{timeLabel}</div>
                              <div className="text-[10px] font-bold text-zinc-400">{h.windScale}</div>
                              <div className="text-[10px] text-blue-500">{h.pop}%</div>
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </Card>
          </section>

          {/* 7. 装备建议 */}
          <section>
            <SectionTitle title="行前准备" icon={Backpack} colorClass="text-[var(--earth-dark)]" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <Card>
                  <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">装备清单</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {plan.equipment_recommendations.map((item: EquipmentItem, i: number) => (
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
                    {plan.equipment_recommendations.length === 0 && (
                      <div className="col-span-full p-6 border-2 border-dashed border-[var(--stone)] rounded-2xl flex flex-col items-center justify-center text-zinc-400 gap-2">
                        <Backpack size={24} />
                        <span className="text-xs font-medium">装备清单生成中...</span>
                      </div>
                    )}
                  </div>
                </Card>
              </div>

              <Card className="bg-gradient-to-br from-[var(--forest)]/5 to-[var(--forest)]/10 border-[var(--forest)]/20">
                <h3 className="text-sm font-bold text-[var(--forest-dark)] uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Navigation size={16} /> 向导建议
                </h3>
                <div className="text-sm text-[var(--forest-dark)] leading-relaxed whitespace-pre-line">
                  {plan.hiking_advice || '暂无向导建议'}
                </div>
                <div className="mt-6 pt-4 border-t border-[var(--forest)]/20 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-[var(--forest)]/10 flex items-center justify-center text-[var(--forest)]">
                    <Tent size={20} />
                  </div>
                  <div className="text-[10px] text-[var(--forest)] font-medium">
                    以上建议仅供参考，请根据实际情况灵活调整。
                  </div>
                </div>
              </Card>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-5xl mx-auto px-4 py-12 border-t border-[var(--stone)]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 text-zinc-400">
            <ShieldAlert size={16} />
            <span className="text-xs">本策划书由 AI 辅助生成，仅供参考。</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-bold text-zinc-400 uppercase tracking-widest">
            <a href="#" className="hover:text-zinc-900 transition-colors">免责声明</a>
            <a href="#" className="hover:text-zinc-900 transition-colors">隐私政策</a>
            <a href="#" className="hover:text-zinc-900 transition-colors">联系我们</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
