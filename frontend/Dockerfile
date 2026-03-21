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
# 生产阶段 - 使用 Nginx Alpine
# ====================================
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 非守护模式运行
CMD ["nginx", "-g", "daemon off;"]
