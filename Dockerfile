FROM python:3.11-slim

LABEL maintainer="DaimaRuge"
LABEL description="Jiuge - Personal Music AI Agent"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/
COPY skill/ ./skill/

# 创建数据目录
RUN mkdir -p /app/data /app/music

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV JIUGE_DATA_DIR=/app/data
ENV JIUGE_MUSIC_DIR=/app/music

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 启动命令
CMD ["uvicorn", "jiuge.api:app", "--host", "0.0.0.0", "--port", "8000"]
