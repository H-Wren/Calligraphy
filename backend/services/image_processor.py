"""
书法图片处理器
自动裁剪 + 背景白化，适合商品展示

核心策略：
通过局部对比度（纹理分析）定位文字区域，
然后向外扩展找到纸张边界，最后裁剪+白化。
"""
import io
import numpy as np
from PIL import Image
import cv2
import logging

logger = logging.getLogger(__name__)


def _find_text_region(gray: np.ndarray) -> tuple:
    """
    通过局部对比度分析找到文字区域。
    文字笔画与纸张之间对比度高，而平滑背景区域对比度低。
    返回 (top, bottom, left, right) 或 None。
    """
    h, w = gray.shape

    # 大核高斯模糊获取背景亮度估计
    blur = cv2.GaussianBlur(gray, (31, 31), 0)

    # 局部对比度 = 原图与背景估计的绝对差
    # 文字区域对比度高，平滑背景对比度低
    contrast = cv2.absdiff(gray, blur)

    # Otsu 自适应阈值分割对比度图
    _, text_mask = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 大核膨胀连接邻近文字
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    text_mask = cv2.dilate(text_mask, kernel, iterations=2)

    # 填孔洞
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel)

    # 找轮廓，过滤小噪点
    contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = max(200, h * w * 0.0005)
    big = [c for c in contours if cv2.contourArea(c) > min_area]

    if not big:
        return None

    all_pts = np.vstack(big)
    x, y, bw, bh = cv2.boundingRect(all_pts)
    return (y, y + bh, x, x + bw)  # top, bottom, left, right


def _expand_to_paper(gray: np.ndarray, text_roi: tuple) -> tuple:
    """
    从文字区域向外扩展，找到纸张边界。
    假设纸张是均匀的浅色背景，遇到非纸张色（墙壁、桌面）时停止。
    """
    h, w = gray.shape
    top, bottom, left, right = text_roi

    # 从文字区域中心采样纸张颜色（边缘可能包含背景）
    cx, cy = (left + right) // 2, (top + bottom) // 2
    patch = gray[max(0, cy-15):min(h, cy+15), max(0, cx-15):min(w, cx+15)]
    paper_color = np.median(patch)

    # 纸张亮度允许偏差 ±35
    lower = paper_color - 35
    upper = paper_color + 35

    # 纸张亮度允许偏差 ±30
    lower = paper_color - 35
    upper = paper_color + 35

    # 逐行/列向外扩展
    # 向上
    new_top = top
    if top > 0:
        scores = []
        for y in range(top - 1, max(0, top - h // 3), -1):
            row = gray[y, left:right]
            match = np.sum((row > lower) & (row < upper)) / len(row)
            scores.append(match)
            if len(scores) > 5 and match < 0.5:
                break
            new_top = y

    # 向下
    new_bottom = bottom
    if bottom < h:
        scores = []
        for y in range(bottom, min(h, bottom + h // 3)):
            row = gray[y, left:right]
            match = np.sum((row > lower) & (row < upper)) / len(row)
            scores.append(match)
            if len(scores) > 5 and match < 0.5:
                break
            new_bottom = y

    # 向左
    new_left = left
    if left > 0:
        scores = []
        for x in range(left - 1, max(0, left - w // 3), -1):
            col = gray[top:bottom, x]
            match = np.sum((col > lower) & (col < upper)) / len(col)
            scores.append(match)
            if len(scores) > 5 and match < 0.5:
                break
            new_left = x

    # 向右
    new_right = right
    if right < w:
        scores = []
        for x in range(right, min(w, right + w // 3)):
            col = gray[top:bottom, x]
            match = np.sum((col > lower) & (col < upper)) / len(col)
            scores.append(match)
            if len(scores) > 5 and match < 0.5:
                break
            new_right = x

    return (new_top, new_bottom, new_left, new_right)


def _whiten(cropped: np.ndarray) -> np.ndarray:
    """保守白化：只变亮区域，绝不覆盖墨迹"""
    gray = cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, bright = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    paper = cv2.bitwise_and(bright, cv2.bitwise_not(ink))
    paper = cv2.dilate(paper, np.ones((3, 3), np.uint8), iterations=1)
    paper = cv2.bitwise_and(paper, cv2.bitwise_not(ink))
    result = cropped.copy()
    result[paper > 0] = [255, 255, 255]
    return result


def crop_calligraphy(image_data: bytes) -> bytes:
    """
    自动裁剪书法作品 + 背景白化。

    流程：
    1. 局部对比度分析定位文字区域（不受背景颜色影响）
    2. 从文字区域向外扩展到纸张边界
    3. 裁剪 + 背景白化
    """
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    img_np = np.array(img)
    h, w = img_np.shape[:2]
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # ========== 步骤1：找文字区域 ==========
    text_roi = _find_text_region(gray)
    if text_roi is None:
        logger.warning("未检测到文字区域")
        result = _whiten(img_np)
        out = io.BytesIO()
        Image.fromarray(result).save(out, format="JPEG", quality=95)
        return out.getvalue()

    top, bottom, left, right = text_roi

    # ========== 步骤2：扩展到纸张 ==========
    top, bottom, left, right = _expand_to_paper(gray, (top, bottom, left, right))

    # 加边距
    pad = 20
    x1 = max(0, left - pad)
    y1 = max(0, top - pad)
    x2 = min(w, right + pad)
    y2 = min(h, bottom + pad)

    # 跳过裁剪（内容铺满）
    if (x2 - x1) * (y2 - y1) > w * h * 0.95:
        logger.info("跳过裁剪（内容铺满）")
        cropped = img_np.copy()
    else:
        cropped = img_np[y1:y2, x1:x2].copy()
        logger.info(f"裁剪: ({x1},{y1})→({x2},{y2})")

    # ========== 白化 + 输出 ==========
    result = _whiten(cropped)
    out = io.BytesIO()
    Image.fromarray(result).save(out, format="JPEG", quality=95)
    return out.getvalue()
