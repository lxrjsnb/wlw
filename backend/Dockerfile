# ============================================================
# 后端 Dockerfile - Django + DRF
# ============================================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 配置 Debian 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用清华镜像源加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华镜像源加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput || true

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000 8001

# 使用 Gunicorn + Uvicorn Worker 启动（支持 WebSocket）
CMD ["gunicorn", "iot_system.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-"]
