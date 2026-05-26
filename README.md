# 书法识文 App

韩应炳书法作品拍照识别工具。拍照 → 云端识别 → 输出印刷体文字。

## 快速开始

### 1. 安装 Python

从 https://www.python.org/downloads/ 下载 **Python 3.9 或 3.10**。
安装时勾选 **"Add Python to PATH"**。

验证安装：

```powershell
python --version
```

### 2. 启动后端

```powershell
cd calligraphy-app\backend

# 安装依赖（首次只需运行一次，过程较慢，需下载 PaddleOCR 模型）
pip install -r requirements.txt

# 启动服务
python main.py
```

看到 `Uvicorn running on http://0.0.0.0:8000` 即启动成功。

> ⚠️ 首次启动会自动下载 PaddleOCR 的中文识别模型（约 15MB），请保持网络畅通。

### 3. 使用前端

直接用浏览器打开 `frontend/index.html` 即可。

### iPhone 上用：

1. 将 `frontend` 文件夹放到一个 HTTP 服务器中（或用 Python 启动）：

```powershell
cd calligraphy-app
python -m http.server 8080
```

2. 在 iPhone 的 Safari 浏览器中访问 `http://你的电脑IP:8080/frontend/`
3. 点击底部分享按钮 → **"添加到主屏幕"**，以后就像 App 一样用了

> 注意：iPhone 和电脑需要在同一 Wi-Fi 网络下。
> 后端 API 地址需在 `frontend/app.js` 中修改 `API_BASE` 为电脑的局域网 IP。

## 配置

在 `frontend/app.js` 中：

```javascript
const API_BASE = "http://你的电脑IP:8000"; // 改成你电脑的局域网 IP
```

## 项目结构

```
calligraphy-app/
├── backend/                  # Python FastAPI 后端
│   ├── main.py              # API 入口
│   ├── requirements.txt     # Python 依赖
│   ├── Dockerfile           # Docker 部署配置
│   └── services/
│       ├── ocr_service.py   # OCR 识别服务
│       └── __init__.py
├── frontend/                # PWA 前端（浏览器）
│   ├── index.html           # 主页面
│   ├── style.css            # 样式
│   ├── app.js               # 逻辑代码
│   ├── manifest.json        # PWA 配置
│   └── sw.js                # Service Worker
├── docker-compose.yml       # Docker 编排
└── .env.example             # 环境变量模板
```

## 部署到云服务器

1. 购买云服务器（阿里云/腾讯云，2核4G 约 80元/月）
2. 安装 Docker
3. 上传项目，运行：

```bash
docker-compose up -d
```

4. 配置域名和 HTTPS 即可正式使用
