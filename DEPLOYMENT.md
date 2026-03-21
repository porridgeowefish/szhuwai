# 部署指南

## 📋 目录

1. [快速开始](#快速开始)
2. [本地开发部署](#本地开发部署)
3. [Docker 完整部署](#docker-完整部署)
4. [云端部署](#云端部署)
5. [常见问题](#常见问题)

---

## 🚀 快速开始

### 前置要求

- **Python 3.10+** (开发环境)
- **Node.js 18+** (前端开发)
- **MySQL 8.0+**
- **MongoDB 8.0+**
- **Docker & Docker Compose** (可选，用于容器化部署)

### 1. 克隆项目

```bash
cd D:\2_Study\Outdoor-Agent-Planner\03_Code
```

### 2. 配置环境变量

`.env` 文件已配置好 API 密钥，数据库配置使用本地默认设置：

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

### 3. 初始化数据库

**Windows:**
```cmd
scripts\init_local_db.bat
```

**Linux/Mac:**
```bash
bash scripts/init_local_db.sh
```

### 4. 启动服务

```bash
cd backend
python main.py
```

访问 http://localhost:8000/docs 查看 API 文档。

---

## 💻 本地开发部署

### 方案一：使用本地 MySQL + Docker MongoDB

适合已有本地 MySQL 的场景。

#### 1. 启动 MongoDB (Docker)

```bash
docker-compose up -d mongodb
```

#### 2. 初始化 MySQL

```bash
# 创建数据库
mysql -u root -e "CREATE DATABASE IF NOT EXISTS outdoor_planner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入表结构
mysql -u root outdoor_planner < scripts/init_mysql.sql
```

#### 3. 启动后端

```bash
cd backend
python main.py
```

### 方案二：完全使用 Docker

```bash
# 启动所有服务（包括数据库）
docker-compose --profile full up -d

# 查看日志
docker-compose logs -f backend
```

### 方案三：混合部署（本地后端 + Docker 数据库）

```bash
# 仅启动数据库服务
docker-compose up -d mongodb mysql

# 启动本地后端
cd backend
python main.py
```

---

## 🐳 Docker 完整部署

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │  │   MongoDB    │ │
│  │   (Nginx)    │──│  (FastAPI)   │──│   (Port 27017)│ │
│  │   Port 80    │  │  Port 8000   │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                           │                             │
│                    ┌──────┴──────┐                     │
│                    │   MySQL     │                     │
│                    │  Port 3307  │                     │
│                    └─────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### 完整部署命令

```bash
# 1. 构建并启动所有服务
docker-compose --profile full up -d

# 2. 查看服务状态
docker-compose ps

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down

# 5. 停止并删除数据卷
docker-compose down -v
```

### 服务端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| Frontend | 80 | 80 | Web 界面 |
| Backend | 8000 | 8000 | API 服务 |
| MongoDB | 27017 | 27017 | 报告存储 |
| MySQL | 3306 | 3307 | 用户数据 |

---

## ☁️ 云端部署

### MongoDB Atlas (推荐)

#### 1. 创建免费集群

访问 https://www.mongodb.com/cloud/atlas/register

#### 2. 获取连接字符串

```
mongodb+srv://username:password@cluster.mongodb.net/outdoor_planner?retryWrites=true&w=majority
```

#### 3. 更新 .env

```env
# 云端 MongoDB 连接
MONGO_CLOUD_URI=mongodb+srv://user:pass@cluster.mongodb.net/outdoor_planner?retryWrites=true&w=majority
```

#### 4. 使用生产配置启动

```bash
docker-compose --profile production up -d
```

### 阿里云/腾讯云部署

#### 使用 ECS + 云数据库

1. **云数据库 MySQL**: 使用云厂商提供的 RDS
2. **云数据库 MongoDB**: 使用云厂商提供的 MongoDB 实例
3. **应用部署**: 使用 Docker Compose 或 Kubernetes

#### 环境变量配置

```env
# 云数据库连接
MYSQL_HOST=your-rds.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=outdoor_user
MYSQL_PASSWORD=strong_password_here

MONGO_HOST=your-mongodb.mongo.aliyuncs.com
MONGO_PORT=3717
MONGO_USER=outdoor_user
MONGO_PASSWORD=strong_password_here
```

---

## 🔧 常见问题

### Q1: MySQL 连接失败

**错误**: `Can't connect to MySQL server on 'localhost'`

**解决方案**:
1. 确认 MySQL 服务已启动
2. Windows: 在服务管理器中启动 MySQL80
3. 检查端口是否被占用: `netstat -an | findstr 3306`

### Q2: MongoDB 连接失败

**错误**: `No reachable servers`

**解决方案**:
1. 启动 MongoDB 服务或使用 Docker
2. 检查防火墙设置
3. 使用 Docker: `docker-compose up -d mongodb`

### Q3: 端口已被占用

**解决方案**:
```bash
# 修改 .env 中的端口
BACKEND_PORT=8001
FRONTEND_PORT=8080
```

### Q4: 代理配置

如需通过代理访问外部 API，已在 `.env` 中配置：

```env
PROXY_HTTP=http://127.0.0.1:7890
PROXY_HTTPS=http://127.0.0.1:7890
```

### Q5: 数据库迁移

从本地迁移到云端：

```bash
# 导出 MySQL
mysqldump -u root outdoor_planner > backup.sql

# 导入到云端
mysql -h cloud-host -u user -p outdoor_planner < backup.sql

# MongoDB 导出
mongodump --uri="mongodb://localhost:27017/outdoor_planner" --out=./backup

# MongoDB 导入
mongorestore --uri="mongodb+srv://cloud-host/outdoor_planner" ./backup
```

---

## 📚 API 端点

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/sms/send` - 发送验证码

### 计划生成
- `POST /api/v1/plan/generate` - 生成户外活动计划

### 报告管理
- `GET /api/v1/reports` - 获取报告列表
- `GET /api/v1/reports/{id}` - 获取报告详情
- `DELETE /api/v1/reports/{id}` - 删除报告

### 额度管理
- `GET /api/v1/quota` - 查询剩余额度

### 用户管理（管理员）
- `GET /api/v1/users` - 获取用户列表
- `PATCH /api/v1/users/{id}/status` - 更新用户状态

完整 API 文档: http://localhost:8000/docs

---

## 🔐 生产环境检查清单

- [ ] 修改 `JWT_SECRET_KEY` 为随机密钥
- [ ] 设置强密码的数据库用户
- [ ] 配置 HTTPS/SSL 证书
- [ ] 启用防火墙规则
- [ ] 配置日志监控
- [ ] 设置数据库备份
- [ ] 配置 CDN（静态资源）
- [ ] 启用速率限制
- [ ] 配置告警通知

---

## 📞 支持

如有问题，请提交 Issue 或查看项目文档。
