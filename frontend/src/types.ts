// 与后端 OutdoorActivityPlan schema 完全匹配的类型定义

export interface HourlyWeather {
  fxTime: string;
  temp: number;
  pop: number;
  precip: number;
  windScale: string;
}

export interface SafetyIssue {
  type: string;
  severity: '低' | '中' | '高' | '极高';
  description: string;
  mitigation: string;
  emergencyContact?: string;
}

export interface CityWeatherDaily {
  fxDate: string;
  tempMax: number;
  tempMin: number;
  textDay: string;
  windScaleDay: string;
  windSpeedDay: number;
  humidity: number;
  precip: number;
  pressure: number;
  uvIndex?: number | null;
  vis?: number | null;
  cloud?: number | null;
  sunrise?: string;
  sunset?: string;
}

export interface GridPointWeather {
  pointType: '起点' | '终点' | '最高点' | '中点';
  temp: number;
  windScale: string;
  humidity: number;
}

export interface Point3D {
  lon: number;
  lat: number;
  elevation: number;
}

export interface ScenicSpot {
  name: string;
  spotType: '自然风光' | '人文景观';
  description: string;
  location: Point3D;
}

export interface EquipmentItem {
  name: string;
  category: '服装' | '鞋类' | '背包' | '露营装备' | '炊具' | '安全装备' | '导航工具' | '卫生用品' | '电子产品' | '其他';
  priority: '必需' | '推荐' | '可选';
  quantity: number;
  weightKg?: number;
  description?: string;
  alternatives: string[];
}

export interface ItineraryItem {
  time: string;
  activity: string;
  location?: string;
  durationMinutes?: number;
  notes?: string;
}

export interface SafetyAssessment {
  overallRisk?: '低风险' | '中等风险' | '高风险';
  conditions?: string;
  recommendation?: '推荐' | '谨慎推荐' | '不推荐';
  riskLevel?: '低风险' | '中等风险' | '高风险';
}

export interface EmergencyRescueContact {
  name: string;
  phone: string;
  type?: '医疗' | '救援' | '报警';
}

// 轨迹详细分析相关类型
export interface TerrainSegment {
  changeType: 'large_ascent' | 'large_descent';
  elevationDiff: number;
  distanceM: number;
  gradientPercent: number;
  startDistanceM: number;
}

// 海拔轨迹点（用于前端可视化）
export interface ElevationPoint {
  distanceM: number;
  elevationM: number;
  isKeyPoint: boolean;
  label?: string;
}

export interface CloudSeaAssessment {
  score: number;
  level: string;
  factors: string[];
}

// 轨迹点（GCJ02坐标系，用于高德地图平面图）
export interface TrackPointGCJ02 {
  lng: number;
  lat: number;
  elevation: number;
  isKeyPoint: boolean;
  label?: string;
}

export interface TrackDetailAnalysis {
  totalDistanceKm: number;
  totalAscentM: number;
  totalDescentM: number;
  maxElevationM: number;
  minElevationM: number;
  avgElevationM: number;
  difficultyLevel: string;
  difficultyScore: number;
  estimatedDurationHours: number;
  safetyRisk: string;
  terrainAnalysis: TerrainSegment[];
  elevationPoints: ElevationPoint[];
  trackPointsGcj02?: TrackPointGCJ02[];
  cloudSeaAssessment?: CloudSeaAssessment;
}

// 交通路线相关类型（与后端 transport.py TransportRoutes 模型完全匹配）

// 位置信息（对应后端 LocationInfo）
export interface LocationInfo {
  address: string;
  lat?: number | null;
  lon?: number | null;
  adcode?: string | null;
  city?: string | null;
  province?: string | null;
}

// 路线汇总信息（对应后端 RouteSummary）
export interface RouteSummary {
  totalDistance?: string | null;
  totalTime?: string | null;
  cost?: string | null;
  fastestMode?: string | null;
  cheapestMode?: string | null;
}

// 公交段（对应后端 TransitSegment）
export interface TransitSegment {
  type: string;
  lineName: string;
  lineId?: string | null;
  departureStop: string;
  arrivalStop: string;
  durationMin: number;
  distanceM: number;
  priceYuan: number;
  operator?: string | null;
}

// 公交路线（对应后端 TransitRoute）
export interface TransitRoute {
  available: boolean;
  durationMin: number;
  distanceKm: number;
  costYuan: number;
  walkingDistance: number;
  segments?: TransitSegment[] | null;
  lineName?: string | null;
  departureStop?: string | null;
  arrivalStop?: string | null;
}

// 驾车路线（对应后端 DrivingRoute）
export interface DrivingRoute {
  available: boolean;
  durationMin: number;
  distanceKm: number;
  tollsYuan: number;
  taxiCostYuan?: number | null;
}

// 步行路线（对应后端 WalkingRoute）
export interface WalkingRoute {
  available: boolean;
  durationMin: number;
  distanceM: number;
}

// 去程路线结构（outbound 内部结构）
export interface OutboundRoutes {
  driving?: DrivingRoute | null;
  transit?: TransitRoute | null;
  walking?: WalkingRoute | null;
}

// 综合交通路线（对应后端 TransportRoutes）
export interface TransportScheme {
  origin: LocationInfo;
  destination: LocationInfo;
  outbound: OutboundRoutes;
  returnRoute: Record<string, unknown>;
  summary: RouteSummary;
  recommendedMode?: string | null;
  fastestMode?: string | null;
  cheapestMode?: string | null;
  taxiCostYuan?: number | null;
  transitRoutes?: TransitRoute[] | null;
}

export interface PlanData {
  planId: string;
  createdAt: string;
  planName: string;
  overallRating: '推荐' | '谨慎推荐' | '不推荐';

  trackOverview: string;
  weatherOverview: string;
  transportOverview: string;

  tripDateWeather: CityWeatherDaily;
  hourlyWeather: HourlyWeather[];
  criticalGridWeather: GridPointWeather[];

  itinerary: ItineraryItem[];
  equipmentRecommendations: EquipmentItem[];
  scenicSpots: ScenicSpot[];
  precautions: string[];
  hikingAdvice?: string;

  safetyAssessment: SafetyAssessment;
  safetyIssues: SafetyIssue[];
  riskFactors: string[];
  emergencyRescueContacts: EmergencyRescueContact[];

  trackDetail?: TrackDetailAnalysis;
  transportScheme?: TransportScheme;
}

// API 响应包装类型
export interface PlanResponse {
  success: boolean;
  data: PlanData;
  message?: string;
}
