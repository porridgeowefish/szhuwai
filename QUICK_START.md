# 🚀 快速部署指南

## 本地开发（一键启动）

```bash
# 1. 配置环境
cp .env.example .env
# 编辑 .env 填写 API 密钥

# 2. 启动数据库（Docker）
docker-compose up -d mysql mongodb

# 3. 等待数据库就绪（约30秒）
docker-compose logs -f mysql

# 4. 启动后端
cd backend
python main.py

# 5. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问：
- 前端: http://localhost:3000
- 后端: http://localhost:8000/docs

---

## Docker 完整部署

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

## 云端部署（阿里云/腾讯云）

### 1. 服务器准备

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. 部署应用

```bash
# 克隆代码
git clone <repo> /opt/outdoor-planner
cd /opt/outdoor-planner/03_Code

# 配置环境
cp .env.example .env
vi .env  # 填写 API 密钥

# 启动服务
docker-compose --profile with-frontend up -d
```

### 3. 配置域名 + HTTPS（可选）

```bash
# 安装 Nginx + Certbot
apt-get install -y nginx certbot python3-certbot-nginx

# 配置站点
vi /etc/nginx/sites-available/outdoor-planner
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 启用站点
ln -s /etc/nginx/sites-available/outdoor-planner /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 申请 SSL 证书
certbot --nginx -d your-domain.com
```

---

## 常用命令

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
