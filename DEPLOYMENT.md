# 部署说明

本项目分为两个部分：

- 前端：静态网页，部署在 GitHub Pages。
- 后端：FastAPI + RapidOCR，部署在 Render Docker Web Service。

当前线上地址：

- 前端：https://h-wren.github.io/Calligraphy/
- 后端：https://calligraphy-api-7cs2.onrender.com

## 1. 前端：GitHub Pages

GitHub Pages 使用 `gh-pages` 分支，目录为 `/ (root)`。

仓库设置路径：

```text
Settings -> Pages -> Build and deployment
```

配置：

```text
Source: Deploy from a branch
Branch: gh-pages
Folder: / (root)
```

### 发布前端

因为本机 `git subtree` 曾出现异常，当前采用临时目录发布：

```powershell
New-Item -ItemType Directory -Force work\gh-pages-publish
robocopy work\Calligraphy\frontend work\gh-pages-publish /E
cd work\gh-pages-publish
git init
git checkout -b gh-pages
git config user.name "Codex"
git config user.email "codex@example.com"
git remote add origin https://github.com/H-Wren/Calligraphy.git
git add -A
git commit -m "Deploy frontend"
git push origin gh-pages --force
```

如果遇到 Git safe.directory 提示，用：

```powershell
git -c safe.directory=D:/Codex-workspaces/2026-06-30/jia/work/gh-pages-publish push origin gh-pages --force
```

## 2. 后端：Render

仓库根目录包含：

```text
render.yaml
```

Render 会基于 `backend/Dockerfile` 构建服务。

部署步骤：

1. 打开 Render。
2. 进入 `calligraphy-api` 服务。
3. 确认连接仓库 `H-Wren/Calligraphy`。
4. 等待最新 commit 自动部署。
5. 如果没有自动部署，点：

```text
Manual Deploy -> Clear build cache & deploy
```

健康检查：

```text
https://calligraphy-api-7cs2.onrender.com/health
```

正常返回示例：

```json
{"status":"ok","timestamp":"..."}
```

## 3. 前后端连接

线上前端的后端地址配置在：

```text
frontend/config.js
```

当前配置：

```javascript
window.CALLIGRAPHY_API_BASE = "https://calligraphy-api-7cs2.onrender.com";
```

修改后需要：

1. 提交到 `master`
2. 重新发布 `frontend/` 到 `gh-pages`

## 4. Render 免费实例限制

Render 免费实例会休眠，首次访问可能需要几十秒唤醒。OCR 任务也可能因资源限制变慢。

当前代码已做两层处理：

- 前端在上传前先请求 `/health` 唤醒后端。
- 识别接口采用后台任务：`POST /api/recognize` 创建任务，`GET /api/recognize/{job_id}` 轮询结果。

桌面浏览器可用性较好；手机浏览器仍可能受上传行为、PWA 缓存和网络环境影响，不作为稳定场景。

## 5. PWA 缓存更新

每次更新前端时，建议同时修改：

```text
frontend/sw.js
frontend/index.html
```

需要更新：

- `CACHE_NAME`
- `app.js?v=...`
- `config.js?v=...`
- `style.css?v=...`

如果手机端仍加载旧版本：

- iPhone Safari：设置 -> Safari -> 高级 -> 网站数据 -> 删除 `h-wren.github.io`
- Android Chrome：站点设置 -> 清除数据

## 6. 当前后端依赖策略

项目曾尝试 PaddleOCR，但在 Render 免费 CPU 环境中出现 oneDNN / PIR 运行时问题，后续改为：

```text
RapidOCR + ONNX Runtime
```

Python 版本为 3.10，`onnxruntime` 固定为 `1.23.2`，因为更高版本在该 Python 环境下没有可用 wheel。
