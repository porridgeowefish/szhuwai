import React, { useState } from 'react';
import { Upload, FileText, MapPin, Mountain, ArrowUp, ArrowDown, Gauge } from 'lucide-react';
import { cn } from '../utils/cn';

const TrackAnalysisPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

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
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    // TODO: 调用轨迹分析 API
    setTimeout(() => {
      setResult({
        distance: '12.5km',
        elevation_gain: '850m',
        elevation_loss: '820m',
        max_elevation: '1850m',
        min_elevation: '1050m',
        estimated_time: '5-6小时',
        difficulty: '中等',
      });
      setAnalyzing(false);
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
          轨迹分析
        </h1>
        <p className="text-sm text-zinc-500 mt-1">上传 GPX/KML 轨迹文件，分析路线信息</p>
      </div>

      <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
        <div className="border-2 border-dashed border-[var(--stone)] rounded-xl p-8 text-center hover:border-[var(--forest)] transition-colors">
          <input
            type="file"
            accept=".gpx,.kml"
            onChange={handleFileChange}
            className="hidden"
            id="track-upload"
          />
          <label htmlFor="track-upload" className="cursor-pointer">
            <Upload size={48} className="mx-auto text-zinc-400 mb-4" />
            <p className="text-zinc-900 font-medium">点击上传或拖拽文件到此处</p>
            <p className="text-sm text-zinc-500 mt-1">支持 GPX、KML 格式</p>
          </label>
          {file && (
            <div className="mt-4 p-3 bg-[var(--sand)] rounded-lg inline-flex items-center gap-2">
              <FileText size={16} className="text-[var(--forest)]" />
              <span className="text-sm font-medium">{file.name}</span>
            </div>
          )}
        </div>

        {file && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className={cn(
              'w-full mt-4 py-3 rounded-xl text-white font-bold btn-forest',
              analyzing && 'opacity-70 cursor-not-allowed'
            )}
          >
            {analyzing ? '分析中...' : '开始分析'}
          </button>
        )}
      </div>

      {result && (
        <div className="bg-white border border-[var(--stone)] rounded-2xl p-6">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Mountain size={20} className="text-[var(--forest)]" />
            分析结果
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-[var(--sand)] rounded-xl">
              <div className="flex items-center gap-2 text-zinc-500 mb-1">
                <MapPin size={16} />
                <span className="text-xs">距离</span>
              </div>
              <div className="text-xl font-bold text-zinc-900">{result.distance}</div>
            </div>
            <div className="p-4 bg-[var(--sand)] rounded-xl">
              <div className="flex items-center gap-2 text-zinc-500 mb-1">
                <ArrowUp size={16} />
                <span className="text-xs">爬升</span>
              </div>
              <div className="text-xl font-bold text-zinc-900">{result.elevation_gain}</div>
            </div>
            <div className="p-4 bg-[var(--sand)] rounded-xl">
              <div className="flex items-center gap-2 text-zinc-500 mb-1">
                <Gauge size={16} />
                <span className="text-xs">难度</span>
              </div>
              <div className="text-xl font-bold text-zinc-900">{result.difficulty}</div>
            </div>
            <div className="p-4 bg-[var(--sand)] rounded-xl">
              <div className="flex items-center gap-2 text-zinc-500 mb-1">
                <Mountain size={16} />
                <span className="text-xs">最高海拔</span>
              </div>
              <div className="text-xl font-bold text-zinc-900">{result.max_elevation}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackAnalysisPage;
