FROM python:3.10-slim-bookworm

WORKDIR /app

ENV FLAGS_use_mkldnn=0
ENV FLAGS_use_onednn=0
ENV FLAGS_enable_pir_api=0
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# 安装系统依赖（PaddleOCR 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 提前暴露二进制依赖问题，避免部署后启动才失败
RUN python -c "import cv2, paddle, paddleocr; print('OCR runtime imports OK')"

# 构建阶段预热 OCR：下载中文模型并验证 CPU 路径，避免首次请求时崩溃或长时间卡住
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_gpu=False, use_angle_cls=False, lang='ch', enable_mkldnn=False, cpu_threads=1, det_db_thresh=0.3, det_db_box_thresh=0.5, show_log=True); print('PaddleOCR warmup OK')"

# 复制代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 端口
EXPOSE 8000

# 启动
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
