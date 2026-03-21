# ====================================
# 构建阶段 - 使用 Node.js 22 LTS
# ====================================
FROM node:22-alpine AS builder

WORKDIR /app

# 安装必要的系统依赖
RUN apk add --no-cache python3 make g++

# 使用国内 npm 镜像加速
RUN npm config set registry https://registry.npmmirror.com

# 配置 npm 生产环境优化
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000

# 复制依赖文件（利用 Docker 缓存）
COPY package.json package-lock.json* ./

# 安装依赖（使用 ci 而非 install，确保版本一致性）
RUN npm ci --legacy-peer-deps --prefer-offline --no-audit

# 复制源代码
COPY . .

# 构建前端（生产模式优化）
RUN npm run build

# ====================================
# 生产阶段 - 使用 Nginx 1.27 Alpine
# ====================================
FROM nginx:1.27-alpine

# 安装 brotli 压缩模块
RUN apk add --no-cache brotli

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 添加安全响应头
RUN echo 'server { \
    listen 80; \
    server_name _; \
    \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # 安全响应头 \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
    add_header Referrer-Policy "no-referrer-when-downgrade" always; \
    \
    # Gzip 压缩 \
    gzip on; \
    gzip_vary on; \
    gzip_proxied any; \
    gzip_comp_level 6; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml; \
    gzip_min_length 256; \
    \
    # Brotli 压缩 \
    brotli on; \
    brotli_comp_level 6; \
    brotli_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml; \
    \
    # SPA 路由支持 \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # 静态资源缓存 \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
        access_log off; \
    } \
    \
    # API 文档代理 \
    location /docs { \
        proxy_pass http://backend:8000/docs; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    \
    location /openapi.json { \
        proxy_pass http://backend:8000/openapi.json; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    \
    # 后端 API 反向代理 \
    location /api/ { \
        proxy_pass http://backend:8000/api/; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        \
        # LLM 生成需要较长超时时间 \
        proxy_connect_timeout 600s; \
        proxy_send_timeout 600s; \
        proxy_read_timeout 600s; \
        proxy_buffering off; \
    } \
    \
    # 健康检查 \
    location /health { \
        access_log off; \
        proxy_pass http://backend:8000/health; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    \
    # 前端健康检查 \
    location /frontend-health { \
        access_log off; \
        return 200 "healthy\n"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/frontend-health || exit 1

# 非守护模式运行
CMD ["nginx", "-g", "daemon off;"]
