import React from 'react';
import {
  MapPin,
  ArrowUp,
  Clock,
  Gauge,
  TrendingUp,
  Target,
  Flag
} from 'lucide-react';
import { TrackDetailAnalysis } from '../types';
import { cn } from '../utils/cn';

interface RouteBriefProps {
  planName: string;
  trackDetail?: TrackDetailAnalysis;
  overallRating?: '推荐' | '谨慎推荐' | '不推荐';
}

/**
 * 线路简介组件
 * 从 track_detail 提取关键信息生成 20-100 字简介
 */
export const RouteBrief: React.FC<RouteBriefProps> = ({
  planName,
  trackDetail,
  overallRating
}) => {
  if (!trackDetail) {
    return (
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[var(--sand)] to-[var(--stone)] border border-[var(--stone-dark)]">
        <p className="text-zinc-500">暂无线路信息</p>
      </div>
    );
  }

  // 生成简介文案
  const generateBrief = () => {
    const parts: string[] = [];

    // 线路名称
    parts.push(`「${planName}」`);

    // 距离和爬升
    if (trackDetail.total_distance_km) {
      parts.push(`全长${trackDetail.total_distance_km.toFixed(1)}km`);
    }
    if (trackDetail.total_ascent_m) {
      parts.push(`累计爬升${trackDetail.total_ascent_m.toFixed(0)}m`);
    }

    // 难度
    if (trackDetail.difficulty_level) {
      parts.push(`难度${trackDetail.difficulty_level}`);
    }

    // 预计时长
    if (trackDetail.estimated_duration_hours) {
      parts.push(`预计${trackDetail.estimated_duration_hours.toFixed(1)}小时`);
    }

    return parts.join('，') + '。';
  };

  // 获取评级颜色
  const getRatingColor = () => {
    switch (overallRating) {
      case '推荐':
        return 'bg-[var(--forest)] text-white';
      case '谨慎推荐':
        return 'bg-amber-500 text-white';
      case '不推荐':
        return 'bg-red-500 text-white';
      default:
        return 'bg-zinc-100 text-zinc-600';
    }
  };

  // 获取难度颜色
  const getDifficultyColor = (level: string) => {
    switch (level) {
      case '简单':
        return 'text-[var(--forest)] bg-[var(--forest)]/10';
      case '中等':
        return 'text-amber-600 bg-amber-50';
      case '困难':
        return 'text-orange-600 bg-orange-50';
      case '极难':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-zinc-600 bg-zinc-100';
    }
  };

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[var(--sand-light)] to-[var(--sand)] border border-[var(--stone)]">
      {/* 装饰背景 */}
      <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
        <svg viewBox="0 0 100 100" fill="none">
          <path d="M0 100 Q 25 60 50 80 T 100 50" stroke="var(--forest)" strokeWidth="2" fill="none" />
          <path d="M0 80 Q 30 40 60 60 T 100 30" stroke="var(--earth)" strokeWidth="2" fill="none" />
        </svg>
      </div>

      <div className="relative p-6">
        {/* 标题行 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-zinc-900" style={{ fontFamily: 'Playfair Display, serif' }}>
                {planName}
              </h2>
              {overallRating && (
                <span className={cn('px-3 py-1 rounded-full text-xs font-bold', getRatingColor())}>
                  {overallRating}
                </span>
              )}
            </div>
            <p className="text-sm text-zinc-600 leading-relaxed">{generateBrief()}</p>
          </div>
        </div>

        {/* 核心数据卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* 总里程 */}
          <div className="p-3 rounded-xl bg-white/80 border border-[var(--stone)]">
            <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
              <MapPin size={12} className="text-[var(--forest)]" />
              总里程
            </div>
            <div className="text-xl font-bold text-zinc-900">
              {trackDetail.total_distance_km.toFixed(1)}
              <span className="text-sm font-normal text-zinc-500 ml-1">km</span>
            </div>
          </div>

          {/* 累计爬升 */}
          <div className="p-3 rounded-xl bg-white/80 border border-[var(--stone)]">
            <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
              <ArrowUp size={12} className="text-blue-500" />
              累计爬升
            </div>
            <div className="text-xl font-bold text-zinc-900">
              {trackDetail.total_ascent_m.toFixed(0)}
              <span className="text-sm font-normal text-zinc-500 ml-1">m</span>
            </div>
          </div>

          {/* 预计时长 */}
          <div className="p-3 rounded-xl bg-white/80 border border-[var(--stone)]">
            <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
              <Clock size={12} className="text-amber-500" />
              预计时长
            </div>
            <div className="text-xl font-bold text-zinc-900">
              {trackDetail.estimated_duration_hours.toFixed(1)}
              <span className="text-sm font-normal text-zinc-500 ml-1">h</span>
            </div>
          </div>

          {/* 难度等级 */}
          <div className="p-3 rounded-xl bg-white/80 border border-[var(--stone)]">
            <div className="flex items-center gap-2 text-xs text-zinc-500 mb-1">
              <Gauge size={12} className="text-[var(--earth)]" />
              难度等级
            </div>
            <div className={cn('inline-flex px-2 py-0.5 rounded-full text-sm font-bold', getDifficultyColor(trackDetail.difficulty_level))}>
              {trackDetail.difficulty_level}
            </div>
          </div>
        </div>

        {/* 关键点位信息 */}
        <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-[var(--stone)]">
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            <TrendingUp size={14} className="text-red-400" />
            <span>最高点 <strong className="text-zinc-800">{trackDetail.max_elevation_m}m</strong></span>
          </div>
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            <Target size={14} className="text-blue-400" />
            <span>最低点 <strong className="text-zinc-800">{trackDetail.min_elevation_m}m</strong></span>
          </div>
          <div className="flex items-center gap-2 text-sm text-zinc-600">
            <Flag size={14} className="text-[var(--forest)]" />
            <span>平均海拔 <strong className="text-zinc-800">{trackDetail.avg_elevation_m}m</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
