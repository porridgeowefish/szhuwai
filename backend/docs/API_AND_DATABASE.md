# Outdoor-Agent-Planner 后端 API 接口与数据库文档

> 基础路径: `/api/v1`
> 服务端口: `8000`
> 认证方式: Bearer Token (Authorization: Bearer \<token\>)

---

## 第一部分：API 接口文档

### 统一响应格式

多数接口采用统一包装格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 业务状态码，200 表示成功 |
| message | string | 响应消息 |
| data | object/null | 响应数据，失败时为 null |

#### 错误码对照表

| 错误码 | 说明 |
|--------|------|
| 400001 | 参数错误 |
| 401001 | 未授权，请先登录 |
| 401002 | Token 无效或已过期 |
| 401003 | 缺少 Authorization 头 |
| 403001 | 无权限访问 |
| 403002 | 需要管理员权限 |
| 403003 | 今日额度已用完 |
| 404001 | 资源不存在 |
| 429001 | 请求过于频繁 |
| 500001 | 服务器内部错误 |
| 100001 | 用户不存在 |
| 100002 | 用户名已存在 |
| 100003 | 手机号已被注册 |
| 100004 | 手机号未绑定 |
| 100005 | 密码错误 |
| 100006 | 验证码错误 |
| 100007 | 账号已被禁用 |
| 100008 | 手机号已注册 |
| 100009 | 手机号未注册 |

---

### 1. 认证模块 (auth)

#### 1.1 检查用户名/手机号是否存在

- **路径**: `POST /api/v1/auth/check-exists`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 用户名（3-20字符，与 phone 至少提供一个） |
| phone | string | 否 | 手机号 |

- **响应**:

```json
{
  "code": 200,
  "message": "检查完成",
  "data": {
    "exists": true,
    "field": "username"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.exists | bool | 是否已存在 |
| data.field | string | 检查的字段：username 或 phone |

---

#### 1.2 用户名注册

- **路径**: `POST /api/v1/auth/register`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| username | string | 是 | 3-20字符，字母开头，仅字母数字下划线 | 用户名 |
| password | string | 是 | 6-32字符 | 密码 |

- **响应** (HTTP 201):

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user": {
      "id": 1,
      "username": "hiker01",
      "phone": null,
      "role": "user",
      "status": "active",
      "createdAt": "2026-04-14T10:00:00",
      "updatedAt": "2026-04-14T10:00:00",
      "lastLoginAt": null
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "tokenType": "Bearer",
    "expiresIn": 86400
  }
}
```

---

#### 1.3 用户名登录

- **路径**: `POST /api/v1/auth/login`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

- **响应**:

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "tokenType": "Bearer",
    "expiresIn": 86400,
    "user": {
      "id": 1,
      "username": "hiker01",
      "phone": null,
      "role": "user",
      "status": "active",
      "createdAt": "2026-04-14T10:00:00",
      "updatedAt": "2026-04-14T10:00:00",
      "lastLoginAt": null
    }
  }
}
```

---

#### 1.4 手机号注册

- **路径**: `POST /api/v1/auth/sms/register`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| phone | string | 是 | 中国大陆11位手机号 | 手机号 |
| code | string | 是 | 6位数字 | 短信验证码 |
| password | string | 否 | 6-32字符 | 密码（不设则只能验证码登录） |
| username | string | 否 | 3-20字符 | 用户名 |

- **响应** (HTTP 201): 同 1.2 注册响应结构

---

#### 1.5 手机号登录

- **路径**: `POST /api/v1/auth/sms/login`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| code | string | 是 | 6位验证码 |

- **响应**: 同 1.3 登录响应结构

---

#### 1.6 重置密码

- **路径**: `POST /api/v1/auth/password/reset`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| code | string | 是 | 验证码 |
| new_password | string | 是 | 新密码（6-32字符） |

- **响应**:

```json
{
  "code": 200,
  "message": "密码重置成功",
  "data": null
}
```

---

#### 1.7 获取当前用户信息

- **路径**: `GET /api/v1/auth/me`
- **认证**: 是
- **请求参数**: 无
- **响应**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "username": "hiker01",
    "phone": "138****1234",
    "role": "user",
    "status": "active",
    "createdAt": "2026-04-14T10:00:00",
    "updatedAt": "2026-04-14T10:00:00",
    "lastLoginAt": "2026-04-14T12:00:00"
  }
}
```

---

#### 1.8 绑定手机号

- **路径**: `POST /api/v1/auth/phone/bind`
- **认证**: 是
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 11位手机号 |
| code | string | 是 | 6位验证码 |

- **响应**:

```json
{
  "code": 200,
  "message": "绑定成功",
  "data": {
    "id": 1,
    "username": "hiker01",
    "phone": "13812341234",
    "role": "user",
    "status": "active",
    "createdAt": "2026-04-14T10:00:00",
    "updatedAt": "2026-04-14T10:30:00",
    "lastLoginAt": null
  }
}
```

---

#### 1.9 解绑手机号

- **路径**: `POST /api/v1/auth/phone/unbind`
- **认证**: 是
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 6位验证码 |

- **响应**: 同绑定手机号响应结构

---

#### 1.10 修改密码

- **路径**: `POST /api/v1/auth/password/change`
- **认证**: 是
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码（6-32字符） |

- **响应**:

```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

---

### 2. 短信模块 (sms)

#### 2.1 发送短信验证码

- **路径**: `POST /api/v1/auth/sms/send`
- **认证**: 否
- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号（中国大陆11位，1[3-9]开头） |
| scene | string | 是 | 场景枚举：register / login / bind / unbind / reset_password |

- **响应**:

```json
{
  "code": 200,
  "message": "验证码发送成功",
  "data": {
    "expireIn": 300,
    "cooldown": 60
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.expireIn | int | 验证码有效期（秒） |
| data.cooldown | int | 冷却时间（秒） |

---

### 3. 计划生成模块 (plan)

#### 3.1 生成户外活动计划

- **路径**: `POST /api/v1/plan/generate`
- **认证**: 是
- **请求类型**: `multipart/form-data`
- **请求参数**:

| 字段 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| trip_date | string | Form | 是 | 出行日期 YYYY-MM-DD |
| departure_point | string | Form | 是 | 出发地点 |
| additional_info | string | Form | 否 | 补充信息 |
| file | file | Form | 是 | GPX/KML 轨迹文件（最大 10MB） |
| plan_title | string | Form | 是 | 线路名称/计划书标题 |
| key_destinations | string | Form | 是 | 核心目的地，逗号分隔 |

- **响应**:

```json
{
  "success": true,
  "data": {
    "planId": "plan_20260414_xxxx",
    "createdAt": "2026-04-14T10:00:00",
    "planName": "武功山穿越",
    "overallRating": "推荐",
    "trackOverview": "18km/爬升1200m/困难",
    "weatherOverview": "晴朗，最高28度",
    "transportOverview": "建议驾车，约2小时",
    "tripDateWeather": { "..." : "..." },
    "hourlyWeather": [],
    "criticalGridWeather": [],
    "itinerary": [],
    "equipmentRecommendations": [],
    "scenicSpots": [],
    "precautions": ["注意防晒"],
    "hikingAdvice": "...",
    "safetyAssessment": {
      "overallRisk": "中等风险",
      "conditions": "天气良好，地形有一定挑战",
      "recommendation": "谨慎推荐",
      "riskLevel": "中等风险"
    },
    "safetyIssues": [],
    "riskFactors": [],
    "emergencyRescueContacts": [],
    "trackDetail": { "..." : "..." },
    "transportScheme": { "..." : "..." }
  },
  "message": "计划生成成功",
  "report_id": "661a1b2c3d4e5f6a7b8c9d0e"
}
```

**OutdoorActivityPlan 核心字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| planId | string | 计划ID |
| planName | string | 计划名称 |
| overallRating | string | 总体推荐等级：推荐/谨慎推荐/不推荐 |
| trackOverview | string | 轨迹概述 |
| weatherOverview | string | 天气概述 |
| transportOverview | string | 交通概述 |
| tripDateWeather | CityWeatherDaily | 出行当天天气详情 |
| hourlyWeather | HourlyWeather[] | 逐小时天气预报 |
| criticalGridWeather | GridPointWeather[] | 关键格点天气 |
| itinerary | ItineraryItem[] | 行程安排 |
| equipmentRecommendations | EquipmentItem[] | 装备建议 |
| scenicSpots | ScenicSpot[] | 风景点推荐 |
| precautions | string[] | 注意事项 |
| hikingAdvice | string | 徒步建议 |
| safetyAssessment | SafetyAssessment | 安全评估 |
| safetyIssues | SafetyIssue[] | 安全风险点 |
| emergencyRescueContacts | EmergencyRescueContact[] | 应急救援电话 |
| trackDetail | TrackDetailAnalysis | 轨迹详细分析 |
| transportScheme | TransportRoutes | 交通方案详情 |

**额度不足时响应**:

```json
{
  "detail": {
    "code": 403003,
    "message": "今日额度已用完，剩余 0 次"
  }
}
```

---

### 4. 额度模块 (quota)

#### 4.1 获取今日剩余额度

- **路径**: `GET /api/v1/quota`
- **认证**: 是
- **请求参数**: 无
- **响应**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "used": 2,
    "total": 5,
    "remaining": 3,
    "resetAt": "2026-04-15T00:00:00"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| data.used | int | 今日已使用次数 |
| data.total | int | 总额度（管理员为 -1） |
| data.remaining | int | 剩余额度（管理员为 -1 表示无限） |
| data.resetAt | string | 下次重置时间（明日 0 点） |

---

### 5. 报告模块 (reports)

#### 5.1 获取我的报告列表

- **路径**: `GET /api/v1/reports`
- **认证**: 是
- **请求参数 (Query)**:

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| page | int | 否 | 1 | >= 1 | 页码 |
| page_size | int | 否 | 20 | 1-100 | 每页数量 |

- **响应**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "661a1b2c3d4e5f6a7b8c9d0e",
        "planName": "武功山穿越",
        "tripDate": "2026-04-15",
        "overallRating": "推荐",
        "createdAt": "2026-04-14T10:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 1,
      "totalPages": 1
    }
  }
}
```

---

#### 5.2 获取报告详情

- **路径**: `GET /api/v1/reports/{report_id}`
- **认证**: 是
- **路径参数**:

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID（MongoDB ObjectId） |

- **响应**: 返回完整的报告内容，包含完整的 OutdoorActivityPlan 数据

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "661a1b2c3d4e5f6a7b8c9d0e",
    "planName": "武功山穿越",
    "tripDate": "2026-04-15",
    "overallRating": "推荐",
    "createdAt": "2026-04-14T10:00:00",
    "userId": 1,
    "content": { "完整计划JSON" : "..." }
  }
}
```

---

#### 5.3 删除报告

- **路径**: `DELETE /api/v1/reports/{report_id}`
- **认证**: 是
- **路径参数**:

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | string | 报告ID |

- **响应**:

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 6. 轨迹分析模块 (track)

#### 6.1 解析轨迹文件

- **路径**: `POST /api/v1/track/analyze`
- **认证**: 否
- **请求类型**: `multipart/form-data`
- **请求参数**:

| 字段 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| file | file | Form | 是 | GPX/KML 轨迹文件（最大 10MB） |

- **响应**:

```json
{
  "success": true,
  "data": {
    "totalDistanceKm": 18.5,
    "totalAscentM": 1200,
    "totalDescentM": 1180,
    "maxElevationM": 1918,
    "minElevationM": 680,
    "avgElevationM": 1200,
    "startPoint": { "lat": 27.45, "lon": 114.17, "elevation": 680 },
    "endPoint": { "lat": 27.46, "lon": 114.18, "elevation": 700 },
    "maxElevPoint": { "lat": 27.47, "lon": 114.18, "elevation": 1918 },
    "minElevPoint": { "lat": 27.45, "lon": 114.17, "elevation": 680 },
    "terrainAnalysis": [
      {
        "changeType": "large_ascent",
        "startPoint": { "..." },
        "endPoint": { "..." },
        "startDistanceM": 2000,
        "elevationDiff": 350,
        "distanceM": 800,
        "gradientPercent": 43.75
      }
    ],
    "elevationPoints": [],
    "trackPointsGcj02": [],
    "difficultyScore": 65,
    "difficultyLevel": "困难",
    "estimatedDurationHours": 7.5,
    "safetyRisk": "中等风险",
    "trackName": "武功山穿越",
    "trackPointsCount": 1500,
    "trackCreatedAt": "2026-04-14T08:00:00"
  },
  "track_id": "track_a1b2c3d4e5f6",
  "message": "轨迹解析成功"
}
```

**TrackAnalysisResult 核心字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| totalDistanceKm | float | 总里程（公里） |
| totalAscentM | float | 总累计爬升（米） |
| totalDescentM | float | 总累计下降（米） |
| maxElevationM | float | 最高海拔（米） |
| minElevationM | float | 最低海拔（米） |
| avgElevationM | float | 平均海拔（米） |
| startPoint | Point3D | 起步点 |
| endPoint | Point3D | 终点 |
| maxElevPoint | Point3D | 最高点 |
| minElevPoint | Point3D | 最低点 |
| terrainAnalysis | TerrainChange[] | 大爬升/大下降路段分析 |
| elevationPoints | ElevationPoint[] | 海拔轨迹点（前端可视化） |
| trackPointsGcj02 | TrackPointGCJ02[] | GCJ02 坐标轨迹点（高德地图，最多200点） |
| difficultyScore | float | 难度评分 0-100 |
| difficultyLevel | string | 难度等级：简单/中等/困难/极难 |
| estimatedDurationHours | float | 预计用时（小时） |
| safetyRisk | string | 安全风险：低风险/中等风险/高风险/极高风险 |

---

### 7. 天气查询模块 (weather)

#### 7.1 查询天气

- **路径**: `POST /api/v1/weather/query`
- **认证**: 否
- **请求类型**: `application/x-www-form-urlencoded`
- **请求参数**:

| 字段 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| lon | float | Form | 是 | 经度 |
| lat | float | Form | 是 | 纬度 |
| trip_date | string | Form | 是 | 出行日期 YYYY-MM-DD |

- **响应**:

```json
{
  "success": true,
  "data": {
    "trip_date": "2026-04-15",
    "forecast_days": 3,
    "use_grid": true,
    "max_temp": 28,
    "min_temp": 12,
    "forecast_3d": {
      "location": "114.17,27.45",
      "updateTime": "2026-04-14 08:00:00",
      "daily": [
        {
          "fxDate": "2026-04-15",
          "tempMax": 28,
          "tempMin": 12,
          "textDay": "晴",
          "windScaleDay": "3",
          "windSpeedDay": 15,
          "humidity": 45,
          "precip": 0,
          "pressure": 1013,
          "uvIndex": 6,
          "vis": 25,
          "cloud": 10,
          "sunrise": "06:15",
          "sunset": "18:45"
        }
      ]
    },
    "hourly_24h": {
      "location": "114.17,27.45",
      "updateTime": "2026-04-14 08:00:00",
      "hourly": [
        {
          "fxTime": "2026-04-15T08:00+08:00",
          "temp": 18,
          "pop": 5,
          "precip": 0,
          "windScale": "2"
        }
      ]
    },
    "grid_points": [
      {
        "point_type": "查询点",
        "temp": 22,
        "wind_scale": "3",
        "humidity": 50
      }
    ]
  },
  "message": "天气查询成功"
}
```

**WeatherSummary 核心字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| trip_date | string | 出行日期 |
| forecast_days | int | 预报天数 |
| use_grid | bool | 是否使用格点天气 |
| max_temp | int/null | 最高温度 |
| min_temp | int/null | 最低温度 |
| forecast_3d | CityWeatherResponse | 3天预报 |
| hourly_24h | HourlyWeatherResponse | 24小时逐小时预报 |
| grid_points | array | 多抽样点格点天气 |

---

### 8. 交通规划模块 (transport)

#### 8.1 规划交通路线

- **路径**: `POST /api/v1/transport/plan`
- **认证**: 否
- **请求类型**: `application/x-www-form-urlencoded`
- **请求参数**:

| 字段 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| departure_point | string | Form | 是 | 出发地点名称 |
| destination_lon | float | Form | 是 | 目的地经度 |
| destination_lat | float | Form | 是 | 目的地纬度 |

- **响应**:

```json
{
  "success": true,
  "data": {
    "origin": {
      "address": "长沙火车站",
      "lon": 112.98,
      "lat": 28.19,
      "city": "长沙市",
      "province": "湖南省"
    },
    "destination": {
      "address": "目的地",
      "lon": 114.17,
      "lat": 27.45
    },
    "outbound": {
      "driving": {
        "available": true,
        "duration_min": 120,
        "distance_km": 150.5,
        "tolls_yuan": 60,
        "taxi_cost_yuan": 350
      },
      "transit": {
        "available": true,
        "duration_min": 180,
        "distance_km": 145.0,
        "cost_yuan": 45,
        "walking_distance": 800,
        "segments": []
      }
    },
    "return_route": {},
    "summary": {
      "total_distance": "150.5公里",
      "total_time": "120分钟",
      "cost": "过路费约60元",
      "fastest_mode": "驾车",
      "cheapest_mode": "公交"
    },
    "recommended_mode": "驾车",
    "fastest_mode": "驾车",
    "cheapest_mode": "公交",
    "taxi_cost_yuan": 60,
    "transit_routes": []
  },
  "message": "交通规划成功"
}
```

**TransportRoutes 核心字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| origin | LocationInfo | 起点信息 |
| destination | LocationInfo | 终点信息 |
| outbound | dict | 去程路线（含 driving 和/或 transit） |
| return_route | dict | 返程路线 |
| summary | RouteSummary | 汇总信息 |
| recommended_mode | string | 推荐交通方式 |
| fastest_mode | string | 最快方式 |
| cheapest_mode | string | 最便宜方式 |
| taxi_cost_yuan | int/null | 打车费用 |
| transit_routes | TransitRoute[]/null | 多条公交方案 |

---

### 9. 搜索查询模块 (search)

#### 9.1 执行搜索查询

- **路径**: `POST /api/v1/search/query`
- **认证**: 否
- **请求类型**: `application/x-www-form-urlencoded`
- **请求参数**:

| 字段 | 类型 | 位置 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| keywords | string | Form | 是 | - | 搜索关键词（多个用空格分隔） |
| max_results | int | Form | 否 | 5 | 每组搜索的最大结果数 |

- **响应**:

```json
{
  "success": true,
  "data": [
    {
      "query": "武功山 景点 景区 旅游",
      "results": [
        {
          "title": "武功山风景名胜区",
          "url": "https://...",
          "content": "武功山位于...",
          "score": 0.95,
          "source": "wikipedia.org",
          "source_type": "web",
          "published_date": null,
          "relevance_tags": [],
          "raw_content": null,
          "favicon": null
        }
      ],
      "total_results": 5,
      "search_time": 1.2,
      "sources": ["tavily"]
    }
  ],
  "message": "搜索完成，共 4 组结果"
}
```

系统自动扩展为 4 组搜索查询：
1. `{keywords} 景点 景区 旅游`
2. `{keywords} 户外徒步 应急救援队 报警电话`
3. `{keywords} 徒步攻略 登山路线 注意事项`
4. `{keywords} 徒步装备 登山装备 露营装备推荐`

---

### 10. 用户管理模块 (users)

#### 10.1 获取用户列表（管理员）

- **路径**: `GET /api/v1/users`
- **认证**: 是（管理员）
- **请求参数 (Query)**:

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| page | int | 否 | 1 | >= 1 | 页码 |
| page_size | int | 否 | 20 | 1-100 | 每页数量 |

- **响应**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "username": "admin",
        "phone": "138****1234",
        "role": "admin",
        "status": "active",
        "createdAt": "2026-04-01T10:00:00",
        "lastLoginAt": "2026-04-14T08:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 50,
      "totalPages": 3
    }
  }
}
```

注意：手机号已脱敏（中间四位用 **** 替换）。

---

#### 10.2 更新用户状态（管理员）

- **路径**: `PATCH /api/v1/users/{user_id}/status`
- **认证**: 是（管理员）
- **路径参数**:

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户 ID |

- **请求 Body (JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 用户状态：active / disabled |

- **响应**:

```json
{
  "code": 200,
  "message": "状态更新成功",
  "data": {
    "id": 2,
    "status": "disabled"
  }
}
```

注意：不能禁用自己。

---

### 其他接口

#### 根路径

- **路径**: `GET /`
- **认证**: 否
- **响应**:

```json
{
  "message": "欢迎使用户外活动智能规划系统 API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### 健康检查

- **路径**: `GET /health`
- **认证**: 否
- **响应**:

```json
{
  "status": "healthy"
}
```

---

## 第二部分：数据库设计

### 数据库架构

系统使用双数据库方案：
- **MySQL**: 用户、认证、额度等关系型数据
- **MongoDB**: 报告内容等文档型数据

### 2.1 MySQL 表结构

#### 表: users（用户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 用户 ID |
| username | VARCHAR(50) | UNIQUE, NULLABLE | 用户名 |
| phone | VARCHAR(20) | UNIQUE, NULLABLE | 手机号 |
| password_hash | VARCHAR(255) | NULLABLE | 密码哈希 |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | 角色（user/admin） |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | 状态（active/disabled） |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW(), ON UPDATE NOW() | 更新时间 |
| last_login_at | DATETIME | NULLABLE | 最后登录时间 |
| deleted_at | DATETIME | NULLABLE | 软删除时间 |

**关系**: 一对多 -> quota_usage

---

#### 表: quota_usage（额度使用表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| user_id | INT | FK -> users.id, ON DELETE CASCADE, NOT NULL | 用户 ID |
| usage_date | DATE | NOT NULL | 使用日期 |
| usage_count | INT | NOT NULL, DEFAULT 0 | 使用次数 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW(), ON UPDATE NOW() | 更新时间 |

**唯一约束**: `uk_user_date` (user_id, usage_date) -- 每用户每天只有一条记录

---

#### 表: sms_codes（短信验证码表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| phone | VARCHAR(20) | NOT NULL, INDEX | 手机号 |
| code | VARCHAR(10) | NOT NULL | 验证码 |
| scene | VARCHAR(20) | NOT NULL, INDEX | 场景（register/login/bind/unbind/reset_password） |
| used | INT | NOT NULL, DEFAULT 0 | 是否已使用（0/1） |
| expire_at | DATETIME | NOT NULL, INDEX | 过期时间 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

#### 表: sms_send_logs（短信发送日志表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| phone | VARCHAR(20) | NOT NULL, INDEX | 手机号 |
| scene | VARCHAR(20) | NOT NULL | 场景 |
| ip | VARCHAR(50) | NULLABLE | 请求 IP |
| success | INT | NOT NULL | 是否成功（0/1） |
| error_msg | VARCHAR(255) | NULLABLE | 错误信息 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

### 2.2 MongoDB 集合

#### 集合: reports（报告集合）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | ObjectId | MongoDB 主键 |
| user_id | int | 用户 ID |
| plan_name | string | 计划名称 |
| trip_date | string | 出行日期 |
| overall_rating | string | 总体评分（推荐/谨慎推荐/不推荐） |
| content | object | 完整的计划内容（OutdoorActivityPlan 的 JSON） |
| created_at | datetime | 创建时间 |
| deleted_at | datetime/null | 软删除时间 |

---

### 2.3 表关系图

```
users (1) ──< quota_usage (N)        每用户每天一条额度记录
users (1) ──< reports (N)            每用户多条报告（MongoDB）
users ── sms_codes                    验证码通过 phone 关联
users ── sms_send_logs                发送日志通过 phone 关联
```

### 2.4 索引汇总

| 表 | 索引字段 | 索引类型 | 说明 |
|------|------|------|------|
| users | username | UNIQUE | 用户名唯一 |
| users | phone | UNIQUE | 手机号唯一 |
| quota_usage | (user_id, usage_date) | UNIQUE | 每用户每天唯一 |
| quota_usage | user_id | FK | 外键 |
| sms_codes | phone | INDEX | 按手机号查询 |
| sms_codes | scene | INDEX | 按场景查询 |
| sms_codes | expire_at | INDEX | 按过期时间查询 |
| sms_send_logs | phone | INDEX | 按手机号查询 |
| reports (MongoDB) | user_id | INDEX | 按用户查询 |

---

## 第三部分：配置项

### 环境变量清单

配置通过 `.env` 文件或系统环境变量加载，环境变量名优先级高于 .env 文件。

#### API 密钥

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| QWEATHER_API_KEY | WEATHER_API_KEY | "" | 和风天气 API 密钥 |
| AMAP_API_KEY | MAP_API_KEY | "" | 高德地图 API 密钥 |
| LLM_API_KEY | LLM_API_KEY | "" | 大模型 API 密钥 |
| TAVILY_API_KEY | SEARCH_API_KEY | "" | Tavily 搜索 API 密钥 |

#### API 端点

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| - | WEATHER_BASE_URL | https://devapi.qweatherapi.com/v7 | 和风天气基础 URL |
| WEATHER_DEVELOPER_HOST | WEATHER_DEVELOPER_HOST | devapi | 和风天气开发者主机 |
| - | MAP_BASE_URL | https://restapi.amap.com/v3 | 高德地图基础 URL |
| - | SEARCH_BASE_URL | https://api.tavily.com | Tavily 搜索基础 URL |
| - | LLM_BASE_URL | https://api.siliconflow.cn/v1/chat/completions | 大模型 API URL |

#### LLM 配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| - | LLM_MODEL | Pro/moonshotai/Kimi-K2.5 | 大模型名称 |
| - | LLM_TEMPERATURE | 0.7 | 温度参数（0.0-2.0） |
| - | LLM_MAX_TOKENS | 8192 | 最大输出 token 数 |
| - | LLM_TIMEOUT | 600 | 超时时间（秒） |

#### MySQL 配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| MYSQL_HOST | MYSQL_HOST | localhost | MySQL 主机 |
| MYSQL_PORT | MYSQL_PORT | 3306 | MySQL 端口 |
| MYSQL_USER | MYSQL_USER | root | 用户名 |
| MYSQL_PASSWORD | MYSQL_PASSWORD | "" | 密码 |
| MYSQL_DATABASE | MYSQL_DATABASE | outdoor_planner | 数据库名 |
| MYSQL_POOL_SIZE | MYSQL_POOL_SIZE | 5 | 连接池大小 |

#### MongoDB 配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| MONGO_HOST | MONGO_HOST | localhost | MongoDB 主机 |
| MONGO_PORT | MONGO_PORT | 27017 | MongoDB 端口 |
| MONGO_USER | MONGO_USER | "" | 用户名 |
| MONGO_PASSWORD | MONGO_PASSWORD | "" | 密码 |
| MONGO_DATABASE | MONGO_DATABASE | outdoor_planner | 数据库名 |

#### JWT 配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| - | JWT_SECRET_KEY | change-me-in-production | JWT 签名密钥（生产环境务必修改） |
| - | JWT_ALGORITHM | HS256 | 签名算法 |
| - | JWT_EXPIRE_SECONDS | 86400 | Token 有效期（秒），默认24小时 |

#### 阿里云短信配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| ALIYUN_ACCESS_KEY_ID | ALIYUN_ACCESS_KEY_ID | "" | 阿里云 AccessKey ID |
| ALIYUN_ACCESS_KEY_SECRET | ALIYUN_ACCESS_KEY_SECRET | "" | 阿里云 AccessKey Secret |
| SMS_SIGN_NAME | SMS_SIGN_NAME | 户外规划助手 | 短信签名 |
| SMS_TEMPLATE_REGISTER | SMS_TEMPLATE_REGISTER | "" | 注册模板 ID |
| SMS_TEMPLATE_LOGIN | SMS_TEMPLATE_LOGIN | "" | 登录模板 ID |
| SMS_TEMPLATE_BIND | SMS_TEMPLATE_BIND | "" | 绑定手机模板 ID |
| SMS_TEMPLATE_UNBIND | SMS_TEMPLATE_UNBIND | "" | 解绑手机模板 ID |
| SMS_TEMPLATE_RESET_PASSWORD | SMS_TEMPLATE_RESET_PASSWORD | "" | 重置密码模板 ID |

#### 短信业务配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| - | SMS_CODE_LENGTH | 6 | 验证码长度（4-8） |
| - | SMS_EXPIRE_SECONDS | 300 | 验证码有效期（秒） |
| - | SMS_COOLDOWN_SECONDS | 60 | 发送冷却时间（秒） |
| - | SMS_DAILY_LIMIT | 10 | 每日发送上限 |

#### 通用配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| - | TIMEOUT | 10 | 请求超时（秒） |
| - | RETRY | 3 | 重试次数 |
| - | RATE_LIMIT | 30 | 每分钟请求限制 |
| - | CACHE_TTL | 3600 | 缓存有效期（秒） |
| - | CACHE_MAX_SIZE | 1000 | 缓存最大条目数 |

#### 代理配置

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| PROXY_HTTP | PROXY.http | - | HTTP 代理地址 |
| PROXY_HTTPS | PROXY.https | - | HTTPS 代理地址 |

---

## 第四部分：启动流程

### 启动命令

```bash
uvicorn main:app --reload --port 8000
# 或
python main.py  # 等价于 uvicorn main:app --host 0.0.0.0 --port 8000
```

### 启动逻辑

`main.py` 启动时依次执行：

1. **加载配置**: `api_config = APIConfig.from_env()` 从环境变量和 .env 文件加载配置
2. **创建 FastAPI 应用**: 配置 title/description/version
3. **注册 CORS 中间件**: 允许来自 `localhost:3000` 和 `localhost:5173` 的前端请求
4. **触发 startup 事件**: 按顺序初始化基础设施
   - init_mysql_client -- MySQL 连接池
   - init_jwt_handler -- JWT 处理器
   - init_aliyun_sms_client -- 阿里云短信客户端
   - init_mongo_client -- MongoDB 客户端
   - 每步失败只打 warning 日志，不阻塞启动
5. **注册路由**: 所有路由挂载在 `/api/v1` 前缀下

### 中间件注册顺序

```python
app.add_middleware(CORSMiddleware, ...)  # CORS 中间件
```

| 中间件 | 作用 | 备注 |
|--------|------|------|
| CORSMiddleware | 跨域资源共享 | allow_origins: localhost:3000/5173 |
| AuthMiddleware（可选） | 全局认证检查 | 定义在 middlewares/auth.py，未在 main.py 中启用 |

认证实际通过 FastAPI 依赖注入实现（Depends），而非全局中间件。

### 路由注册

所有路由注册在 `/api/v1` 前缀下：

| 路由模块 | 前缀 | 标签 | 文件 |
|----------|------|------|------|
| track_router | /api/v1/track | 轨迹分析 | src/api/routes/track.py |
| weather_router | /api/v1/weather | 天气查询 | src/api/routes/weather.py |
| transport_router | /api/v1/transport | 交通规划 | src/api/routes/transport.py |
| search_router | /api/v1/search | 搜索查询 | src/api/routes/search.py |
| plan_router | /api/v1/plan | 计划生成 | src/api/routes/plan.py |
| sms_router | /api/v1/auth/sms | 短信 | src/api/routes/sms.py |
| auth_router | /api/v1/auth | 认证 | src/api/routes/auth.py |
| quota_router | /api/v1/quota | 额度 | src/api/routes/quota.py |
| reports_router | /api/v1/reports | 报告 | src/api/routes/reports.py |
| users_router | /api/v1/users | 用户管理 | src/api/routes/users.py |

### 认证机制

认证依赖注入提供三种级别：

| 别名 | 函数 | 说明 |
|------|------|------|
| CurrentUser | get_current_user | 必须登录，否则 401 |
| AdminUser | get_admin_user | 必须登录且为管理员，否则 403 |
| OptionalUser | get_optional_user | 可选登录，未认证返回 None |

Token 通过 HTTP Bearer 方式传递：`Authorization: Bearer <token>`

### API 文档

启动后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
