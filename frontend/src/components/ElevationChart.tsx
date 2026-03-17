import React from 'react';
import { ArrowDown, ArrowUp } from 'lucide-react';
import { TerrainSegment, ElevationPoint } from '../types';

interface ElevationChartProps {
  points: ElevationPoint[];
  maxElevation: number;
  minElevation: number;
  terrainAnalysis?: TerrainSegment[];
  height?: number;
  className?: string;
}

/**
 * 海拔可视化图表
 * - 使用SVG绘制平滑海拔曲线
 * - 绿色代表低海拔，红色代表高海拔
 * - 用小红旗表示关键点位
 * - 大爬升/大下降路段用颜色高亮显示
 */
export const ElevationChart: React.FC<ElevationChartProps> = (props) => {
  const chartHeight = props.height || 140;
  const padding = { top: 20, bottom: 25, left: 5, right: 5 };
  const innerWidth = 100 - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // 计算海拔范围
  const elevationRange = props.maxElevation - props.minElevation || 1;

  // 获取总距离（单位：米）
  const totalDistance = props.points.length > 0
    ? props.points[props.points.length - 1].distance_m
    : 1000;

  // 坐标转换函数（返回百分比坐标）
  const getX = (distance: number): number => {
    return padding.left + (distance / totalDistance) * innerWidth;
  };

  const getY = (elevation: number): number => {
    // Y轴向下为正，海拔越高Y越小
    return padding.top + ((props.maxElevation - elevation) / elevationRange) * innerHeight;
  };

  // 生成SVG曲线路径
  const generatePath = (): string => {
    if (props.points.length === 0) return '';

    // 移动到第一个点
    let path = `M ${getX(props.points[0].distance_m)} ${getY(props.points[0].elevation_m)}`;

    // 使用直线连接各点
    for (let i = 1; i < props.points.length; i++) {
      const curr = props.points[i];
      path += ` L ${getX(curr.distance_m)} ${getY(curr.elevation_m)}`;
    }

    return path;
  };

  // 生成填充区域路径
  const generateAreaPath = (): string => {
    if (props.points.length === 0) return '';

    const linePath = generatePath();
    const lastPoint = props.points[props.points.length - 1];
    const firstPoint = props.points[0];
    const bottomY = chartHeight - padding.bottom;

    return `${linePath} L ${getX(lastPoint.distance_m)} ${bottomY} L ${getX(firstPoint.distance_m)} ${bottomY} Z`;
  };

  // 获取海拔对应的颜色
  const getElevationColor = (elevation: number): string => {
    const ratio = (elevation - props.minElevation) / elevationRange;

    if (ratio < 0.5) {
      const t = ratio * 2;
      const r = Math.round(34 + (234 - 34) * t);
      const g = Math.round(197 + (179 - 197) * t);
      const b = Math.round(94 + (8 - 94) * t);
      return `rgb(${r}, ${g}, ${b})`;
    } else {
      const t = (ratio - 0.5) * 2;
      const r = Math.round(234 + (239 - 234) * t);
      const g = Math.round(179 + (68 - 179) * t);
      const b = Math.round(8 + (68 - 8) * t);
      return `rgb(${r}, ${g}, ${b})`;
    }
  };

  // 生成渐变定义
  const gradientStops = props.points.map((point, index) => {
    const offset = props.points.length > 1 ? (index / (props.points.length - 1)) * 100 : 0;
    return (
      <stop
        key={index}
        offset={`${offset}%`}
        stopColor={getElevationColor(point.elevation_m)}
      />
    );
  });

  // 如果没有数据，显示占位符
  if (props.points.length === 0) {
    return (
      <div className={props.className || ''}>
        <div
          className="relative w-full overflow-hidden rounded-lg bg-zinc-100 flex items-center justify-center"
          style={{ height: `${chartHeight}px` }}
        >
          <span className="text-zinc-400 text-sm">暂无海拔数据</span>
        </div>
      </div>
    );
  }

  // 生成大爬升/大下降段的背景高亮区域
  const renderTerrainHighlights = () => {
    if (!props.terrainAnalysis || props.terrainAnalysis.length === 0) return null;

    return props.terrainAnalysis.map((terrain, index) => {
      // 需要找到终点距离
      const endDistance = terrain.start_distance_m + terrain.distance_m;
      const x1 = getX(terrain.start_distance_m);
      const x2 = getX(endDistance);
      const width = x2 - x1;

      const isAscent = terrain.change_type === '大爬升';
      const color = isAscent ? 'rgba(220, 38, 38, 0.15)' : 'rgba(37, 99, 235, 0.15)';
      const borderColor = isAscent ? 'rgba(220, 38, 38, 0.4)' : 'rgba(37, 99, 235, 0.4)';

      return (
        <g key={index}>
          <rect
            x={x1}
            y={padding.top}
            width={Math.max(width, 1)}
            height={innerHeight}
            fill={color}
          />
          {/* 顶部标记线 */}
          <line
            x1={x1}
            y1={padding.top}
            x2={x1}
            y2={padding.top + innerHeight}
            stroke={borderColor}
            strokeWidth="0.5"
            strokeDasharray="2,2"
          />
          <line
            x1={x2}
            y1={padding.top}
            x2={x2}
            y2={padding.top + innerHeight}
            stroke={borderColor}
            strokeWidth="0.5"
            strokeDasharray="2,2"
          />
        </g>
      );
    });
  };

  // 绘制关键点 - 红色圆点
  const renderKeyPointMarkers = () => {
    return props.points.filter(p => p.is_key_point).map((point, index) => {
      const x = getX(point.distance_m);
      const y = getY(point.elevation_m);

      return (
        <g key={index}>
          {/* 红色实心圆点 */}
          <circle
            cx={x}
            cy={y}
            r="2.5"
            fill="#dc2626"
            stroke="#ffffff"
            strokeWidth="0.8"
          />
        </g>
      );
    });
  };

  return (
    <div className={props.className || ''}>
      <div
        className="relative w-full overflow-hidden rounded-lg bg-gradient-to-b from-zinc-50 to-zinc-100"
        style={{ height: `${chartHeight}px` }}
      >
        {/* SVG 图表 */}
        <svg
          viewBox={`0 0 100 ${chartHeight}`}
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          {/* 渐变定义 */}
          <defs>
            <linearGradient id="elevationGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              {gradientStops}
            </linearGradient>
            <linearGradient id="elevationFill" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="rgba(34, 197, 94, 0.3)" />
              <stop offset="100%" stopColor="rgba(34, 197, 94, 0.05)" />
            </linearGradient>
          </defs>

          {/* 地形变化段高亮背景 */}
          {renderTerrainHighlights()}

          {/* 背景网格线 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
            <line
              key={i}
              x1={padding.left}
              x2={100 - padding.right}
              y1={padding.top + ratio * innerHeight}
              y2={padding.top + ratio * innerHeight}
              stroke="rgba(0,0,0,0.05)"
              strokeWidth="0.3"
              vectorEffect="non-scaling-stroke"
            />
          ))}

          {/* 海拔填充区域 */}
          <path
            d={generateAreaPath()}
            fill="url(#elevationFill)"
          />

          {/* 海拔曲线 */}
          <path
            d={generatePath()}
            fill="none"
            stroke="url(#elevationGradient)"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />

          {/* 关键点 - 红色圆点 */}
          {renderKeyPointMarkers()}
        </svg>

        {/* 关键点标签 - 显示名称和海拔 */}
        <div className="absolute inset-0 pointer-events-none">
          {props.points.filter(p => p.is_key_point).map((point, index) => (
            <div
              key={index}
              className="absolute text-[7px] font-bold text-zinc-700 bg-white/95 px-1 py-0.5 rounded shadow-sm whitespace-nowrap"
              style={{
                left: `${getX(point.distance_m)}%`,
                top: `${(getY(point.elevation_m) / chartHeight) * 100}%`,
                transform: 'translate(-50%, -130%)'
              }}
            >
              {point.label || '关键点'} {point.elevation_m.toFixed(0)}m
            </div>
          ))}
        </div>

        {/* 地形分析标注 - 改到曲线旁边 */}
        {props.terrainAnalysis && props.terrainAnalysis.map((terrain, index) => {
          const startX = getX(terrain.start_distance_m);
          const endX = getX(terrain.start_distance_m + terrain.distance_m);
          const centerX = (startX + endX) / 2;
          const isAscent = terrain.change_type === '大爬升';

          return (
            <div
              key={index}
              className="absolute flex items-center gap-1 px-2 py-1 rounded text-[9px] font-bold whitespace-nowrap shadow-sm pointer-events-auto"
              style={{
                left: `${Math.min(Math.max(centerX, 10), 90)}%`,
                top: '5px',
                transform: 'translateX(-50%)',
                backgroundColor: isAscent ? '#fef2f2' : '#eff6ff',
                color: isAscent ? '#dc2626' : '#2563eb',
                border: `1px solid ${isAscent ? '#fecaca' : '#bfdbfe'}`,
              }}
              title={`${terrain.change_type}: ${terrain.elevation_diff.toFixed(0)}m, 坡度${terrain.gradient_percent.toFixed(1)}%, 距离${terrain.distance_m.toFixed(0)}m`}
            >
              {isAscent ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
              <span>{terrain.elevation_diff.toFixed(0)}m</span>
              <span className="text-[8px] opacity-70">({terrain.distance_m.toFixed(0)}m)</span>
            </div>
          );
        })}

        {/* 距离刻度 - 底部 */}
        <div className="absolute bottom-1 left-0 right-0 flex justify-between text-[7px] text-zinc-400 font-mono px-1">
          <span>0km</span>
          <span>{(totalDistance / 2000).toFixed(1)}km</span>
          <span>{(totalDistance / 1000).toFixed(1)}km</span>
        </div>

        {/* 海拔刻度 - 左侧 */}
        <div className="absolute left-0.5 top-0 bottom-6 flex flex-col justify-between text-[7px] text-zinc-400 font-mono py-1">
          <span>{props.maxElevation}m</span>
          <span>{Math.round((props.maxElevation + props.minElevation) / 2)}m</span>
          <span>{props.minElevation}m</span>
        </div>
      </div>

      {/* 图例 */}
      <div className="flex items-center justify-center gap-4 mt-1.5 text-[9px] text-zinc-500">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-red-600 border border-white" />
          <span>关键点</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2 rounded-sm bg-red-100 border border-red-300" />
          <span>大爬升</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2.5 h-2 rounded-sm bg-blue-100 border border-blue-300" />
          <span>大下降</span>
        </div>
      </div>
    </div>
  );
};