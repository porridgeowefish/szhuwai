import React, { useRef } from 'react';
import {
  Calendar,
  MapPin,
  Navigation,
  Mountain,
  Paperclip,
  X,
  Info,
  Tent,
  ChevronRight
} from 'lucide-react';
import { cn } from '../utils/cn';

interface HeroSectionProps {
  tripDate: string;
  setTripDate: (v: string) => void;
  departurePoint: string;
  setDeparturePoint: (v: string) => void;
  planTitle: string;
  setPlanTitle: (v: string) => void;
  destination1: string;
  setDestination1: (v: string) => void;
  destination2: string;
  setDestination2: (v: string) => void;
  destination3: string;
  setDestination3: (v: string) => void;
  additionalInfo: string;
  setAdditionalInfo: (v: string) => void;
  file: File | null;
  setFile: (f: File | null) => void;
  isLoading: boolean;
  onGenerate: () => void;
  error: string | null;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  tripDate,
  setTripDate,
  departurePoint,
  setDeparturePoint,
  planTitle,
  setPlanTitle,
  destination1,
  setDestination1,
  destination2,
  setDestination2,
  destination3,
  setDestination3,
  additionalInfo,
  setAdditionalInfo,
  file,
  setFile,
  isLoading,
  onGenerate,
  error
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();
      if (ext === 'gpx' || ext === 'kml') {
        setFile(selectedFile);
      } else {
        alert('请选择 GPX 或 KML 格式的文件');
      }
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const clearFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 示例数据
  const examples = [
    { date: '2026-04-15', departure: '成都市武侯区', title: '峨眉山金顶环线', dest1: '峨眉山金顶', info: '适合周末出行，2天1夜' },
    { date: '2026-05-01', departure: '杭州市西湖区', title: '莫干山徒步', dest1: '莫干山', info: '节假日休闲游' },
    { date: '2026-04-20', departure: '北京市朝阳区', title: '香山植物园', dest1: '香山', info: '一日轻徒步' },
  ];

  const applyExample = (ex: typeof examples[0]) => {
    setTripDate(ex.date);
    setDeparturePoint(ex.departure);
    setPlanTitle(ex.title);
    setDestination1(ex.dest1);
    setAdditionalInfo(ex.info);
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* 背景层 - 山峦渐变 + 噪点纹理 */}
      <div className="absolute inset-0 mountain-gradient" />
      <div className="absolute inset-0 nature-texture opacity-30" />

      {/* 装饰元素 - 模拟远山 */}
      <div className="absolute bottom-0 left-0 right-0 h-1/3">
        <svg viewBox="0 0 1440 320" className="absolute bottom-0 w-full h-auto" preserveAspectRatio="none">
          <path
            fill="#2D5A27"
            fillOpacity="0.4"
            d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,218.7C672,235,768,245,864,234.7C960,224,1056,192,1152,181.3C1248,171,1344,181,1392,186.7L1440,192L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
          <path
            fill="#1E3D1A"
            fillOpacity="0.6"
            d="M0,288L48,272C96,256,192,224,288,213.3C384,203,480,213,576,229.3C672,245,768,267,864,261.3C960,256,1056,224,1152,213.3C1248,203,1344,213,1392,218.7L1440,224L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
        </svg>
      </div>

      {/* 内容层 */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        {/* 标题区 */}
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 mb-4 rounded-full glass text-sm font-medium text-[var(--forest)]">
            <Tent size={16} />
            <span>AI 驱动的智能规划</span>
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg" style={{ fontFamily: 'Playfair Display, serif' }}>
            户外出行智能策划
          </h1>
          <p className="text-lg text-white/80 max-w-xl mx-auto">
            输入轨迹文件，AI 为您生成专业的徒步路线策划书
            <br />
            包含天气分析、安全评估、装备建议
          </p>
        </div>

        {/* 表单卡片 - 玻璃拟态 */}
        <div className="w-full max-w-2xl glass rounded-3xl p-6 md:p-8 shadow-2xl animate-fade-in-up delay-200">
          <div className="space-y-5">
            {/* 行1: 日期 + 出发地 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                  <Calendar size={16} className="text-[var(--forest)]" />
                  出行日期 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={tripDate}
                  onChange={(e) => setTripDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl input-nature text-zinc-800"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                  <MapPin size={16} className="text-[var(--forest)]" />
                  出发地点 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={departurePoint}
                  onChange={(e) => setDeparturePoint(e.target.value)}
                  placeholder="如：成都市武侯区XX小区"
                  className="w-full px-4 py-3 rounded-xl input-nature text-zinc-800 placeholder:text-zinc-400"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* 行2: 线路名称 */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                <Navigation size={16} className="text-[var(--forest)]" />
                线路名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={planTitle}
                onChange={(e) => setPlanTitle(e.target.value)}
                placeholder="如：峨眉山金顶环线"
                className="w-full px-4 py-3 rounded-xl input-nature text-zinc-800 placeholder:text-zinc-400"
                disabled={isLoading}
              />
            </div>

            {/* 行3: 核心目的地 */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                <Mountain size={16} className="text-[var(--forest)]" />
                核心目的地 <span className="text-red-500">*</span>
                <span className="text-xs text-zinc-400 font-normal">（至少填写1个）</span>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  type="text"
                  value={destination1}
                  onChange={(e) => setDestination1(e.target.value)}
                  placeholder="目的地1（必填）"
                  className="w-full px-4 py-2.5 rounded-xl input-nature text-sm text-zinc-800 placeholder:text-zinc-400"
                  disabled={isLoading}
                />
                <input
                  type="text"
                  value={destination2}
                  onChange={(e) => setDestination2(e.target.value)}
                  placeholder="目的地2（可选）"
                  className="w-full px-4 py-2.5 rounded-xl input-nature text-sm text-zinc-800 placeholder:text-zinc-400"
                  disabled={isLoading}
                />
                <input
                  type="text"
                  value={destination3}
                  onChange={(e) => setDestination3(e.target.value)}
                  placeholder="目的地3（可选）"
                  className="w-full px-4 py-2.5 rounded-xl input-nature text-sm text-zinc-800 placeholder:text-zinc-400"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* 行4: 轨迹文件 */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                <Navigation size={16} className="text-[var(--forest)]" />
                轨迹文件 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".gpx,.kml"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className={cn(
                    "w-full px-4 py-3 rounded-xl border-2 border-dashed transition-all flex items-center gap-3",
                    file
                      ? "border-[var(--forest)] bg-[var(--forest)]/5"
                      : "border-[var(--stone-dark)] hover:border-[var(--forest)] hover:bg-[var(--forest)]/5",
                    isLoading && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <Paperclip size={20} className={file ? "text-[var(--forest)]" : "text-zinc-400"} />
                  <span className={cn("text-sm", file ? "text-[var(--forest)] font-medium" : "text-zinc-500")}>
                    {file ? file.name : "点击上传 GPX / KML 轨迹文件"}
                  </span>
                </button>
                {file && (
                  <button
                    type="button"
                    onClick={clearFile}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-red-100 rounded-full transition-colors"
                  >
                    <X size={16} className="text-red-500" />
                  </button>
                )}
              </div>
            </div>

            {/* 行5: 补充要求 */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-semibold text-[var(--earth-dark)]">
                <Info size={16} className="text-[var(--forest)]" />
                补充要求
                <span className="text-xs text-zinc-400 font-normal">（可选）</span>
              </label>
              <textarea
                value={additionalInfo}
                onChange={(e) => setAdditionalInfo(e.target.value)}
                placeholder="队伍情况、特殊需求、偏好等..."
                rows={2}
                className="w-full px-4 py-3 rounded-xl input-nature resize-none text-zinc-800 placeholder:text-zinc-400"
                disabled={isLoading}
              />
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 flex items-center gap-2">
                <X size={16} />
                {error}
              </div>
            )}

            {/* 提交按钮 */}
            <button
              onClick={onGenerate}
              disabled={isLoading}
              className={cn(
                "w-full py-4 rounded-xl text-white font-bold text-lg flex items-center justify-center gap-2 btn-forest",
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

        {/* 示例卡片 */}
        <div className="w-full max-w-2xl mt-8 animate-fade-in-up delay-400">
          <p className="text-sm font-medium text-white/60 mb-3 text-center">试试这些示例</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {examples.map((ex, idx) => (
              <button
                key={idx}
                onClick={() => applyExample(ex)}
                disabled={isLoading}
                className="p-4 rounded-xl glass text-left hover:bg-white/90 transition-all group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-[var(--forest)]/20 flex items-center justify-center text-xs font-bold text-[var(--forest)] group-hover:bg-[var(--forest)] group-hover:text-white transition-colors">
                    {idx + 1}
                  </div>
                  <span className="font-semibold text-sm text-zinc-800">{ex.title}</span>
                </div>
                <p className="text-xs text-zinc-500">{ex.departure}</p>
                <p className="text-xs text-zinc-400 mt-1">{ex.info}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 底部图例 */}
        <div className="absolute bottom-4 left-4 right-4 flex justify-center gap-6 text-xs text-white/50">
          <span>🏔️ 支持GPX/KML轨迹</span>
          <span>🌤️ 实时天气分析</span>
          <span>🛡️ 安全评估</span>
          <span>🎒 装备建议</span>
        </div>
      </div>
    </div>
  );
};
