"""
图像质量评估模块
"""

from PIL import Image
from pathlib import Path
import numpy as np
from typing import Tuple, Optional


def get_image_info(image_path: Path) -> Tuple[int, int, int]:
    """
    获取图片基本信息
    
    Args:
        image_path: 图片路径
    
    Returns:
        (宽度, 高度, 文件大小字节)
    """
    try:
        stat = image_path.stat()
        file_size = stat.st_size
        
        with Image.open(image_path) as img:
            width, height = img.size
            
        return width, height, file_size
    except Exception:
        return 0, 0, 0


def calculate_sharpness(image_path: Path) -> float:
    """
    计算图片清晰度（使用拉普拉斯方差法）
    
    Args:
        image_path: 图片路径
    
    Returns:
        清晰度分数，越高越清晰
    """
    try:
        with Image.open(image_path) as img:
            # 转换为灰度图
            gray = img.convert('L')
            # 转换为 numpy 数组
            img_array = np.array(gray)
            
            # 拉普拉斯算子
            laplacian = np.array([[0, 1, 0],
                                   [1, -4, 1],
                                   [0, 1, 0]])
            
            # 卷积计算
            from scipy import ndimage
            sharpness = ndimage.convolve(img_array, laplacian)
            
            # 返回方差作为清晰度指标
            return float(sharpness.var())
    except Exception:
        return 0.0


def calculate_quality_score(image_path: Path) -> float:
    """
    综合评估图片质量分数
    
    考虑因素：
    - 分辨率
    - 文件大小
    - 清晰度
    
    Args:
        image_path: 图片路径
    
    Returns:
        质量分数 (0-1)
    """
    try:
        width, height, file_size = get_image_info(image_path)
        
        if width == 0 or height == 0:
            return 0.0
        
        resolution = width * height
        
        # 分辨率评分（以 4K 为满分）
        resolution_score = min(resolution / (3840 * 2160), 1.0)
        
        # 文件大小评分（以 5MB 为满分）
        size_score = min(file_size / (5 * 1024 * 1024), 1.0)
        
        # 清晰度评分
        try:
            sharpness = calculate_sharpness(image_path)
            # 归一化清晰度（假设 1000 为较高清晰度）
            sharpness_score = min(sharpness / 1000, 1.0)
        except Exception:
            sharpness_score = 0.5  # 默认中等
        
        # 综合评分（加权平均）
        quality = (
            resolution_score * 0.4 +
            size_score * 0.2 +
            sharpness_score * 0.4
        )
        
        return quality
    except Exception:
        return 0.0


def compare_quality(image1: Path, image2: Path) -> int:
    """
    比较两张图片的质量
    
    Args:
        image1: 第一张图片路径
        image2: 第二张图片路径
    
    Returns:
        正数表示 image1 更好，负数表示 image2 更好，0 表示相同
    """
    score1 = calculate_quality_score(image1)
    score2 = calculate_quality_score(image2)
    return score1 - score2


def select_best_image(images: list) -> Optional[Path]:
    """
    从一组图片中选择质量最好的一张
    
    Args:
        images: 图片路径列表
    
    Returns:
        质量最好的图片路径
    """
    if not images:
        return None
    
    if len(images) == 1:
        return images[0]
    
    best = images[0]
    best_score = calculate_quality_score(best)
    
    for img in images[1:]:
        score = calculate_quality_score(img)
        if score > best_score:
            best = img
            best_score = score
    
    return best
