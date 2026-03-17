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
  emergency_contact?: string;
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
  uvIndex?: number | null;  // 格点天气API可能不返回
  vis?: number | null;      // 格点天气API可能不返回
  cloud?: number | null;
  sunrise?: string;
  sunset?: string;
}

export interface GridPointWeather {
  point_type: '起点' | '终点' | '最高点' | '中点';
  temp: number;
  wind_scale: string;
  humidity: number;
}

export interface Point3D {
  lon: number;
  lat: number;
  elevation: number;
}

export interface ScenicSpot {
  name: string;
  spot_type: '自然风光' | '人文景观';
  description: string;
  location: Point3D;
}

export interface EquipmentItem {
  name: string;
  category: '服装' | '鞋类' | '背包' | '露营装备' | '炊具' | '安全装备' | '导航工具' | '卫生用品' | '电子产品' | '其他';
  priority: '必需' | '推荐' | '可选';
  quantity: number;
  weight_kg?: number;
  description?: string;
  alternatives: string[];
}

export interface ItineraryItem {
  time: string;
  activity: string;
  location?: string;
  duration_minutes?: number;
  notes?: string;
}

export interface SafetyAssessment {
  overall_risk?: '低风险' | '中等风险' | '高风险';
  conditions?: string;
  recommendation?: '推荐' | '谨慎推荐' | '不推荐';
  risk_level?: '低风险' | '中等风险' | '高风险';
}

export interface EmergencyRescueContact {
  name: string;
  phone: string;
  type?: '医疗' | '救援' | '报警';
}

// 轨迹详细分析相关类型
export interface TerrainSegment {
  change_type: '大爬升' | '大下降';
  elevation_diff: number;
  distance_m: number;
  gradient_percent: number;
  start_distance_m: number;  // 路段起点累计距离（米）
}

// 海拔轨迹点（用于前端可视化）
export interface ElevationPoint {
  distance_m: number;        // 累计距离（米）
  elevation_m: number;       // 海拔（米）
  is_key_point: boolean;     // 是否为关键点
  label?: string;            // 关键点标签
}

export interface CloudSeaAssessment {
  score: number;
  level: string;
  factors: string[];
}

export interface TrackDetailAnalysis {
  total_distance_km: number;
  total_ascent_m: number;
  total_descent_m: number;
  max_elevation_m: number;
  min_elevation_m: number;
  avg_elevation_m: number;
  difficulty_level: string;
  difficulty_score: number;
  estimated_duration_hours: number;
  safety_risk: string;
  terrain_analysis: TerrainSegment[];
  elevation_points: ElevationPoint[];  // 海拔轨迹点（用于可视化）
  cloud_sea_assessment?: CloudSeaAssessment;
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
  total_distance?: string | null;
  total_time?: string | null;
  cost?: string | null;
  fastest_mode?: string | null;
  cheapest_mode?: string | null;
}

// 公交段（对应后端 TransitSegment）
export interface TransitSegment {
  type: string;           // 交通类型 (subway, bus, walk)
  line_name: string;      // 线路名称
  line_id?: string | null;
  departure_stop: string; // 上车站名称
  arrival_stop: string;   // 下车站名称
  duration_min: number;   // 时长（分钟）
  distance_m: number;     // 距离（米）
  price_yuan: number;     // 价格（元）
  operator?: string | null;
}

// 公交路线（对应后端 TransitRoute）
export interface TransitRoute {
  available: boolean;
  duration_min: number;       // 时长（分钟）
  distance_km: number;        // 距离（公里）
  cost_yuan: number;          // 费用（元）
  walking_distance: number;   // 步行距离（米）
  segments?: TransitSegment[] | null;
  line_name?: string | null;       // 主要线路名称
  departure_stop?: string | null;  // 上车点
  arrival_stop?: string | null;    // 下车点
}

// 驾车路线（对应后端 DrivingRoute）
export interface DrivingRoute {
  available: boolean;
  duration_min: number;       // 时长（分钟）
  distance_km: number;        // 距离（公里）
  tolls_yuan: number;         // 过路费（元）
  taxi_cost_yuan?: number | null;  // 出租车预估费用（元）
}

// 步行路线（对应后端 WalkingRoute）
export interface WalkingRoute {
  available: boolean;
  duration_min: number;  // 时长（分钟）
  distance_m: number;    // 距离（米）
}

// 去程路线结构（outbound 内部结构）
export interface OutboundRoutes {
  driving?: DrivingRoute | null;
  transit?: TransitRoute | null;
  walking?: WalkingRoute | null;
}

// 综合交通路线（对应后端 TransportRoutes - 这是 transport_scheme 的实际类型）
export interface TransportScheme {
  origin: LocationInfo;                       // 起点信息
  destination: LocationInfo;                  // 终点信息
  outbound: OutboundRoutes;                   // 去程路线
  return_route: Record<string, unknown>;      // 返程路线
  summary: RouteSummary;                      // 汇总信息
  recommended_mode?: string | null;           // 推荐交通方式
  fastest_mode?: string | null;               // 最快交通方式
  cheapest_mode?: string | null;              // 最便宜交通方式
  taxi_cost_yuan?: number | null;             // 打车费用预估（元）
  transit_routes?: TransitRoute[] | null;     // 多条公交路线方案
}

export interface PlanData {
  plan_id: string;
  created_at: string;
  plan_name: string;
  overall_rating: '推荐' | '谨慎推荐' | '不推荐';

  track_overview: string;
  weather_overview: string;
  transport_overview: string;

  trip_date_weather: CityWeatherDaily;
  hourly_weather: HourlyWeather[];
  critical_grid_weather: GridPointWeather[];

  itinerary: ItineraryItem[];
  equipment_recommendations: EquipmentItem[];
  scenic_spots: ScenicSpot[];
  precautions: string[];
  hiking_advice?: string;

  safety_assessment: SafetyAssessment;
  safety_issues: SafetyIssue[];
  risk_factors: string[];
  emergency_rescue_contacts: EmergencyRescueContact[];

  track_detail?: TrackDetailAnalysis;
  transport_scheme?: TransportScheme;
}

// API 响应包装类型
export interface PlanResponse {
  success: boolean;
  data: PlanData;
  message?: string;
}
