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
  Calendar,
  ChevronRight,
  TrendingUp,
  Map as MapIcon,
  Tent,
  Paperclip,
  X,
  Mountain,
  ArrowUp,
  ArrowDown,
  Cloud,
  Timer,
  Gauge,
  Trees,
  Landmark,
  Snowflake,
  Download
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import {
  PlanData,
  PlanResponse,
  SafetyIssue,
  HourlyWeather,
  EquipmentItem,
  TransitRoute,
  DrivingRoute,
  WalkingRoute
} from './types';
import {
  calculateWindChill,
  windScaleToSpeed,
  getWindChillRisk,
  getElevationColor
} from './utils/weather';
import { exportToPDF } from './utils/pdf';
import { ElevationChart } from './components/ElevationChart';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

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

const SectionTitle = ({ title, icon: Icon, colorClass = "text-zinc-900" }: { title: string, icon: any, colorClass?: string }) => (
  <div className="flex items-center gap-2 mb-6">
    <div className={cn("p-2 rounded-lg bg-zinc-100", colorClass)}>
      <Icon size={20} />
    </div>
    <h2 className="text-xl font-bold tracking-tight">{title}</h2>
  </div>
);

const Card = ({ children, className, ...props }: { children: React.ReactNode, className?: string } & React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm", className)} {...props}>
    {children}
  </div>
);

const Badge = ({ children, variant = "default" }: { children: React.ReactNode, variant?: 'default' | 'success' | 'warning' | 'error' }) => {
  const variants = {
    default: "bg-zinc-100 text-zinc-600",
    success: "bg-emerald-50 text-emerald-700 border-emerald-100",
    warning: "bg-amber-50 text-amber-700 border-amber-100",
    error: "bg-rose-50 text-rose-700 border-rose-100"
  };
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-medium border", variants[variant])}>
      {children}
    </span>
  );
};

export default function App() {
  const [tripDate, setTripDate] = useState("");
  const [departurePoint, setDeparturePoint] = useState("");
  const [additionalInfo, setAdditionalInfo] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [weatherTab, setWeatherTab] = useState<'overview' | 'hourly'>('overview');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef2 = useRef<HTMLInputElement>(null);
  const mainContentRef = useRef<HTMLDivElement>(null);

  // 新增：线路名称和核心目的地
  const [planTitle, setPlanTitle] = useState("");
  const [destination1, setDestination1] = useState("");
  const [destination2, setDestination2] = useState("");
  const [destination3, setDestination3] = useState("");

  const handleGenerate = async () => {
    // 强拦截逻辑：校验必须字段
    if (!file || !tripDate || !departurePoint) {
      alert("必须选择日期、填写出发点并上传轨迹文件！");
      return;
    }

    // 新增：校验线路名称和至少一个核心目的地
    if (!planTitle.trim()) {
      alert("请输入线路名称！");
      return;
    }

    const destinations = [destination1, destination2, destination3].filter(d => d.trim());
    if (destinations.length === 0) {
      alert("请至少填写一个核心目的地！");
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
      // 新增：传递线路名称和核心目的地
      formData.append('plan_title', planTitle);
      formData.append('key_destinations', destinations.join(','));

      const response = await fetch("/api/generate-plan", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const response_data: PlanResponse = await response.json();
      setPlan(response_data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成策划书失败，请稍后重试");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, ref?: React.RefObject<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      if (ext === 'gpx' || ext === 'kml') {
        setFile(selectedFile);
      } else {
        setError("请选择 GPX 或 KML 格式的文件");
      }
    }
    if (ref?.current) {
      ref.current.value = '';
    }
  };

  const clearFile = (ref?: React.RefObject<HTMLInputElement>) => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (ref?.current) {
      ref.current.value = '';
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

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-zinc-900 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Header */}
      <header className="bg-white border-b border-zinc-200 sticky top-0 z-50">
        {plan === null ? (
          // 初始状态 - 表单输入
          <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col items-center gap-6">
            <div className="text-center space-y-2 mb-4">
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-zinc-900">
                户外出行智能策划
              </h1>
              <p className="text-zinc-500">填写出行信息，AI 为您生成专业的徒步路线策划书</p>
            </div>
            <div className="w-full space-y-4">
              {/* 出行日期 */}
              <div className="flex items-center gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2">
                  <Calendar size={16} /> 出行日期
                </label>
                <input
                  type="date"
                  value={tripDate}
                  onChange={(e) => setTripDate(e.target.value)}
                  required
                  className="flex-1 px-4 py-3 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
              </div>

              {/* 出发地点 */}
              <div className="flex items-center gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2">
                  <MapPin size={16} /> 出发地点
                </label>
                <input
                  type="text"
                  value={departurePoint}
                  onChange={(e) => setDeparturePoint(e.target.value)}
                  placeholder="请输入详细出发地，如：成都市武侯区XX小区"
                  required
                  className="flex-1 px-4 py-3 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
              </div>

              {/* 线路名称（必填） */}
              <div className="flex items-center gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2">
                  <Navigation size={16} /> 线路名称<span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={planTitle}
                  onChange={(e) => setPlanTitle(e.target.value)}
                  placeholder="必填：如「峨眉山金顶环线」"
                  required
                  className="flex-1 px-4 py-3 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
              </div>

              {/* 核心目的地（至少填1个） */}
              <div className="flex items-start gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2 pt-3">
                  <Mountain size={16} /> 核心目的地<span className="text-rose-500">*</span>
                </label>
                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    value={destination1}
                    onChange={(e) => setDestination1(e.target.value)}
                    placeholder="目的地1（必填）：如「峨眉山金顶」"
                    className="w-full px-4 py-2.5 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                    disabled={isLoading}
                  />
                  <input
                    type="text"
                    value={destination2}
                    onChange={(e) => setDestination2(e.target.value)}
                    placeholder="目的地2（可选）：如「万年寺」"
                    className="w-full px-4 py-2.5 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                    disabled={isLoading}
                  />
                  <input
                    type="text"
                    value={destination3}
                    onChange={(e) => setDestination3(e.target.value)}
                    placeholder="目的地3（可选）：如「清音阁」"
                    className="w-full px-4 py-2.5 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                    disabled={isLoading}
                  />
                  <p className="text-xs text-zinc-400">提示：至少填写1个核心目的地，用于搜索相关信息</p>
                </div>
              </div>

              {/* 轨迹文件 */}
              <div className="flex items-center gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2">
                  <MapIcon size={16} /> 轨迹文件
                </label>
                <div className="flex-1 flex items-center gap-3">
                  <div className="relative flex-1">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".gpx,.kml"
                      onChange={(e) => handleFileChange(e, fileInputRef)}
                      className="hidden"
                      disabled={isLoading}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isLoading}
                      className={cn(
                        "w-full px-4 py-3 border border-zinc-200 rounded-xl hover:border-emerald-500 hover:bg-emerald-50 transition-all flex items-center gap-2 text-zinc-600 text-left",
                        isLoading && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <Paperclip size={18} />
                      <span className="text-sm">
                        {file ? file.name : "点击上传 GPX/KML 轨迹文件（必须上传）"}
                      </span>
                    </button>
                    {file && (
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); clearFile(fileInputRef); }}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-zinc-100 rounded"
                      >
                        <X size={16} className="text-zinc-400" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* 补充要求 */}
              <div className="flex items-start gap-3">
                <label className="w-24 text-sm font-bold text-zinc-700 flex items-center gap-2 pt-3">
                  <Info size={16} /> 补充要求
                </label>
                <textarea
                  value={additionalInfo}
                  onChange={(e) => setAdditionalInfo(e.target.value)}
                  placeholder="可选：队伍情况、偏好等..."
                  rows={3}
                  className="flex-1 px-4 py-3 border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all resize-none"
                  disabled={isLoading}
                />
              </div>

              {/* 生成按钮 */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleGenerate}
                  disabled={isLoading}
                  className={cn(
                    "px-8 py-4 bg-emerald-500 text-white rounded-2xl font-bold hover:bg-emerald-600 transition-all flex items-center gap-2 whitespace-nowrap",
                    isLoading && "opacity-70 cursor-not-allowed"
                  )}
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Navigation size={20} />
                      生成智能策划
                    </>
                  )}
                </button>
              </div>
            </div>
            {error && (
              <div className="text-sm text-rose-600 flex items-center gap-2">
                <AlertTriangle size={16} />
                {error}
              </div>
            )}
          </div>
        ) : (
          // 已有策划 - 显示计划信息和快速重新生成
          <div className="max-w-5xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-black tracking-tight">{plan.plan_name}</h1>
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
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                placeholder="补充要求..."
                className="px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent w-48 md:w-64"
                disabled={isLoading}
              />
              <div className="relative">
                <input
                  ref={fileInputRef2}
                  type="file"
                  accept=".gpx,.kml"
                  onChange={(e) => handleFileChange(e, fileInputRef2)}
                  className="hidden"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef2.current?.click()}
                  disabled={isLoading}
                  className={cn(
                    "p-2 border border-zinc-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all text-zinc-600",
                    isLoading && "opacity-50 cursor-not-allowed"
                  )}
                  title="上传 GPX/KML 文件"
                >
                  <Paperclip size={16} />
                </button>
                {file && (
                  <div className="absolute -top-8 left-0 flex items-center gap-1 px-2 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 whitespace-nowrap">
                    <span className="max-w-[80px] truncate">{file.name}</span>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); clearFile(fileInputRef2); }}
                      className="p-0.5 hover:bg-emerald-200 rounded"
                    >
                      <X size={12} />
                    </button>
                  </div>
                )}
              </div>
              <button
                onClick={handleGenerate}
                disabled={isLoading}
                className={cn(
                  "px-4 py-2 bg-emerald-500 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all flex items-center gap-2",
                  isLoading && "opacity-70 cursor-not-allowed"
                )}
              >
                {isLoading ? "生成中..." : "重新生成"}
              </button>
              <button
                onClick={async () => {
                  if (mainContentRef.current && plan) {
                    try {
                      await exportToPDF(mainContentRef.current, plan.plan_name);
                    } catch (err) {
                      console.error('PDF导出错误:', err);
                      alert('PDF导出失败，请查看控制台了解详情');
                    }
                  }
                }}
                className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-sm font-bold hover:bg-zinc-800 transition-colors flex items-center gap-2"
              >
                <Download size={16} /> 导出策划书
              </button>
            </div>
          </div>
        )}
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {isLoading ? (
          // Loading State
          <div className="flex flex-col items-center justify-center py-20 space-y-6">
            <div className="relative">
              <div className="w-20 h-20 border-4 border-zinc-200 rounded-full" />
              <div className="absolute inset-0 w-20 h-20 border-4 border-emerald-500 rounded-full border-t-transparent animate-spin" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-lg font-bold text-zinc-900">Agent 正在分析轨迹与天气数据...</p>
              <p className="text-sm text-zinc-500">这可能需要几秒钟，请稍候</p>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-8 w-full max-w-md">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="h-3 bg-zinc-200 rounded animate-pulse" />
                  <div className="h-2 bg-zinc-100 rounded animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
                </div>
              ))}
            </div>
          </div>
        ) : !plan ? (
          // Empty State - Welcome
          <div className="flex flex-col items-center justify-center py-12 space-y-8">
            <div className="text-center space-y-4 max-w-xl">
              <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto">
                <Tent size={32} className="text-emerald-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-zinc-900 mb-2">欢迎使用户外出行智能策划</h2>
                <p className="text-zinc-500">输入您的出行需求，AI 将为您生成专业的徒步路线策划书，包含天气分析、安全评估和装备建议。</p>
              </div>
            </div>
            <div className="w-full max-w-2xl">
              <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-4 text-center">试试这些示例</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { date: "2024-03-20", departure: "北京市朝阳区", info: "适合新手，难度适中" },
                  { date: "2024-03-21", departure: "上海市浦东新区", info: "2天1夜，看日出" },
                  { date: "2024-03-22", departure: "成都市武侯区", info: "川西小环线，7天行程" },
                  { date: "2024-03-23", departure: "广州市天河区", info: "一日轻徒步，适合老人孩子" }
                ].map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setTripDate(example.date);
                      setDeparturePoint(example.departure);
                      setAdditionalInfo(example.info);
                    }}
                    className="p-4 bg-white border border-zinc-200 rounded-xl text-left hover:border-emerald-500 hover:shadow-md transition-all group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-zinc-100 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                        <span className="text-xs font-bold">{idx + 1}</span>
                      </div>
                      <div>
                        <p className="text-sm text-zinc-600 group-hover:text-zinc-900">{example.departure}</p>
                        <p className="text-xs text-zinc-400 mt-1">{example.date} · {example.info}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : plan && (
          // Data State - Render existing cards
          <div ref={mainContentRef} className="pdf-export-container">
        {/* Track Detail Analysis - 线路详细分析 */}
        {plan.track_detail && (
        <section>
          <SectionTitle title="线路详细分析" icon={Mountain} colorClass="text-emerald-600" />
          <Card>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 核心数据 */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">核心数据</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                    <div className="text-xs text-emerald-600 font-medium mb-1">总里程</div>
                    <div className="text-2xl font-black text-emerald-700">{plan.track_detail.total_distance_km}<span className="text-sm font-normal ml-1">km</span></div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                    <div className="text-xs text-blue-600 font-medium mb-1 flex items-center gap-1"><ArrowUp size={10} />总爬升</div>
                    <div className="text-2xl font-black text-blue-700">{plan.track_detail.total_ascent_m}<span className="text-sm font-normal ml-1">m</span></div>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
                    <div className="text-xs text-amber-600 font-medium mb-1 flex items-center gap-1"><ArrowDown size={10} />总下降</div>
                    <div className="text-2xl font-black text-amber-700">{plan.track_detail.total_descent_m}<span className="text-sm font-normal ml-1">m</span></div>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
                    <div className="text-xs text-rose-600 font-medium mb-1 flex items-center gap-1"><Timer size={10} />预计用时</div>
                    <div className="text-2xl font-black text-rose-700">{plan.track_detail.estimated_duration_hours}<span className="text-sm font-normal ml-1">h</span></div>
                  </div>
                </div>
              </div>

              {/* 海拔数据 */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">海拔数据</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600 flex items-center gap-2"><TrendingUp size={14} className="text-red-400" />最高海拔</span>
                    <span className="text-lg font-bold text-zinc-900">{plan.track_detail.max_elevation_m}m</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600 flex items-center gap-2"><ArrowDown size={14} className="text-blue-400" />最低海拔</span>
                    <span className="text-lg font-bold text-zinc-900">{plan.track_detail.min_elevation_m}m</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600 flex items-center gap-2"><Gauge size={14} className="text-emerald-400" />平均海拔</span>
                    <span className="text-lg font-bold text-zinc-900">{plan.track_detail.avg_elevation_m}m</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 海拔可视化图表 */}
            <div className="mt-6 pt-6 border-t border-zinc-100">
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-4">海拔剖面图</h3>
              <ElevationChart
                points={plan.track_detail.elevation_points || []}
                maxElevation={plan.track_detail.max_elevation_m}
                minElevation={plan.track_detail.min_elevation_m}
                terrainAnalysis={plan.track_detail.terrain_analysis}
                height={140}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              {/* 难度评估 & 云海指数 */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">难度与风险</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600">难度等级</span>
                    <Badge variant={plan.track_detail.difficulty_level === '简单' ? 'success' : plan.track_detail.difficulty_level === '中等' ? 'warning' : 'error'}>
                      {plan.track_detail.difficulty_level}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600">难度评分</span>
                    <span className="text-lg font-bold text-zinc-900">{plan.track_detail.difficulty_score}/100</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <span className="text-sm text-zinc-600">安全风险</span>
                    <Badge variant={plan.track_detail.safety_risk === '低风险' ? 'success' : plan.track_detail.safety_risk === '中等风险' ? 'warning' : 'error'}>
                      {plan.track_detail.safety_risk}
                    </Badge>
                  </div>
                </div>

                {/* 云海指数 */}
                {plan.track_detail.cloud_sea_assessment && (
                  <div className="mt-4 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
                    <div className="flex items-center gap-2 mb-2">
                      <Cloud size={16} className="text-indigo-500" />
                      <span className="text-sm font-bold text-indigo-700">云海指数</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-3xl font-black text-indigo-600">{plan.track_detail.cloud_sea_assessment.score}</div>
                      <div>
                        <div className="text-sm font-bold text-indigo-700">{plan.track_detail.cloud_sea_assessment.level}</div>
                        {plan.track_detail.cloud_sea_assessment.factors.length > 0 && (
                          <div className="text-xs text-indigo-500 mt-1">{plan.track_detail.cloud_sea_assessment.factors.join(' · ')}</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 地形分析 - 大爬升/大下降路段（水平滚动卡片） */}
            {plan.track_detail.terrain_analysis && plan.track_detail.terrain_analysis.length > 0 && (
              <div className="mt-6 pt-6 border-t border-zinc-100">
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-4">关键路段分析</h3>
                <div className="overflow-x-auto pb-2 -mx-2 px-2">
                  <div className="flex gap-4 min-w-max">
                  {plan.track_detail.terrain_analysis.map((segment, idx) => (
                    <div key={idx} className={cn(
                      "p-4 rounded-xl border min-w-[200px] flex-shrink-0",
                      segment.change_type === '大爬升' ? "bg-red-50 border-red-100" : "bg-blue-50 border-blue-100"
                    )}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {segment.change_type === '大爬升' ? (
                            <ArrowUp size={16} className="text-red-500" />
                          ) : (
                            <ArrowDown size={16} className="text-blue-500" />
                          )}
                          <span className="font-bold text-sm">{segment.change_type}</span>
                        </div>
                        <span className="text-xs text-zinc-500">路段 {idx + 1}</span>
                      </div>
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "font-bold text-lg",
                            segment.change_type === '大爬升' ? "text-red-600" : "text-blue-600"
                          )}>
                            {segment.change_type === '大爬升' ? '↑' : '↓'} {segment.elevation_diff}m
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-zinc-600">
                          <span>长度 {segment.distance_m}m</span>
                          <span className={cn(
                            "font-medium",
                            segment.gradient_percent > 20 ? "text-red-600" : segment.gradient_percent > 15 ? "text-amber-600" : "text-zinc-600"
                          )}>
                            坡度 {segment.gradient_percent}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  </div>
                </div>
              </div>
            )}
          </Card>
        </section>
        )}

        {/* Transport Scheme - 交通方案专栏 */}
        {plan.transport_scheme && (
        <section>
          <SectionTitle title="交通方案" icon={MapPin} colorClass="text-amber-600" />
          <div className="space-y-4">
            {/* 路线汇总信息 */}
            {plan.transport_scheme.summary && (
              <Card className="p-4 bg-zinc-50 border-zinc-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-200 rounded-lg">
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
                "p-4 border-l-4",
                plan.transport_scheme.recommended_mode === '驾车' ? "border-l-amber-500 bg-amber-50/50" : "border-l-zinc-300"
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
                  {plan.transport_scheme.recommended_mode === '驾车' && (
                    <span className="px-2 py-1 bg-amber-500 text-white text-xs font-bold rounded-full">推荐</span>
                  )}
                  {plan.transport_scheme.fastest_mode === '驾车' && (
                    <span className="px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">最快</span>
                  )}
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
                {plan.transport_scheme.transit_routes.map((route, idx) => (
                  <Card key={idx} className={cn(
                    "p-4 border-l-4",
                    plan.transport_scheme.recommended_mode === '公交' && idx === 0 ? "border-l-green-500 bg-green-50/50" : "border-l-zinc-300"
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
                          <span className="px-2 py-1 bg-emerald-500 text-white text-xs font-bold rounded-full">最省钱</span>
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
                    {/* 公交段详情 */}
                    {route.segments && route.segments.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-zinc-100">
                        <div className="flex flex-wrap gap-2">
                          {route.segments.map((seg, sidx) => (
                            <div key={sidx} className={cn(
                              "px-3 py-1.5 rounded-full text-xs font-medium",
                              seg.type === 'subway' ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
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

            {/* 步行方案（如果可用且较短） */}
            {plan.transport_scheme.outbound?.walking && plan.transport_scheme.outbound.walking.distance_m < 5000 && (
              <Card className="p-4 border-l-4 border-l-zinc-300">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-100 rounded-lg">
                      <Navigation size={20} className="text-zinc-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-zinc-900">步行</h3>
                      <p className="text-xs text-zinc-500">距离较近可步行</p>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.outbound.walking.distance_m}m</div>
                    <div className="text-xs text-zinc-500">距离</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-zinc-900">{plan.transport_scheme.outbound.walking.duration_min}分钟</div>
                    <div className="text-xs text-zinc-500">预计时间</div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </section>
        )}

        {/* Weather Board */}
        <section>
          <SectionTitle title="动态天气看板" icon={CloudSun} colorClass="text-blue-600" />
          <Card className="p-0 overflow-hidden">
            <div className="flex border-b border-zinc-100">
              <button 
                onClick={() => setWeatherTab('overview')}
                className={cn(
                  "flex-1 py-4 text-sm font-bold transition-colors",
                  weatherTab === 'overview' ? "bg-zinc-50 text-zinc-900 border-b-2 border-zinc-900" : "text-zinc-400 hover:text-zinc-600"
                )}
              >
                详情与格点
              </button>
              <button 
                onClick={() => setWeatherTab('hourly')}
                className={cn(
                  "flex-1 py-4 text-sm font-bold transition-colors",
                  weatherTab === 'hourly' ? "bg-zinc-50 text-zinc-900 border-b-2 border-zinc-900" : "text-zinc-400 hover:text-zinc-600"
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
                        <div className="text-5xl font-black tracking-tighter">{plan.trip_date_weather.tempMax}°<span className="text-zinc-300">/</span>{plan.trip_date_weather.tempMin}°</div>
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
                    <div className="bg-zinc-50 rounded-xl p-4 space-y-3">
                      <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-2">关键节点格点数据</div>
                      {plan.critical_grid_weather.map((grid, idx) => {
                        // 计算风寒指数（仅对最高点计算）
                        const windSpeed = windScaleToSpeed(grid.wind_scale);
                        const windChill = calculateWindChill(grid.temp, windSpeed.avg);
                        const windChillRisk = windChill !== null ? getWindChillRisk(windChill) : null;

                        return (
                          <div key={idx} className={cn(
                            "flex items-center justify-between p-3 rounded-lg border",
                            grid.point_type === '最高点' ? "bg-white border-amber-200 shadow-sm" : "bg-transparent border-zinc-100"
                          )}>
                            <div className="flex items-center gap-2">
                              {grid.point_type === '最高点' ? <TrendingUp size={14} className="text-amber-500" /> : <MapPin size={14} className="text-zinc-400" />}
                              <span className="text-sm font-bold">{grid.point_type}</span>
                            </div>
                            <div className="flex items-center gap-4 text-xs font-mono">
                              <span className="flex items-center gap-1"><Thermometer size={12} /> {grid.temp}°C</span>
                              <span className="flex items-center gap-1"><Wind size={12} /> {grid.wind_scale}</span>
                              <span className="flex items-center gap-1"><Droplets size={12} /> {grid.humidity}%</span>
                              {/* 最高点显示风寒指数 */}
                              {grid.point_type === '最高点' && windChill !== null && (
                                <span className={cn("flex items-center gap-1", windChillRisk?.color)}>
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
                        // 解析时间，支持多种格式
                        let timeLabel = '';
                        if (h.fxTime.includes('T')) {
                          // ISO 格式: 2024-03-15T08:00+08:00
                          const timePart = h.fxTime.split('T')[1];
                          if (timePart) {
                            // 提取 HH:MM
                            timeLabel = timePart.substring(0, 5);
                          }
                        } else {
                          // 其他格式直接使用
                          timeLabel = h.fxTime;
                        }
                        return { ...h, time: timeLabel };
                      })}>
                        <defs>
                          <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
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
                        <YAxis
                          hide
                          domain={['dataMin - 5', 'dataMax + 5']}
                        />
                        <Tooltip
                          contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                          labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
                          formatter={(value: number, name: string) => [`${value}°C`, name]}
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
                    {/* 底部风力降水信息 - 每3小时显示一次 */}
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

        {/* Safety & Emergency */}
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
                    <div className="text-sm font-bold text-rose-900">综合风险定级: {plan.safety_assessment.overall_risk || '未知'}</div>
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
                  {plan.safety_issues.map((issue, idx) => (
                    <div key={idx} className="p-4 border border-zinc-100 rounded-xl hover:border-zinc-200 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-bold text-sm flex items-center gap-2">
                          <div className={cn(
                            "w-2 h-2 rounded-full",
                            issue.severity === '高' ? "bg-rose-500" : issue.severity === '中' ? "bg-amber-500" : "bg-emerald-500"
                          )} />
                          {issue.type}
                        </div>
                        <Badge variant={issue.severity === '高' ? 'error' : issue.severity === '中' ? 'warning' : 'success'}>
                          严重程度: {issue.severity}
                        </Badge>
                      </div>
                      <p className="text-xs text-zinc-600 mb-3 leading-relaxed">{issue.description}</p>
                      <div className="flex items-start gap-2 p-2 bg-zinc-50 rounded-lg text-xs text-zinc-500 italic">
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

        {/* Scenic Spots */}
        <section>
          <SectionTitle title="沿途风光" icon={MapIcon} colorClass="text-indigo-600" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plan.scenic_spots.map((spot, idx) => (
              <Card key={idx} className="group hover:border-indigo-200 transition-all">
                <div className="flex gap-4">
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-colors",
                    spot.spot_type === '自然风光'
                      ? "bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white"
                      : "bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white"
                  )}>
                    {spot.spot_type === '自然风光' ? <Trees size={24} /> : <Landmark size={24} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-bold text-sm">{spot.name}</h4>
                      <span className={cn(
                        "text-[10px] px-2 py-0.5 rounded-full",
                        spot.spot_type === '自然风光'
                          ? "bg-emerald-50 text-emerald-600"
                          : "bg-amber-50 text-amber-600"
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
              <div className="col-span-full p-6 border-2 border-dashed border-zinc-200 rounded-2xl flex flex-col items-center justify-center text-zinc-400 gap-2">
                <MapPin size={24} />
                <span className="text-xs font-medium">沿途风光等待探索...</span>
              </div>
            )}
          </div>
        </section>

        {/* Preparation & Gear */}
        <section>
          <SectionTitle title="行前准备" icon={Backpack} colorClass="text-zinc-900" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <Card>
                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">装备清单</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {plan.equipment_recommendations.map((item, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl border border-zinc-100 hover:border-zinc-200 hover:shadow-sm transition-all group cursor-pointer"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 rounded-lg bg-zinc-50 flex items-center justify-center text-zinc-400 group-hover:bg-emerald-50 group-hover:text-emerald-500 transition-colors">
                          <CheckCircle2 size={16} />
                        </div>
                        <span className="text-[10px] text-zinc-400 bg-zinc-50 px-1.5 py-0.5 rounded">{item.category}</span>
                      </div>
                      <div className="text-sm font-medium">{item.name}</div>
                      {item.description && (
                        <div className="text-[10px] text-zinc-400 mt-1 line-clamp-2">{item.description}</div>
                      )}
                    </div>
                  ))}
                  {plan.equipment_recommendations.length === 0 && (
                    <div className="col-span-full p-6 border-2 border-dashed border-zinc-200 rounded-2xl flex flex-col items-center justify-center text-zinc-400 gap-2">
                      <Backpack size={24} />
                      <span className="text-xs font-medium">装备清单生成中...</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-100">
              <h3 className="text-sm font-bold text-emerald-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                <Navigation size={16} /> 向导建议
              </h3>
              <div className="text-sm text-emerald-800 leading-relaxed whitespace-pre-line">
                {plan.hiking_advice || "暂无向导建议"}
              </div>
              <div className="mt-6 pt-4 border-t border-emerald-200/50 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-emerald-200/50 flex items-center justify-center text-emerald-700">
                  <Tent size={20} />
                </div>
                <div className="text-[10px] text-emerald-600 font-medium">
                  以上建议仅供参考，请根据实际情况灵活调整。
                </div>
              </div>
            </Card>
          </div>
        </section>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="max-w-5xl mx-auto px-4 py-12 border-t border-zinc-200">
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
