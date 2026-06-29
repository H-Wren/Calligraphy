# 书法识文

一款面向书法作品的拍照识别 PWA。用户可以用手机或浏览器上传书法图片，后端通过 PaddleOCR 识别文字，并支持查看、编辑、复制识别结果和保存本地历史记录。

![书法识文首页](docs/images/capture.png)

## 功能亮点

- 拍照或从相册选择书法作品图片
- 前端自动压缩图片，减少上传体积
- FastAPI 后端调用 PaddleOCR 中文识别
- 识别结果可编辑、复制，并保存到浏览器本地历史
- 支持自动裁剪与背景白化，便于保存更干净的作品图
- PWA 形态，可添加到 iPhone 主屏幕使用
- 提供 Docker Compose 部署配置

## 效果预览

| 识别中 | 结果页 | 识别文本 |
| --- | --- | --- |
| ![识别中](docs/images/processing.png) | ![识别结果顶部](docs/images/result-top.png) | ![识别文本](docs/images/result-text.png) |

## 技术栈

- 前端：HTML、CSS、原生 JavaScript、PWA
- 后端：Python、FastAPI、Uvicorn
- OCR：PaddleOCR、PaddlePaddle
- 图像处理：OpenCV、Pillow
- 部署：Docker、Docker Compose

## 项目结构

```text
Calligraphy/
├── backend/                  # FastAPI 后端
│   ├── main.py               # API 入口
│   ├── requirements.txt      # Python 依赖
│   ├── Dockerfile            # 后端 Docker 镜像
│   ├── uploads/              # 上传图片保存目录
│   └── services/
│       ├── image_processor.py # 自动裁剪和背景白化
│       └── ocr_service.py     # OCR 识别服务
├── frontend/                 # PWA 前端
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── manifest.json
│   └── sw.js
├── docs/images/              # README 展示图片
├── 截图/                     # 原始截图
├── docker-compose.yml
└── .env.example
```

## 本地运行

### 1. 准备 Python 环境

建议使用 Python 3.9 或 3.10。

```powershell
python --version
```

### 2. 启动后端

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

启动成功后，后端默认运行在：

```text
http://localhost:8000
```

首次运行 PaddleOCR 时会自动下载中文识别模型，请保持网络畅通。

### 3. 打开前端

直接用浏览器打开：

```text
frontend/index.html
```

如果要在手机上访问，建议在项目根目录启动一个静态服务：

```powershell
python -m http.server 8080
```

然后在同一 Wi-Fi 下用手机访问：

```text
http://你的电脑IP:8080/frontend/
```

如果后端不在本机，需要在 `frontend/app.js` 中把 `API_BASE` 改成后端地址：

```javascript
const API_BASE = "http://你的电脑IP:8000";
```

## Docker 部署

```bash
docker-compose up -d
```

默认暴露后端服务：

```text
http://localhost:8000
```

生产环境建议额外配置域名、HTTPS 和更严格的 CORS 白名单。

更完整的线上部署流程见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/recognize` | 上传图片并返回 OCR 识别结果 |
| `POST` | `/api/crop-image` | 上传图片并返回裁剪、白化后的图片 |

## 注意事项

- OCR 效果取决于照片清晰度、光线、纸张倾斜和书法字体复杂度。
- 当前前端使用浏览器 `localStorage` 保存历史记录，不会同步到服务端。
- `backend/uploads/` 会保存上传图片，公开部署时请按实际隐私要求清理或改造。
