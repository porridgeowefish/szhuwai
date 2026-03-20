// 高德地图 JSAPI 2.0 类型声明

declare namespace AMap {
  class Map {
    constructor(container: string | HTMLElement, options?: MapOptions);
    setCenter(center: [number, number] | LngLat): void;
    setZoom(zoom: number): void;
    setFitView(overlays?: Overlay[], immediately?: boolean, avoid?: [number, number, number, number]): void;
    add(overlay: Overlay): void;
    remove(overlay: Overlay): void;
    destroy(): void;
  }

  interface MapOptions {
    zoom?: number;
    center?: [number, number] | LngLat;
    mapStyle?: string;
    viewMode?: '2D' | '3D';
  }

  class LngLat {
    constructor(lng: number, lat: number);
    getLng(): number;
    getLat(): number;
  }

  class Polyline implements Overlay {
    constructor(options: PolylineOptions);
    setPath(path: LngLat[]): void;
  }

  interface PolylineOptions {
    path: LngLat[];
    strokeColor?: string;
    strokeWeight?: number;
    strokeOpacity?: number;
    lineJoin?: string;
    lineCap?: string;
    showDir?: boolean;
  }

  class Marker implements Overlay {
    constructor(options: MarkerOptions);
    setPosition(position: LngLat): void;
    setContent(content: string | HTMLElement): void;
  }

  interface MarkerOptions {
    position: LngLat;
    title?: string;
    content?: string | HTMLElement;
    offset?: [number, number];
  }

  interface Overlay {
    // 空接口，用于类型标记
  }
}

interface Window {
  AMap: typeof AMap;
  _AMapSecurityConfig?: {
    securityJsCode: string;
  };
}
