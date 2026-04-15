# 快速启动指南

## 前置要求

- **Python 3.10+** (开发环境)
- **Node.js 18+** (前端开发)
- **MySQL 8.0+**
- **MongoDB 8.0+**
- **Docker & Docker Compose** (可选，用于容器化部署)

---

## 方式一：Docker 一键启动

适合使用 Docker Desktop 的场景。

### 一键启动

```bash
start.bat
```

或使用 Make 命令：

```bash
make start
```

### 服务地址

| 服务 | 地址 |
|------|------|
| API 服务 | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| MySQL | localhost:3307 |
| MongoDB | localhost:27017 |

### 常用 Make 命令

```bash
make start      # 启动所有服务
make stop       # 停止服务
make logs       # 查看日志
make status     # 查看状态
make restart    # 重启服务
make build      # 重新构建
make clean      # 清理容器和数据
```

### 常用 Docker 命令

```bash
# 启动所有服务
docker-compose up -d

# 仅启动数据库
docker-compose up -d mysql mongodb

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建
docker-compose build --no-cache
```

### 测试

```bash
# 在 Docker 容器中运行测试
make test

# 或直接执行
docker-compose exec backend pytest test/ -v
```

---

## 方式二：本地开发部署

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写 API 密钥和数据库配置
```

`.env` 数据库默认配置：

```env
# 本地 MySQL (默认 localhost:3306)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=outdoor_planner

# 本地 MongoDB (默认 localhost:27017)
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=outdoor_planner
```

### 2. 启动数据库（Docker）

```bash
docker-compose up -d mysql mongodb
```

等待数据库就绪（约30秒）：

```bash
docker-compose logs -f mysql
```

### 3. 初始化数据库

**Windows:**
```cmd
scripts\init_local_db.bat
```

**Linux/Mac:**
```bash
bash scripts/init_local_db.sh
```

### 4. 启动后端

```bash
cd backend
python main.py
```

### 5. 启动前端（新终端）

```bash
cd frontend
npm install
npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 (开发模式) / http://localhost:5173 (Vite) |
| 后端 | http://localhost:8000/docs |

---

## 方式三：Docker 完整部署（含前端）

```bash
# 启动所有服务（含前端）
docker-compose --profile with-frontend up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

访问：
- 前端: http://localhost
- 后端: http://localhost:8000/docs

---

## 配置文件说明

- `.env` - 环境变量配置（API 密钥、数据库配置）
- `docker-compose.yml` - Docker 服务定义
- `scripts/init_mysql.sql` - MySQL 初始化脚本
- `scripts/setup_mongodb.js` - MongoDB 初始化脚本

## 数据持久化

数据存储在 Docker Volume 中：
- `outdoor_mongodb_data` - MongoDB 数据
- `outdoor_mongodb_config` - MongoDB 配置
- `outdoor_mysql_data` - MySQL 数据

清理数据：`make clean-all`

---

## 常用运维命令

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 停止服务
docker-compose down

# 更新代码
git pull
docker-compose up -d --build

# 备份数据
docker exec outdoor-mysql sh -c 'exec mysqldump --all-databases -uroot -p"password"' > backup.sql
```

---

## API 密钥申请

| 服务 | 地址 |
|------|------|
| 和风天气 | https://dev.qweather.com/ |
| 高德地图 | https://console.amap.com/ |
| 硅基流动 | https://cloud.siliconflow.cn/ |
| Tavily | https://tavily.com/ |
| 阿里云短信 | https://dysms.console.aliyun.com/ |
