# 户外活动智能规划系统

## 项目简介

户外活动智能规划系统是一个基于数据契约的户外活动规划平台，整合天气、地图、搜索等多种 API，为用户提供专业的户外活动建议和规划服务。

## 核心特性

- **数据契约驱动**：所有 API 通信使用结构化 JSON，确保数据一致性
- **多 API 集成**：集成和风天气、高德地图、Tavily 搜索等多种服务
- **智能分析**：提供轨迹分析、天气安全评估、路线规划等功能
- **模块化架构**：清晰的模块划分，易于扩展和维护

## 项目结构

```
03_Code/
├── api/                    # API 客户端实现
│   ├── config.py          # 配置管理
│   ├── utils.py          # 基础类和工具
│   ├── weather_client.py  # 天气 API 客户端
│   ├── map_client.py     # 地图 API 客户端
│   └── search_client.py  # 搜索 API 客户端
├── schemas/              # 数据模型定义
│   ├── base.py           # 基础模型（Point3D）
│   ├── track.py          # 轨迹分析模型
│   ├── weather.py        # 天气数据模型
│   ├── transport.py      # 交通路线模型
│   ├── search.py        # 搜索结果模型
│   └── output.py        # 输出模型
├── test/               # 测试套件
│   ├── __init__.py
│   ├── conftest.py     # pytest 配置
│   ├── pytest.ini      # pytest 配置文件
│   ├── api/           # API 客户端测试
│   ├── schemas/       # 数据模型测试
│   └── integration/   # 集成测试
├── docs/              # 技术文档
│   ├── API_TECHNICAL_DOCS.md    # API 技术文档
│   └── SCHEMAS.md              # 数据模型文档
├── .env.example       # 环境变量模板
├── .gitignore        # Git 忽略配置
├── Makefile         # 常用命令
├── FILE_ORGANIZATION.md   # 文件组织说明
└── README.md        # 本文档
```

## 快速开始

### 环境要求

- Python 3.8+
- Anaconda (推荐使用 real_base 环境)

### 安装步骤

1. **克隆项目**
```bash
cd 03_Code
```

2. **创建虚拟环境**
```bash
# 使用 Anaconda real_base 环境
conda activate real_base
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥
```

### 必填环境变量

| 变量名 | 说明 |
|-------|------|
| `QWEATHER_API_KEY` | 和风天气 API 密钥 |
| `AMAP_API_KEY` | 高德地图 API 密钥 |
| `LLM_API_KEY` | LLM API 密钥 |
| `TAVILY_API_KEY` | Tavily 搜索 API 密钥 |

可选环境变量：
- `PROXY_HTTP` / `PROXY_HTTPS`：代理地址（本机代理端口为 7890）
- `API_TIMEOUT`：API 超时时间（秒，默认：10）
- `API_RETRY`：重试次数（默认：3）

## 运行项目

### 基本使用

```python
from api.weather_client import WeatherClient
from api.map_client import MapClient
from api.search_client import SearchClient

# 初始化客户端
weather_client = WeatherClient()
map_client = MapClient()
search_client = SearchClient()

# 获取天气
forecast = weather_client.get_weather_3d("Beijing")

# 地理编码
location = map_client.geocode("北京市朝阳区")

# 搜索信息
results = search_client.search("北京 徒步 路线")
```

### 使用 Makefile

```bash
# 运行所有测试
make test

# 代码检查
make lint

# 类型检查
make type-check
```

## 测试

### 测试命令

```bash
# 运行所有测试
pytest test/ -v

# 跳过慢速测试
pytest test/ -m "not slow" -v

# 运行特定模块测试
pytest test/schemas/ -v
pytest test/api/ -v
pytest test/integration/ -v

# 运行带覆盖率的测试
pytest test/ --cov=schemas --cov=api --cov-report=html
```

### VS Code 一键测试

项目已配置 VS Code 测试环境：

1. 打开测试面板（`Ctrl+Shift+T`）
2. 选择测试并点击运行

### 测试说明

- `test/schemas/`：数据模型单元测试
- `test/api/`：API 客户端测试
- `test/integration/`：集成测试（CI 中不运行）

## 部署

### 生产环境配置

1. **环境变量配置**
```bash
# 使用生产环境 API 密钥
QWEATHER_API_KEY=production_key
AMAP_API_KEY=production_key
```

2. **代理配置**
```bash
# 如需代理
PROXY_HTTP=http://proxy-server:port
PROXY_HTTPS=http://proxy-server:port
```

3. **日志级别**
生产环境建议使用 `WARNING` 或 `ERROR` 级别。

### 性能优化

- **缓存**：API 响应自动缓存，默认 TTL 为 1 小时
- **限流**：自动实现 API 限流，防止配额耗尽
- **重试机制**：请求失败自动重试，指数退避策略

## 故障排除

### 常见问题

#### 1. 天气 API 返回 400 Invalid Parameter

**原因**：`location` 参数格式不正确

**解决方案**：
- 使用经纬度坐标格式：`lon,lat`
- 示例：`location="116.0579,22.5431"`

#### 2. Windows 终端编码问题

**原因**：Windows 终端默认使用 GBK 编码

**解决方案**：
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout, encoding='utf-8')
```

#### 3. 网络连接问题

**原因**：代理配置或网络限制

**解决方案**：
- 检查 `.env` 中的代理设置
- 确认 API 密钥正确

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或针对特定客户端
weather_client.logger.setLevel(logging.DEBUG)
```

## 文档

- [API 技术文档](docs/API_TECHNICAL_DOCS.md)：详细的 API 接口说明
- [数据模型文档](docs/SCHEMAS.md)：数据模型定义和使用说明

## 开发规范

- **代码风格**：使用 `ruff` 进行代码检查
- **类型检查**：使用 `mypy --strict` 进行类型检查
- **测试优先**：先写测试，后写逻辑
- **中文文档**：所有文档使用中文编写

## 许可证

MIT License
