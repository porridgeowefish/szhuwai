import { useEffect, useRef, useState, useCallback } from 'react';

// 高德地图类型定义 - 见 src/types/amap.d.ts

interface AMapInstance {
  map: AMap.Map | null;
  loaded: boolean;
  error: string | null;
}

interface TrackPoint {
  lng: number;
  lat: number;
  elevation?: number;
  label?: string;
  isKeyPoint?: boolean;
}

/**
 * 高德地图初始化 Hook
 * @param containerId 地图容器 DOM ID
 * @param securityKey 高德地图安全密钥（可选）
 */
export function useAmap(containerId: string, securityKey?: string) {
  const [state, setState] = useState<AMapInstance>({
    map: null,
    loaded: false,
    error: null
  });
  const mapRef = useRef<AMap.Map | null>(null);
  const markersRef = useRef<AMap.Marker[]>([]);
  const polylineRef = useRef<AMap.Polyline | null>(null);

  // 初始化地图
  const initMap = useCallback(() => {
    if (!window.AMap) {
      setState(prev => ({ ...prev, error: '高德地图 SDK 未加载' }));
      return;
    }

    const container = document.getElementById(containerId);
    if (!container) {
      setState(prev => ({ ...prev, error: '地图容器不存在' }));
      return;
    }

    try {
      const map = new window.AMap.Map(containerId, {
        zoom: 13,
        center: [103.8, 30.0], // 默认中心点
        mapStyle: 'amap://styles/whitesmoke',
        viewMode: '2D'
      });

      mapRef.current = map;
      setState({ map, loaded: true, error: null });
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : '地图初始化失败'
      }));
    }
  }, [containerId]);

  // 加载高德地图 SDK
  useEffect(() => {
    if (window.AMap) {
      initMap();
      return;
    }

    // 设置安全密钥
    if (securityKey) {
      window._AMapSecurityConfig = {
        securityJsCode: securityKey
      };
    }

    const script = document.createElement('script');
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${securityKey || ''}`;
    script.async = true;
    script.onload = () => {
      initMap();
    };
    script.onerror = () => {
      setState(prev => ({ ...prev, error: '高德地图 SDK 加载失败' }));
    };

    document.head.appendChild(script);

    return () => {
      // 清理地图实例
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
      }
    };
  }, [initMap, securityKey]);

  // 绘制轨迹线
  const drawTrack = useCallback((points: TrackPoint[]) => {
    if (!mapRef.current || !window.AMap || points.length === 0) return;

    // 清除旧轨迹
    if (polylineRef.current) {
      mapRef.current.remove(polylineRef.current);
    }
    markersRef.current.forEach(m => mapRef.current?.remove(m));
    markersRef.current = [];

    // 转换坐标点
    const path = points.map(p => new window.AMap.LngLat(p.lng, p.lat));

    // 绘制轨迹线
    const polyline = new window.AMap.Polyline({
      path,
      strokeColor: '#2D5A27',
      strokeWeight: 4,
      strokeOpacity: 0.9,
      lineJoin: 'round',
      lineCap: 'round',
      showDir: true
    });

    mapRef.current.add(polyline);
    polylineRef.current = polyline;

    // 添加关键点标记
    points.forEach((point, index) => {
      if (point.isKeyPoint) {
        const marker = new window.AMap.Marker({
          position: new window.AMap.LngLat(point.lng, point.lat),
          title: point.label || `点${index + 1}`,
          content: `<div class="amap-marker-content" style="
            background: #dc2626;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          ">${point.label || '关键点'}</div>`
        });
        mapRef.current?.add(marker);
        markersRef.current.push(marker);
      }
    });

    // 自适应视野
    mapRef.current.setFitView([polyline, ...markersRef.current], false, [50, 50, 50, 50]);
  }, []);

  // 设置地图中心和缩放
  const setCenterAndZoom = useCallback((center: [number, number], zoom: number) => {
    if (mapRef.current) {
      mapRef.current.setCenter(center);
      mapRef.current.setZoom(zoom);
    }
  }, []);

  return {
    map: state.map,
    loaded: state.loaded,
    error: state.error,
    drawTrack,
    setCenterAndZoom
  };
}

/**
 * WGS84 坐标转 GCJ02（高德坐标系）
 * 简化版本，实际应用建议使用专业转换库
 */
export function wgs84ToGcj02(lng: number, lat: number): [number, number] {
  const PI = Math.PI;
  const a = 6378245.0;
  const ee = 0.00669342162296594323;

  const transformLat = (x: number, y: number) => {
    let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
    ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
    return ret;
  };

  const transformLng = (x: number, y: number) => {
    let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
    ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
    return ret;
  };

  let dLat = transformLat(lng - 105.0, lat - 35.0);
  let dLng = transformLng(lng - 105.0, lat - 35.0);
  const radLat = lat / 180.0 * PI;
  let magic = Math.sin(radLat);
  magic = 1 - ee * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI);
  dLng = (dLng * 180.0) / (a / sqrtMagic * Math.cos(radLat) * PI);

  return [lng + dLng, lat + dLat];
}
