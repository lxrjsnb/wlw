# ============================================================
# 前端 Dockerfile - Vue 3 + Vite
# ============================================================

# 构建阶段 - 使用国内镜像源加速
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 配置 npm 使用淘宝镜像源加速
RUN npm config set registry https://registry.npmmirror.com

# 复制 package.json 和 package-lock.json（如果存在）
COPY package*.json ./

# 安装依赖（构建需要 devDependencies）
RUN npm ci --silent

# 复制源代码
COPY . .

# 构建生产环境文件
RUN npm run build

# 生产阶段 - 使用 Nginx
FROM nginx:alpine

# 配置 nginx 使用阿里云镜像源（如果需要安装额外包）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
