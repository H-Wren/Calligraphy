# 部署说明

这个项目需要同时部署前端和后端：

- 前端：静态 PWA，适合 GitHub Pages。
- 后端：FastAPI + PaddleOCR，需要能运行 Docker 的服务，例如 Render、Railway、Fly.io 或云服务器。

## 1. 前端：GitHub Pages

前端发布到 `gh-pages` 分支，页面地址通常是：

```text
https://h-wren.github.io/Calligraphy/
```

如果第一次访问没有页面，到仓库：

```text
Settings -> Pages
```

把 Source 设为：

```text
Deploy from a branch
```

然后选择：

```text
Branch: gh-pages
Folder: / (root)
```

## 2. 后端：Render

仓库根目录已经包含 Render Blueprint：

```text
render.yaml
```

部署步骤：

1. 打开 Render。
2. 选择 `New +` -> `Blueprint`。
3. 连接 GitHub 仓库 `H-Wren/Calligraphy`。
4. Render 会读取 `render.yaml` 并创建 `calligraphy-api` 服务。
5. 服务创建后，等待首次构建完成。
6. 打开后端健康检查地址，确认返回 `status: ok`：

```text
https://你的-render-service.onrender.com/health
```

注意：当前配置使用 Render 免费实例。PaddleOCR 依赖较重，免费实例可能构建慢、冷启动慢，甚至内存不足。稳定使用建议后续升级到至少 1GB 内存以上的实例。

## 3. 连接前端和后端

拿到后端地址后，修改：

```text
frontend/config.js
```

把：

```javascript
window.CALLIGRAPHY_API_BASE = "";
```

改成：

```javascript
window.CALLIGRAPHY_API_BASE = "https://你的-render-service.onrender.com";
```

然后提交并推送，并重新发布 `gh-pages`：

```powershell
git add frontend/config.js
git commit -m "Configure production API endpoint"
git push origin master
git subtree push --prefix frontend origin gh-pages
```

如果 `gh-pages` 已存在且普通 push 被拒绝，可以删除本地临时分支后重新 split，再推送。

## 4. 本地临时切换 API

不改代码也可以在浏览器控制台临时设置 API 地址：

```javascript
localStorage.setItem("api_base", "https://你的-render-service.onrender.com");
location.reload();
```

清除配置：

```javascript
localStorage.removeItem("api_base");
location.reload();
```
