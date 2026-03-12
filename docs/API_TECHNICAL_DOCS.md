# 户外活动智能规划系统 - API 技术文档

本文档包含所有 API 的技术说明、数据模型定义和使用示例。

详细的项目文档请参考：[根目录 README.md](../README.md)

## 目录

- [架构设计](#架构设计)
- [天气 API](#和风天气API)
- [地图 API](#高德地图API)
- [搜索 API](#Tavily搜索API)

## 架构设计

### 分层架构

系统采用分层架构，确保职责清晰：

```
┌─────────────────────────────────────────┐
│              Presentation               │
│          (example_usage.py)             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Services Layer                │
│  services/weather_analyzer.py           │
│  - 业务逻辑：云海概率计算               │
│  - 安全熔断检查                         │
│  - 风险评估                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           API Client Layer              │
│  api/weather_client.py                  │
│  - HTTP 请求                            │
│  - 数据反序列化                         │
│  - 错误处理                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           External APIs                 │
│  - 和风天气 API                         │
│  - 高德地图 API                         │
│  - Tavily 搜索 API                      │
└─────────────────────────────────────────┘
```

### 职责分离

- **API Client** (`api/`): 仅负责数据获取和反序列化，返回 Pydantic 模型
- **Services** (`services/`): 消费模型，进行业务运算（云海概率、安全检查等）
- **Schemas** (`schemas/`): 数据模型定义

### 使用示例

```python
from api.weather_client import WeatherClient
from services.weather_analyzer import WeatherAnalyzer
from api.config import APIConfig

# 1. 获取数据（API Client）
config = APIConfig.from_env()
weather_client = WeatherClient(config)
city_forecast = weather_client.get_weather_3d("Beijing")
summit_forecast = weather_client.get_grid_weather_3d(116.23, 39.54)

# 2. 业务分析（Services）
analyzer = WeatherAnalyzer()
cloud_sea = analyzer.calculate_cloud_sea_probability(
    city_forecast.daily[0],
    summit_forecast.daily[0]
)
safety = analyzer.check_weather_safety(
    city_forecast.daily,
    summit_forecast.daily
)
```

## 天气 API

### API 概述

和风天气 API 提供实时天气、预报、格点天气等多种天气数据服务。

### API 端点

- **基础 URL**: `https://p25khw5ygp.re.qweatherapi.com/v7/`
- **认证方式**: `X-QW-Api-Key` 请求头
- **开发者主机**: `devapi` (开发环境) / 商业主机

### 常用接口

#### 1. 城市 3 天预报

**端点**: `/weather/3d`
**参数**:
- `location`: 位置参数（支持城市名或 LocationID）
- `lang`: 语言 (默认: `zh`)

**请求示例**:
```bash
curl -H "X-QW-Api-Key: YOUR_KEY" \
  "https://p25khw5ygp.re.qweatherapi.com/v7/weather/3d?location=Beijing&lang=zh"
```

**响应字段** (`daily[]`):
| 字段 | 类型 | 描述 |
|------|------|------|
| `fxDate` | string | 日期 YYYY-MM-DD |
| `tempMax` | float | 最高温度 (℃) |
| `tempMin` | float | 最低温度 (℃) |
| `textDay` | string | 白天天气描述 |
| `windScaleDay` | string | 白天风力等级 |
| `humidity` | int | 湿度 (%) |
| `precip` | float | 降水量 (mm) |
| `pop` | int | 降水概率 (%) |
| `uvIndex` | int | UV指数 |
| `visibility` | int | 能见度 (km) |

#### 2. 城市 7 天预报

**端点**: `/weather/7d`
**参数**: 与 3 天预报相同

#### 3. 逐小时预报

**端点**: `/weather/24h`
**参数**:
- `location`: 位置
- `hours`: 小时数 (默认: 24h)

**响应字段** (`hourly[]`):
| 字段 | 类型 | 描述 |
|------|------|------|
| `fxTime` | string | 时间 YYYY-MM-DD HH:mm |
| `temp` | float | 温度 (℃) |
| `pop` | int | 降水概率 (%) |
| `windScale` | string | 风力等级 |

#### 4. 格点天气预报

**端点**: `/grid-weather/3d`
**参数**:
- `location`: `lon,lat` (经纬度坐标，英文逗号分隔)
- `lang`: 语言 (默认: `zh`)

**位置参数格式**:

和风天气 API 的 `location` 参数支持三种格式：

1. **LocationID**（推荐）
   - 通过 GeoAPI 城市搜索接口获取
   - 端点: `https://dev.qweather.com/docs/api/geoapi/city-lookup/`

2. **经纬度坐标**
   - 格式：`lon,lat`
   - 示例：`116.41,39.92`

3. **城市名称**
   - 示例：`北京`、`上海`

**注意**: 使用中文名称可能无法正确解析，建议使用英文城市名或坐标。

### 数据模型

#### WeatherDaily

```python
from schemas.weather import WeatherDaily

weather = WeatherDaily(
    fxDate="2024-03-15",
    tempMax=25.5,
    tempMin=15.2,
    textDay="晴",
    textNight="晴",
    windScaleDay="3",
    windScaleNight="2",
    humidity=65,
    precipitation=0,
    pop=10,
    uvIndex=6,
    visibility=20
)
```

#### WeatherSummary

```python
from schemas.weather import WeatherSummary

summary = WeatherSummary(
    trip_date="2024-03-15",
    forecast_days=3,
    use_grid=True,
    max_temp=25,
    min_temp=15,
    safe_for_outdoor=True
)
```

### 使用示例

```python
from api.weather_client import WeatherClient

client = WeatherClient()

# 获取 3 天预报
forecast = client.get_weather_3d("Beijing")
print(f"预报天数: {len(forecast.daily)}")
print(f"更新时间: {forecast.updateTime}")

# 获取逐小时预报
hourly = client.get_hourly_weather("Beijing", hours=12)
print(f"小时数据点: {len(hourly.hourly)}")

# 获取格点天气（山区天气）
grid = client.get_grid_weather_3d(116.23, 39.54)
```

---

## 地图 API

### API 概述

高德地图 API 提供地理编码、路径规划、POI 搜索等地图服务。

### API 端点

- **基础 URL**: `https://restapi.amap.com/v3`
- **认证方式**: `key` 查询参数

### 常用接口

#### 1. 地理编码

**端点**: `/geocode/geo`
**参数**:
- `address`: 地址
- `city`: 城市（可选）
- `key`: API 密钥
- `output`: 返回格式 (`JSON` 或 `XML`)

**响应字段** (`geocodes[0]`):
| 字段 | 类型 | 描述 |
|------|------|------|
| `formatted_address` | string | 完整地址 |
| `province` | string | 省份 |
| `city` | string | 城市 |
| `district` | string | 区县 |
| `adcode` | string | 行政区划代码 |
| `location` | string | 坐标 `lon,lat` |

#### 2. 路径规划

**驾车路径规划** (`/direction/driving`)
- `walking` | `/direction/walking`
- `transit` | `/direction/transit/integrated`)

**参数**:
- `origin`: 起点（经纬度坐标）
- `destination`: 终点
- `strategy`: 策略（`LEAST_TIME`, `LEAST_FEE`, `LEAST_DISTANCE`, `RECOMMENDED`）
- `extensions`: `base`, `all`, `traffic`

**DrivingRoute 响应字段**:
| 字段 | 类型 | 描述 |
|------|------|------|
| `distance_km` | float | 距离（公里） |
| `duration_min` | int | 用时（分钟） |
| `tolls_yuan` | int | 路费（元） |
| `traffic_lights` | int | 红绿灯数量 |
| `steps` | list | 导航步骤 |

#### 3. 逆地理编码

**端点**: `/geocode/regeo`
**参数**:
- `location`: 坐标
- `extensions`: `base`, `all`

### 数据模型

#### GeocodeResult

```python
from schemas.transport import GeocodeResult

geo = GeocodeResult(
    address="北京市朝阳区",
    province="北京市",
    city="北京市",
    district="朝阳区",
    adcode="110105",
    lon=116.487,
    lat=39.982
)

# 转换为 Point3D
point = geo.to_point3d(elevation=50)
```

#### DrivingRoute

```python
from schemas.transport import DrivingRoute, RouteStep

route = DrivingRoute(
    available=True,
    duration_min=30,
    distance_km=15.5,
    tolls_yuan=10,
    traffic_lights=5,
    steps=[
        RouteStep(
            instruction="向右转",
            distance=50,
            duration=30,
            action="turn"
        )
    ]
)
```

### 使用示例

```python
from api.map_client import MapClient

client = MapClient()

# 地理编码
geo = client.geocode("北京市朝阳区")
print(f"地址: {geo.address}")
print(f"坐标: ({geo.lon}, {geo.lat})")

# 驾车路线规划
route = client.driving_route(
    "116.404,39.915",  # 北京
    "116.196,39.917"   # 上海
    strategy="LEAST_TIME"
)

print(f"距离: {route.distance_km} 公里")
print(f"用时: {route.duration_min} 分钟")
```

---

## 搜索 API

### API 概述

Tavily API 提供强大的网络搜索能力，支持多种搜索类型。

### API 端点

- **基础 URL**: `https://api.tavily.com`
- **认证方式**: `Authorization: Bearer {API_KEY}` 请求头

### 常用接口

#### 网络搜索

**端点**: `/search`
**参数**:
- `query`: 搜索关键词
- `max_results`: 最大结果数（默认: 10）
- `search_depth`: 搜索深度（默认: `basic`）
- `days`: 搜索天数（可选）

**响应字段**:
| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | 标题 |
| `url` | string | 链接 |
| `content` | string | 内容摘要 |
| `score` | float | 相关度评分 (0-1) |
| `published_date` | string | 发布日期 |
| `source` | string | 来源网站 |

### 数据模型

#### SearchResult

```python
from schemas.search import SearchResult

result = SearchResult(
    title="香山徒步路线",
    url="https://example.com",
    content="香山是北京著名的...",
    score=0.85,
    source="hiking.com"
)
```

### 使用示例

```python
from api.search_client import SearchClient

client = SearchClient()

# 网络搜索
results = client.search("北京 徒步 路线", max_results=5)
print(f"找到 {results.total_results} 条结果")

for result in results.results[:3]:
    print(f"\n标题: {result.title}")
    print(f"链接: {result.url}")
    print(f"来源: {result.source}")
```

---

## 测试说明

### 测试文件组织

项目使用 `pytest` 进行单元测试和集成测试。

#### 测试目录结构

```
test/
├── __init__.py
├── conftest.py          # pytest 配置和夹具
├── pytest.ini          # pytest 配置文件
├── schemas/           # 数据模型测试
│   └── test_models.py
├── api/               # API 客户端测试
│   ├── test_clients.py
│   ├── test_map.py
│   └── test_search.py
├── integration/        # 集成测试
│   └── test_workflow.py
└── test_all_apis_simple.py  # 简单 API 连通测试
```

#### 运行测试

```bash
# 运行所有测试
pytest test/ -v

# 运行特定测试
pytest test/schemas/ -v      # 数据模型
pytest test/api/ -v         # API 客户端
pytest test/integration/ -v # 集成测试

# 跳过慢速测试
pytest test/ -v -m "not slow"
```

#### 测试配置

`test/pytest.ini` 已配置：
- 排除临时测试文件 (`test_*.py`)
- 跳过 `integration` marker 的测试（CI 中不调用）

### API 连通测试

`test/test_all_apis_simple.py` 是手动验证 API 连通性的独立脚本。

---

## 配置说明

### 环境变量

| 变量名 | 说明 |
|------|------|
| `QWEATHER_API_KEY` | 和风天气 API 密钥 |
| `WEATHER_DEVELOPER_HOST` | 开发者主机 (默认: `devapi`) |
| `AMAP_API_KEY` | 高德地图 API 密钥 |
| `LLM_API_KEY` | LLM API 密钥 |
| `TAVILY_API_KEY` | 搜索 API 密钥 |
| `PROXY_HTTP` | HTTP 代理地址 |
| `PROXY_HTTPS` | HTTPS 代理地址 |
| `API_TIMEOUT` | API 超时（秒，默认: 10） |
| `API_RETRY` | 重试次数（默认: 3） |
| `API_RATE_LIMIT` | 每分钟请求限制（默认: 30） |

---

## 常见问题

### 1. 天气 API 返回 400 Invalid Parameter

**原因**: `location` 参数格式不正确

**解决方案**:
- 使用经纬度坐标格式：`lon,lat`（英文逗号分隔）
- 或使用 LocationID
- 示例：`location="116.0579,22.5431"`

### 2. 地图 API 返回 440300 错误

**原因**: API 密钥无效或 IP 白名单问题

**解决方案**:
- 检查 API 密钥是否正确
- 检查 IP 是否在白名单中

### 3. 搜索 API 连接失败

**原因**: 网络问题或 API 密钥无效

**解决方案**:
- 检查网络连接
- 检查代理设置

---

---

## 测试说明

### 测试文件组织

项目使用 `pytest` 进行单元测试和集成测试。

#### 测试目录结构

```
test/
├── __init__.py
├── conftest.py          # pytest 配置和夹具
├── pytest.ini          # pytest 配置文件
├── schemas/           # 数据模型测试
│   └── test_models.py
├── api/               # API 客户端测试
│   ├── test_clients.py
│   ├── test_map.py
│   └── test_search.py
├── integration/        # 集成测试
│   └── test_workflow.py
└── test_all_apis_simple.py  # 简单 API 连通测试
```

#### 运行测试

```bash
# 运行所有测试
pytest test/ -v

# 运行特定测试
pytest test/schemas/ -v      # 数据模型
pytest test/api/ -v         # API 客户端
pytest test/integration/ -v # 集成测试

# 跳过慢速测试
pytest test/ -v -m "not slow"
```

#### 测试配置

`test/pytest.ini` 已配置：
- 排除临时测试文件 (`test_*.py`)
- 跳过 `integration` marker 的测试（CI 中不调用）

### API 连通测试

`test/test_all_apis_simple.py` 是手动验证 API 连通性的独立脚本。

### 执行的操作

#### 1. 创建目录结构
```
03_Code/
├── docs/              # 所有 MD 文档归档
│   ├── README_schemas.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── QUICKSTART.md
│   └── WEATHER_API_UPDATE_SUMMARY.md
├── test/               # 测试文件
│   ├── __init__.py
│   ├── conftest.py
│   ├── pytest.ini
│   ├── schemas/
│   ├── api/
│   └── integration/
```

#### 2. 清理冗余文件

已删除的临时测试文件：
- `test_*.py` (临时调试文件)
- `simple_test*.py` (临时调试文件)
- `debug_*.py` (临时调试文件)
- `api_requests.log` (临时日志)
- `errors.log` (临时日志)

保留的测试文件：
- `test/test_all_apis_simple.py` - 简单 API 连通测试
- `test/conftest.py` - pytest 配置
- `test/pytest.ini` - pytest 配置
- `test/schemas/test_models.py` - 数据模型测试
- `test/api/test_*.py` - API 客户端测试

#### 3. 文件整理说明

| 原位置 | 新位置 | 说明 |
|----------|--------|------|
| README_schemas.md | docs/README_schemas.md | API 契约和数据模型文档 |
| IMPLEMENTATION_SUMMARY.md | docs/IMPLEMENTATION_SUMMARY.md | 实现总结文档 |
| QUICKSTART.md | docs/QUICKSTART.md | 快速开始指南 |
| WEATHER_API_UPDATE_SUMMARY.md | docs/WEATHER_API_UPDATE_SUMMARY.md | 天气 API 更新总结 |

| test_schemas.py | test/schemas/test_models.py | 已移到 test/schemas/ |
| test_api.py | test/api/test_clients.py | 已移到 test/api/ |
| test_new_weather_api.py | test/api/test_weather.py | 已移到 test/api/ |

#### 4. pytest 配置

`test/pytest.ini` 已配置：
- 排除临时测试文件 (`test_*.py`)
- 标记集成测试 (`integration` marker）
- 标记需要 API 密钥的测试 (`api` marker)
- 标记慢速测试 (`slow` marker)

#### 5. CI 流程建议

测试文件不会被 CI 流程调用：
- `test/test_all_apis_simple.py` 是手动 API 连通测试
- CI 应该只运行 `pytest test/` 下的正式测试

CI 运行命令：
```bash
# 只运行正式测试，跳过慢速测试
pytest test/ -m "not slow" -v

# 运行所有测试
pytest test/ -v

# 运行带覆盖率的测试
pytest test/ --cov=schemas --cov=api --cov-report=html
```

#### 6. API 测试结果

通过简单测试验证的 API 状态：

| API | 状态 | 说明 |
|-----|------|------|
| 和风天气 | ✅ PASS | 3天/7天/逐小时预报正常 |
| 高德地图 | ✅ PASS | 地理编码、路线规划正常 |
| Tavily 搜索 | ✅ PASS | 搜索功能正常 |
| SiliconFlow LLM | ⚠️ PASS | API 调用正常（Windows 编码显示问题） |

---

**注意**: LLM API 调用正常成功，但在 Windows 终端打印中文字符时可能出现 GBK 编码问题。这是因为 `content` 中包含中文，而 Windows 终端默认使用 GBK 编码。建议在实际使用中通过编码处理或使用终端显示 UTF-8。

## 测试使用方式

### 手动运行测试
```bash
# 进入项目目录
cd 03_Code

# 运行简单 API 连通测试（快速验证）
python test/test_all_apis_simple.py

# 运行正式 pytest 测试
pytest test/ -v

# 运行特定测试
pytest test/schemas/ -v
pytest test/api/ -v
```

### VS Code 测试

在 VS Code 中：
1. 打开测试面板（`Ctrl+Shift+T`）
2. 选择 `pytest` 测试运行器
3. 点击测试旁边的播放按钮运行测试

## 完成

✅ 文档已整理到 `docs/` 目录
✅ 测试文件已组织到 `test/` 目录
✅ 冗余临时文件已清理
✅ pytest 配置已设置
✅ CI 流程不会调用临时测试文件

---

**更新时间**: 2026-03-12
