# ☁️ 云端部署摘要

## 📁 项目结构

```
03_Code/
├── docker-compose.yml         # Docker 编排配置
├── .env.example               # 环境变量模板
├── QUICK_START.md             # 快速开始指南
├── DEPLOYMENT.md              # 详细部署文档
│
├── backend/
│   ├── Dockerfile             # 后端镜像构建
│   ├── main.py                # FastAPI 应用入口
│   ├── requirements.txt       # Python 依赖
│   └── src/                   # 源代码
│
└── frontend/
    ├── Dockerfile             # 前端镜像构建
    ├── nginx.conf             # Nginx 配置（API 代理）
    ├── vite.config.ts         # Vite 配置（开发代理）
    └── src/                   # React 源代码
```

## 🔧 关键配置文件

### 1. docker-compose.yml
- **MySQL**: 端口 3306（容器）/ 3307（主机）
- **MongoDB**: 端口 27017
- **Backend**: 端口 8000，健康检查 `/health`
- **Frontend**: 端口 80，反向代理 `/api/*` 到后端

### 2. .env.example
包含所有必需的环境变量：
- API 密钥（天气、地图、LLM、搜索）
- 数据库连接
- JWT 配置
- 短信配置

### 3. backend/Dockerfile
- 基于 Python 3.11
- 时区设置: Asia/Shanghai
- 健康检查: `/health`
- 启动命令: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`

### 4. frontend/nginx.conf
- 静态文件服务: `/`
- API 反向代理: `/api/*` → `http://backend:8000/api/*`
- 超时设置: 600秒（LLM 生成）

## 🚀 一键部署命令

### 本地开发
```bash
# 仅启动数据库
docker-compose up -d mysql mongodb

# 启动后端（本地运行）
cd backend && python main.py

# 启动前端（本地运行）
cd frontend && npm run dev
```

### Docker 完整部署
```bash
# 启动所有服务
docker-compose up -d

# 重新构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 云端部署
```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 2. 克隆代码
git clone <repo> /opt/outdoor-planner
cd /opt/outdoor-planner/03_Code

# 3. 配置环境
cp .env.example .env
vi .env

# 4. 启动服务
docker-compose up -d
```

## 🔍 验证部署

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 检查健康状态
curl http://localhost:8000/health

# 3. 查看 API 文档
http://localhost:8000/docs

# 4. 访问前端
http://localhost
```

## 📊 端口映射

| 服务 | 容器端口 | 主机端口 | 访问地址 |
|------|---------|---------|---------|
| Frontend | 80 | 80 | http://localhost |
| Backend | 8000 | 8000 | http://localhost:8000 |
| MySQL | 3306 | 3307 | localhost:3307 |
| MongoDB | 27017 | 27017 | localhost:27017 |

## 🔒 安全检查清单

- [ ] 修改 `.env` 中的 `JWT_SECRET_KEY`
- [ ] 设置强数据库密码
- [ ] 配置 HTTPS/SSL
- [ ] 限制入站端口（仅 80、443、22）
- [ ] 定期更新镜像
- [ ] 配置日志轮转

## 🛠️ 运维命令

```bash
# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart backend

# 更新代码
git pull
docker-compose up -d --build

# 备份数据
docker exec outdoor-mysql mysqldump -u root -p"password" outdoor_planner > backup.sql

# 进入容器
docker exec -it outdoor-backend bash
docker exec -it outdoor-mysql bash
```

## 📞 故障排查

| 问题 | 解决方案 |
|------|---------|
| 端口被占用 | 修改 docker-compose.yml 中的端口映射 |
| 数据库连接失败 | 等待数据库完全启动，检查容器日志 |
| API 404 | 检查 nginx.conf 中的代理配置 |
| 镜像构建失败 | 清理 Docker 缓存：`docker system prune -a` |

## 📚 相关文档

- [快速开始](QUICK_START.md)
- [详细部署指南](DEPLOYMENT.md)
- [后端 API 文档](backend/docs/README.md)
