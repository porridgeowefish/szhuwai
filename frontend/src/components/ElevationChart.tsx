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
 * - 使用低饱和山地色带表达海拔变化
 * - 用小节点表示关键点位
 * - 大爬升/大下降路段用细区间带提示，避免整段刺眼标红
 */
export const ElevationChart: React.FC<ElevationChartProps> = (props) => {
  const chartHeight = props.height || 140;
  const padding = { top: 24, bottom: 26, left: 6, right: 4 };
  const innerWidth = 100 - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // 计算海拔范围
  const elevationRange = props.maxElevation - props.minElevation || 1;

  // 获取总距离（单位：米）
  const totalDistance = props.points.length > 0
    ? props.points[props.points.length - 1].distanceM
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
    let path = `M ${getX(props.points[0].distanceM)} ${getY(props.points[0].elevationM)}`;

    // 使用直线连接各点
    for (let i = 1; i < props.points.length; i++) {
      const curr = props.points[i];
      path += ` L ${getX(curr.distanceM)} ${getY(curr.elevationM)}`;
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

    return `${linePath} L ${getX(lastPoint.distanceM)} ${bottomY} L ${getX(firstPoint.distanceM)} ${bottomY} Z`;
  };

  // 获取海拔对应的颜色
  const getElevationColor = (elevation: number): string => {
    const ratio = (elevation - props.minElevation) / elevationRange;

    if (ratio < 0.5) {
      const t = ratio * 2;
      const r = Math.round(21 + (132 - 21) * t);
      const g = Math.round(128 + (148 - 128) * t);
      const b = Math.round(61 + (72 - 61) * t);
      return `rgb(${r}, ${g}, ${b})`;
    } else {
      const t = (ratio - 0.5) * 2;
      const r = Math.round(132 + (154 - 132) * t);
      const g = Math.round(148 + (92 - 148) * t);
      const b = Math.round(72 + (64 - 72) * t);
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
        stopColor={getElevationColor(point.elevationM)}
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
      const endDistance = terrain.startDistanceM + terrain.distanceM;
      const x1 = getX(terrain.startDistanceM);
      const x2 = getX(endDistance);
      const width = x2 - x1;

      const isAscent = terrain.changeType === 'large_ascent';
      const color = isAscent ? 'rgba(245, 158, 11, 0.12)' : 'rgba(14, 165, 233, 0.10)';
      const borderColor = isAscent ? 'rgba(180, 83, 9, 0.45)' : 'rgba(2, 132, 199, 0.38)';

      return (
        <g key={index}>
          <rect
            x={x1}
            y={padding.top}
            width={Math.max(width, 1)}
            height={innerHeight}
            fill={color}
            rx="0.8"
          />
          {/* 顶部标记线 */}
          <line
            x1={x1}
            y1={padding.top}
            x2={x1}
            y2={padding.top + innerHeight}
            stroke={borderColor}
            strokeWidth="0.45"
            strokeDasharray="1.6,2.4"
          />
          <line
            x1={x2}
            y1={padding.top}
            x2={x2}
            y2={padding.top + innerHeight}
            stroke={borderColor}
            strokeWidth="0.45"
            strokeDasharray="1.6,2.4"
          />
        </g>
      );
    });
  };

  // 绘制关键点：用 HTML 固定像素小红点，避免 SVG 横向自适应时 circle 被拉成椭圆。
  const renderKeyPointDots = () => {
    return props.points.filter(p => p.isKeyPoint).map((point, index) => {
      const x = getX(point.distanceM);
      const y = getY(point.elevationM);

      return (
        <span
          key={`${point.distanceM}-${index}`}
          className="pointer-events-auto absolute h-2 w-2 rounded-full border border-white bg-red-500 shadow-[0_0_0_1px_rgba(185,28,28,0.25)]"
          style={{
            left: `${x}%`,
            top: `${(y / chartHeight) * 100}%`,
            transform: 'translate(-50%, -50%)',
          }}
          title={`${point.label || '关键点'} ${point.elevationM.toFixed(0)}m`}
        />
      );
    });
  };

  return (
    <div className={props.className || ''}>
      <div
        className="relative w-full overflow-hidden rounded-lg border border-zinc-200/70 bg-gradient-to-b from-[#f8faf4] to-[#eef1e8]"
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
              <stop offset="55%" stopColor="rgba(132, 148, 72, 0.13)" />
              <stop offset="100%" stopColor="rgba(132, 148, 72, 0.02)" />
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
              stroke="rgba(63,63,70,0.08)"
              strokeWidth="0.25"
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
            strokeWidth="1.15"
            vectorEffect="non-scaling-stroke"
          />
        </svg>

        {/* 关键点固定像素标记 */}
        <div className="absolute inset-0 pointer-events-none">
          {renderKeyPointDots()}
        </div>

        {/* 地形分析标注 - 改到曲线旁边 */}
        {props.terrainAnalysis && props.terrainAnalysis.map((terrain, index) => {
          const startX = getX(terrain.startDistanceM);
          const endX = getX(terrain.startDistanceM + terrain.distanceM);
          const centerX = (startX + endX) / 2;
          const isAscent = terrain.changeType === 'large_ascent';

          return (
            <div
              key={index}
              className="absolute flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold whitespace-nowrap shadow-sm pointer-events-auto"
              style={{
                left: `${Math.min(Math.max(centerX, 10), 90)}%`,
                top: isAscent ? '5px' : '20px',
                transform: 'translateX(-50%)',
                backgroundColor: isAscent ? 'rgba(255, 251, 235, 0.95)' : 'rgba(240, 249, 255, 0.95)',
                color: isAscent ? '#92400e' : '#0369a1',
                border: `1px solid ${isAscent ? '#fde68a' : '#bae6fd'}`,
              }}
              title={`${isAscent ? '大爬升' : '大下降'}: ${terrain.elevationDiff.toFixed(0)}m, 坡度${terrain.gradientPercent.toFixed(1)}%, 距离${terrain.distanceM.toFixed(0)}m`}
            >
              {isAscent ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
              <span>{terrain.elevationDiff.toFixed(0)}m</span>
              <span className="text-[8px] opacity-70">({terrain.distanceM.toFixed(0)}m)</span>
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
          <div className="h-2 w-2 rounded-full border border-white bg-red-500 shadow-[0_0_0_1px_rgba(185,28,28,0.25)]" />
          <span>关键点</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-2 w-3 rounded-sm border border-amber-200 bg-amber-100" />
          <span>爬升区间</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-2 w-3 rounded-sm border border-sky-200 bg-sky-100" />
          <span>下降区间</span>
        </div>
      </div>
    </div>
  );
};
