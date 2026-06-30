"""
书法识别 App — FastAPI 后端入口
"""
import os
import uuid
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response
from dotenv import load_dotenv

from services.ocr_service import recognize_text
from services.image_processor import crop_calligraphy

load_dotenv()

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("calligraphy-api")

# ---------- FastAPI ----------
app = FastAPI(
    title="书法识别 API",
    description="为韩应炳先生书法作品提供拍照识别服务",
    version="1.0.0"
)

# CORS — 允许 PWA 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://h-wren.github.io",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    origin = request.headers.get("origin")
    if origin in {
        "https://h-wren.github.io",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
    }:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# ---------- 配置 ----------
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE", "10"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".heic", ".heif"}


# ---------- 工具函数 ----------
def validate_image(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


# ---------- API 路由 ----------
@app.get("/")
def root():
    return {"service": "书法识别 API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.options("/{path:path}")
def options_preflight(path: str):
    return {"status": "ok"}


@app.post("/api/recognize")
async def api_recognize(file: UploadFile = File(...)):
    """
    上传书法图片，返回 OCR 识别结果

    请求方式: multipart/form-data
    参数: file (图片文件)
    """
    # 1. 校验文件
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    if not validate_image(file.filename):
        raise HTTPException(400, f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")

    # 2. 读取文件内容
    image_data = await file.read()
    size_mb = len(image_data) / (1024 * 1024)

    if size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(400, f"图片过大（{size_mb:.1f}MB），请压缩到 {MAX_IMAGE_SIZE_MB}MB 以内")

    logger.info(f"收到图片: {file.filename} ({size_mb:.1f}MB)")

    # 3. 保存原始图片（留作记录）
    file_id = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    with open(save_path, "wb") as f:
        f.write(image_data)

    # 4. OCR 识别
    result = recognize_text(image_data)

    # 5. 返回结果
    if result.get("error"):
        logger.warning(f"识别异常: {result['error']}")
        return JSONResponse(
            status_code=200,
            content={"success": False, "error": result["error"], "text": ""}
        )

    logger.info(f"识别完成: {result['total_lines']} 行文字")
    return {
        "success": True,
        "text": result["text"],
        "lines": result["lines"],
        "total_lines": result["total_lines"],
    }


@app.post("/api/crop-image")
async def api_crop_image(file: UploadFile = File(...)):
    """
    上传书法图片，返回自动裁剪+背景白化后的图片
    """
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    if not validate_image(file.filename):
        raise HTTPException(400, f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")

    image_data = await file.read()

    logger.info(f"裁剪图片: {file.filename} ({len(image_data)/1024:.1f}KB)")

    try:
        result_bytes = crop_calligraphy(image_data)
    except Exception as e:
        logger.exception("裁剪失败")
        raise HTTPException(500, f"图片处理失败: {str(e)}")

    from fastapi.responses import Response
    return Response(
        content=result_bytes,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="cropped_{file.filename}"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
