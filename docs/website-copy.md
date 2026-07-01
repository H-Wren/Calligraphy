# 个人网站项目文案：书法识文

以下文案可用于更新到个人网站 [https://h-wren.github.io/Website/](https://h-wren.github.io/Website/) 的项目页、作品集页或工具列表。

## 项目卡片版

**书法识文**  
一个面向书法作品整理的 OCR 实验工具。用户可以在桌面浏览器上传书法照片，系统自动压缩图片并调用后端识别文字，返回可编辑、可复制、可保存到本地历史的释文结果。项目重点不在通用 OCR，而在探索传统书法作品如何进入数字档案、作品检索和个人收藏整理流程。

链接：

- Demo: https://h-wren.github.io/Calligraphy/
- GitHub: https://github.com/H-Wren/Calligraphy

技术关键词：FastAPI, RapidOCR, ONNX Runtime, GitHub Pages, Render, PWA

## 稍长介绍版

**书法识文** 是一个围绕书法作品数字化整理建立的小型 Web 工具。它把“拍照/上传作品图 -> OCR 识别 -> 人工校对 -> 保存释文”的流程做成一个可操作原型，用于辅助书法作品的文字记录、档案整理和检索准备。

项目采用静态前端 + Python 后端架构：前端部署在 GitHub Pages，负责图片上传、压缩、结果编辑和本地历史记录；后端部署在 Render，使用 FastAPI 接收图片，并通过 RapidOCR / ONNX Runtime 完成中文文字识别。由于书法字体、拍摄角度和纸面状态对 OCR 影响很大，项目将识别结果定位为“可校对草稿”，而不是最终文本。

当前版本桌面端可用，手机端仍受浏览器上传机制、PWA 缓存和免费后端冷启动影响，暂不作为稳定使用场景。这个项目更像是一个面向文化材料整理的工具原型：它验证了书法图片从视觉材料进入结构化文本工作流的可能性，也为后续作品档案、批量整理和个人网站展示提供基础。

## 精简项目说明

一个桌面端优先的书法 OCR 原型工具，用于将书法作品照片转成可编辑文本，辅助作品释文、档案整理和后续检索。前端使用原生 HTML/CSS/JavaScript 与 PWA 缓存，后端使用 FastAPI + RapidOCR，并部署到 GitHub Pages 与 Render。

## 网站列表用一句话

书法识文：一个将书法照片转换为可编辑文本的 OCR 实验工具，用于辅助作品释文和数字档案整理。

## 英文版

**Calligraphy OCR** is a desktop-first experimental tool for organizing calligraphy works. It lets users upload a calligraphy image, sends it to a FastAPI backend for OCR, and returns editable text that can be copied or saved locally. The project is positioned as an archival assistant rather than a general-purpose OCR product: recognition results are intended as drafts for human correction, especially given the variability of calligraphic styles and image quality.

Built with vanilla JavaScript, FastAPI, RapidOCR, ONNX Runtime, GitHub Pages, and Render.

## 可放入项目元数据

```json
{
  "title": "书法识文",
  "subtitle": "书法作品 OCR 与数字化整理辅助工具",
  "description": "桌面端优先的书法 OCR 原型，用于将书法作品照片转换为可编辑文本，辅助释文、归档和检索。",
  "status": "Prototype",
  "role": "Full-stack development, product framing, deployment",
  "stack": ["HTML", "CSS", "JavaScript", "FastAPI", "RapidOCR", "ONNX Runtime", "GitHub Pages", "Render"],
  "demoUrl": "https://h-wren.github.io/Calligraphy/",
  "repoUrl": "https://github.com/H-Wren/Calligraphy"
}
```
