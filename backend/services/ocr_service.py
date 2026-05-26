"""
书法 OCR 识别服务
封装 PaddleOCR 3.x，支持楷书/行书文字识别（简体输出）
"""
import numpy as np
from PIL import Image, ImageEnhance
import io
import cv2
import logging

logger = logging.getLogger(__name__)

_ocr_instance = None


def get_ocr():
    """获取 OCR 单例"""
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            logger.info("正在初始化 PaddleOCR...")
            _ocr_instance = PaddleOCR(
                lang='ch',
                use_textline_orientation=True,
                text_det_thresh=0.3,
                text_det_box_thresh=0.5,
            )
            logger.info("PaddleOCR 初始化完成")
        except Exception as e:
            logger.error(f"PaddleOCR 初始化失败: {e}")
            raise
    return _ocr_instance


def _deskew(img: np.ndarray) -> np.ndarray:
    """轻量纠偏：检测图像中的长直线，计算偏转角并纠正"""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=int(min(h, w) * 0.15))
    if lines is None:
        return img

    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if -30 <= angle <= 30:
            angles.append(angle)

    if not angles:
        return img

    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:
        return img

    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    logger.info(f"纠偏: {median_angle:.1f}°")
    return rotated


def _preprocess(image_data: bytes) -> np.ndarray:
    """
    预处理图片：
    1. PIL 基础增强（对比度、锐度、亮度）
    2. CLAHE 去反光（保留彩色信息，不二值化）
    3. 轻量纠偏
    """
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    # 1. 增强对比度
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    # 2. 增强锐度
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    # 3. 增强亮度
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)

    img = np.array(image)

    # 4. CLAHE 去反光（仅在亮度通道处理，保留颜色）
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # 5. 纠偏
    result = _deskew(result)

    return result


def _is_noise(text: str, confidence: float, box: list) -> bool:
    """判断识别结果是否为噪声（印章、污渍等）"""
    # 极低置信度直接过滤
    if confidence < 0.3:
        return True

    # 文本内容清洗
    stripped = text.strip()
    if not stripped:
        return True

    # 纯标点/数字/字母（非中文内容）
    non_cjk = sum(1 for c in stripped if not ('一' <= c <= '鿿'))
    # 如果非中文字符占比超过一半，视为噪声
    if non_cjk > len(stripped) * 0.5:
        return True

    # 低置信度一律过滤
    if confidence < 0.5:
        return True

    # 检测框极小（< 30px 宽或高）→ 噪声
    if box is not None and len(box) >= 4:
        import numpy as np
        if isinstance(box, np.ndarray):
            box_flat = box.flatten().tolist()
        else:
            box_flat = list(box)
        if len(box_flat) >= 4:
            x1, y1, x2, y2 = int(box_flat[0]), int(box_flat[1]), int(box_flat[2]), int(box_flat[3])
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            if w < 30 or h < 30:
                return True

    return False


def _to_simplified(text: str) -> str:
    """繁体转简体"""
    try:
        import zhconv
        return zhconv.convert(text, 'zh-cn')
    except ImportError:
        return text


def recognize_text(image_data: bytes) -> dict:
    """
    对图片进行 OCR 识别。

    Args:
        image_data: 图片的二进制数据

    Returns:
        dict: {
            "text": "识别出的纯文本（简体）",
            "lines": [ ... ],
            "total_lines": ...,
            "error": None 或 错误信息
        }
    """
    try:
        ocr = get_ocr()

        # 预处理
        img_array = _preprocess(image_data)

        # PaddleOCR 3.x API
        # text_rec_score_thresh=0.3 降低识别门槛，保留更多低自信度生僻字
        result = ocr.ocr(img_array, text_rec_score_thresh=0.3)
        if not result or result[0] is None:
            return {
                "success": True,
                "text": "",
                "lines": [],
                "total_lines": 0,
                "error": "未识别到文字，请确认图片中包含书法文字"
            }

        res = result[0]
        rec_texts = res.get("rec_texts", [])
        rec_scores = res.get("rec_scores", [])
        rec_boxes = res.get("rec_boxes", [])

        if not rec_texts:
            return {
                "success": True,
                "text": "",
                "lines": [],
                "total_lines": 0,
                "error": "未识别到文字，请确认图片中包含书法文字"
            }

        lines = []
        for idx in range(len(rec_texts)):
            text = rec_texts[idx]
            score = rec_scores[idx] if idx < len(rec_scores) else 0.0
            box = rec_boxes[idx] if idx < len(rec_boxes) else []

            # 过滤噪声
            if _is_noise(text, score, box):
                continue

            # 繁体转简体
            simplified = _to_simplified(text)

            line = {
                "text": simplified,
                "raw_text": text,
                "confidence": round(float(score), 4),
                "order": idx,
            }
            if box is not None and len(box) >= 4:
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                line["box"] = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            else:
                line["box"] = []

            lines.append(line)

        full_text = "\n".join(ln["text"] for ln in lines)

        return {
            "success": True,
            "text": full_text,
            "lines": lines,
            "total_lines": len(lines),
            "error": None
        }

    except Exception as e:
        logger.exception("OCR 识别异常")
        return {
            "success": False,
            "text": "",
            "lines": [],
            "total_lines": 0,
            "error": f"识别失败: {str(e)}"
        }
