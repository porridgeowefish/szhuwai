import React, { useState, useEffect, useRef } from 'react';
import {
  Map as MapIcon,
  TrendingUp,
  ArrowUp,
  ArrowDown,
  Timer,
  Gauge,
  Cloud,
  Loader2
} from 'lucide-react';
import { TrackDetailAnalysis, TrackPointGCJ02 } from '../types';
import { ElevationChart } from './ElevationChart';
import { cn } from '../utils/cn';

interface TrackDetailSectionProps {
  trackDetail: TrackDetailAnalysis;
}

/**
 * 线路详情组件
 * - 侧栏切换：平面图 ↔ 海拔剖面图
 * - 平面图：集成高德地图 JSAPI 2.0
 * - 海拔图：保留现有 ElevationChart 逻辑
 */
export const TrackDetailSection: React.FC<TrackDetailSectionProps> = ({
  trackDetail
}) => {
  // 从 trackDetail 获取 GCJ02 轨迹点
  const trackPointsGCJ02 = trackDetail.track_points_gcj02;
  const [activeTab, setActiveTab] = useState<'map' | 'elevation'>('elevation');
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // 使用 ref 管理地图实例和覆盖物
  const mapRef = useRef<AMap.Map | null>(null);
  const polylineRef = useRef<AMap.Polyline | null>(null);
  const markersRef = useRef<AMap.Marker[]>([]);

  // 1. 地图初始化 - 只在 tab 切换到 map 时执行一次
  useEffect(() => {
    if (activeTab !== 'map') return;

    // 检查高德地图 SDK 是否加载
    if (!window.AMap) {
      setMapError('高德地图 SDK 未加载，请在 index.html 中配置有效的 API Key');
      return;
    }

    // 避免重复初始化
    if (mapRef.current) {
      return;
    }

    try {
      // 计算地图中心点：使用第一个轨迹点或默认位置
      const defaultCenter: [number, number] = [103.8, 30.0];
      const center = (trackPointsGCJ02 && trackPointsGCJ02.length > 0)
        ? [trackPointsGCJ02[0].lng, trackPointsGCJ02[0].lat] as [number, number]
        : defaultCenter;

      const map = new window.AMap.Map('track-map-container', {
        zoom: 12,
        center,
        mapStyle: 'amap://styles/whitesmoke',
        viewMode: '2D'
      });

      mapRef.current = map;
      setMapLoaded(true);
    } catch (err) {
      setMapError(err instanceof Error ? err.message : '地图初始化失败');
    }

    // 清理函数 - 组件卸载时销毁地图
    return () => {
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
        setMapLoaded(false);
      }
    };
  }, [activeTab]);

  // 2. 轨迹绘制 - 在地图初始化完成后执行
  useEffect(() => {
    console.log('轨迹绘制 useEffect 触发', {
      hasMap: !!mapRef.current,
      pointsCount: trackPointsGCJ02?.length || 0
    });

    if (!mapRef.current || !trackPointsGCJ02 || trackPointsGCJ02.length === 0) {
      return;
    }

    const map = mapRef.current;

    // 清理旧轨迹和标记
    if (polylineRef.current) {
      map.remove(polylineRef.current);
      polylineRef.current = null;
    }
    markersRef.current.forEach(marker => map.remove(marker));
    markersRef.current = [];

    try {
      // 绘制新轨迹
      const path = trackPointsGCJ02.map(p => new window.AMap.LngLat(p.lng, p.lat));

      const polyline = new window.AMap.Polyline({
        path,
        strokeColor: '#2D5A27',
        strokeWeight: 4,
        strokeOpacity: 0.9,
        lineJoin: 'round',
        lineCap: 'round'
      });

      map.add(polyline);
      polylineRef.current = polyline;

      // 添加关键点标记
      trackPointsGCJ02.forEach(point => {
        if (point.is_key_point) {
          const marker = new window.AMap.Marker({
            position: new window.AMap.LngLat(point.lng, point.lat),
            title: point.label || '关键点',
            content: `<div style="
              background: #dc2626;
              color: white;
              padding: 2px 8px;
              border-radius: 4px;
              font-size: 11px;
              white-space: nowrap;
              box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            ">${point.label || '关键点'}</div>`
          });
          map.add(marker);
          markersRef.current.push(marker);
        }
      });

      // 自适应视野
      map.setFitView();
    } catch (err) {
      console.error('轨迹绘制失败:', err);
    }
  }, [mapLoaded, trackPointsGCJ02]);

  return (
    <div className="rounded-2xl bg-white border border-[var(--stone)] overflow-hidden">
      {/* 切换标签 */}
      <div className="flex border-b border-[var(--stone)]">
        <button
          onClick={() => setActiveTab('elevation')}
          className={cn(
            'flex-1 py-4 px-6 flex items-center justify-center gap-2 text-sm font-semibold transition-all',
            activeTab === 'elevation'
              ? 'bg-[var(--sand)] text-[var(--forest)] border-b-2 border-[var(--forest)]'
              : 'text-zinc-400 hover:text-zinc-600 hover:bg-zinc-50'
          )}
        >
          <TrendingUp size={18} />
          海拔剖面图
        </button>
        <button
          onClick={() => setActiveTab('map')}
          className={cn(
            'flex-1 py-4 px-6 flex items-center justify-center gap-2 text-sm font-semibold transition-all',
            activeTab === 'map'
              ? 'bg-[var(--sand)] text-[var(--forest)] border-b-2 border-[var(--forest)]'
              : 'text-zinc-400 hover:text-zinc-600 hover:bg-zinc-50'
          )}
        >
          <MapIcon size={18} />
          平面轨迹图
        </button>
      </div>

      {/* 内容区 */}
      <div className="p-6">
        {activeTab === 'elevation' ? (
          <div className="space-y-6">
            {/* 海拔图 */}
            <div className="rounded-xl overflow-hidden">
              <ElevationChart
                points={trackDetail.elevation_points || []}
                maxElevation={trackDetail.max_elevation_m}
                minElevation={trackDetail.min_elevation_m}
                terrainAnalysis={trackDetail.terrain_analysis}
                height={180}
              />
            </div>

            {/* 核心数据网格 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <DataCard
                icon={<MapIcon size={16} className="text-[var(--forest)]" />}
                label="总里程"
                value={`${trackDetail.total_distance_km.toFixed(1)} km`}
              />
              <DataCard
                icon={<ArrowUp size={16} className="text-blue-500" />}
                label="累计爬升"
                value={`${trackDetail.total_ascent_m.toFixed(0)} m`}
              />
              <DataCard
                icon={<ArrowDown size={16} className="text-amber-500" />}
                label="累计下降"
                value={`${trackDetail.total_descent_m.toFixed(0)} m`}
              />
              <DataCard
                icon={<Timer size={16} className="text-rose-500" />}
                label="预计用时"
                value={`${trackDetail.estimated_duration_hours.toFixed(1)} h`}
              />
            </div>

            {/* 海拔数据 */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-[var(--sand)] rounded-xl">
              <div className="text-center">
                <div className="text-xs text-zinc-500 mb-1">最高海拔</div>
                <div className="text-lg font-bold text-red-600">{trackDetail.max_elevation_m}m</div>
              </div>
              <div className="text-center border-x border-[var(--stone)]">
                <div className="text-xs text-zinc-500 mb-1">最低海拔</div>
                <div className="text-lg font-bold text-blue-600">{trackDetail.min_elevation_m}m</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-zinc-500 mb-1">平均海拔</div>
                <div className="text-lg font-bold text-[var(--forest)]">{trackDetail.avg_elevation_m}m</div>
              </div>
            </div>

            {/* 难度与云海 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 难度评估 */}
              <div className="p-4 border border-[var(--stone)] rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Gauge size={16} className="text-[var(--earth)]" />
                  <span className="font-semibold text-sm">难度评估</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={cn(
                    'px-3 py-1 rounded-full text-sm font-bold',
                    trackDetail.difficulty_level === '简单' ? 'bg-[var(--forest)]/10 text-[var(--forest)]' :
                    trackDetail.difficulty_level === '中等' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  )}>
                    {trackDetail.difficulty_level}
                  </span>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-zinc-900">{trackDetail.difficulty_score}</span>
                    <span className="text-sm text-zinc-500">/100</span>
                  </div>
                </div>
              </div>

              {/* 云海指数 */}
              {trackDetail.cloud_sea_assessment && (
                <div className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Cloud size={16} className="text-indigo-500" />
                    <span className="font-semibold text-sm text-indigo-700">云海指数</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-3xl font-black text-indigo-600">
                      {trackDetail.cloud_sea_assessment.score}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-indigo-700">
                        {trackDetail.cloud_sea_assessment.level}
                      </div>
                      {trackDetail.cloud_sea_assessment.factors.length > 0 && (
                        <div className="text-xs text-indigo-500 mt-1">
                          {trackDetail.cloud_sea_assessment.factors.join(' · ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 关键路段分析 */}
            {trackDetail.terrain_analysis && trackDetail.terrain_analysis.length > 0 && (
              <div className="pt-4 border-t border-[var(--stone)]">
                <h4 className="text-sm font-semibold text-zinc-700 mb-3">关键路段分析</h4>
                <div className="overflow-x-auto pb-2 -mx-2 px-2">
                  <div className="flex gap-3 min-w-max">
                    {trackDetail.terrain_analysis.map((segment, idx) => (
                      <div
                        key={idx}
                        className={cn(
                          'p-3 rounded-xl border min-w-[180px] flex-shrink-0',
                          segment.change_type === '大爬升'
                            ? 'bg-red-50 border-red-100'
                            : 'bg-blue-50 border-blue-100'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {segment.change_type === '大爬升' ? (
                            <ArrowUp size={14} className="text-red-500" />
                          ) : (
                            <ArrowDown size={14} className="text-blue-500" />
                          )}
                          <span className="text-xs font-bold">{segment.change_type}</span>
                        </div>
                        <div className="text-lg font-bold text-zinc-900">
                          {segment.change_type === '大爬升' ? '↑' : '↓'} {segment.elevation_diff}m
                        </div>
                        <div className="text-xs text-zinc-500 mt-1">
                          长度 {segment.distance_m}m · 坡度 {segment.gradient_percent}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* 平面图容器 */}
            <div
              id="track-map-container"
              className="w-full h-[400px] rounded-xl bg-[var(--sand)] relative overflow-hidden"
            >
              {mapError ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500">
                  <MapIcon size={48} className="mb-4 opacity-30" />
                  <p className="text-sm">{mapError}</p>
                  <p className="text-xs text-zinc-400 mt-2">
                    请在 index.html 中配置有效的高德地图 API Key
                  </p>
                </div>
              ) : !mapLoaded ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500">
                  <Loader2 size={32} className="animate-spin mb-2" />
                  <p className="text-sm">加载地图中...</p>
                </div>
              ) : null}
            </div>

            {/* 图例 */}
            <div className="flex items-center justify-center gap-6 text-xs text-zinc-500">
              <div className="flex items-center gap-2">
                <div className="w-4 h-1 bg-[var(--forest)] rounded" />
                <span>轨迹路线</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span>关键点</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 辅助组件：数据卡片
const DataCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
}> = ({ icon, label, value }) => (
  <div className="p-3 bg-[var(--sand)] rounded-xl">
    <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
      {icon}
      {label}
    </div>
    <div className="text-lg font-bold text-zinc-900">{value}</div>
  </div>
);
