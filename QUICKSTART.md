# 快速启动 - Docker 部署

## 前置要求

- Docker Desktop 已安装并运行
- Docker Compose 已可用

## 一键启动

```bash
start.bat
```

或使用 Make 命令：

```bash
make start
```

## 服务地址

| 服务 | 地址 |
|------|------|
| API 服务 | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| MySQL | localhost:3307 |
| MongoDB | localhost:27017 |

## 常用命令

```bash
make start      # 启动所有服务
make stop       # 停止服务
make logs       # 查看日志
make status     # 查看状态
make restart    # 重启服务
make build      # 重新构建
make clean      # 清理容器和数据
```

## Docker 命令

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

## 测试

```bash
# 在 Docker 容器中运行测试
make test

# 或直接执行
docker-compose exec backend pytest test/ -v
```

## 配置文件

- `.env` - 环境变量配置（API 密钥、数据库配置）
- `docker-compose.yml` - Docker 服务定义
- `scripts/init_mysql.sql` - MySQL 初始化脚本
- `scripts/setup_mongodb.js` - MongoDB 初始化脚本

## 云端部署

使用相同的配置部署到云端：

1. 将代码上传到服务器
2. 确保服务器已安装 Docker 和 Docker Compose
3. 运行 `make start` 或 `docker-compose up -d`

## 数据持久化

数据存储在 Docker Volume 中：
- `outdoor_mongodb_data` - MongoDB 数据
- `outdoor_mongodb_config` - MongoDB 配置
- `outdoor_mysql_data` - MySQL 数据

清理数据：`make clean-all`
