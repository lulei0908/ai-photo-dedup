"""
图像哈希工具模块
"""

from PIL import Image
import imagehash
from pathlib import Path
from typing import Optional


def calculate_phash(image_path: Path, hash_size: int = 8) -> Optional[str]:
    """
    计算图片的感知哈希 (pHash)
    
    Args:
        image_path: 图片路径
        hash_size: 哈希大小，默认 8 (生成 64 位哈希)
    
    Returns:
        十六进制哈希字符串，失败返回 None
    """
    try:
        with Image.open(image_path) as img:
            # 转换为 RGB 模式（处理透明通道等）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 计算感知哈希
            hash_value = imagehash.phash(img, hash_size=hash_size)
            return str(hash_value)
    except Exception as e:
        print(f"计算哈希失败 {image_path}: {e}")
        return None


def calculate_ahash(image_path: Path, hash_size: int = 8) -> Optional[str]:
    """
    计算图片的平均哈希 (aHash)
    
    Args:
        image_path: 图片路径
        hash_size: 哈希大小
    
    Returns:
        十六进制哈希字符串
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            hash_value = imagehash.average_hash(img, hash_size=hash_size)
            return str(hash_value)
    except Exception as e:
        print(f"计算哈希失败 {image_path}: {e}")
        return None


def calculate_dhash(image_path: Path, hash_size: 8) -> Optional[str]:
    """
    计算图片的差值哈希 (dHash)
    
    Args:
        image_path: 图片路径
        hash_size: 哈希大小
    
    Returns:
        十六进制哈希字符串
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            hash_value = imagehash.dhash(img, hash_size=hash_size)
            return str(hash_value)
    except Exception as e:
        print(f"计算哈希失败 {image_path}: {e}")
        return None


def calculate_whash(image_path: Path, hash_size: int = 8) -> Optional[str]:
    """
    计算图片的小波哈希 (wHash)
    
    Args:
        image_path: 图片路径
        hash_size: 哈希大小
    
    Returns:
        十六进制哈希字符串
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            hash_value = imagehash.whash(img, hash_size=hash_size)
            return str(hash_value)
    except Exception as e:
        print(f"计算哈希失败 {image_path}: {e}")
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    计算两个十六进制哈希字符串的汉明距离
    
    Args:
        hash1: 第一个哈希值
        hash2: 第二个哈希值
    
    Returns:
        汉明距离（不同位的数量）
    """
    if len(hash1) != len(hash2):
        raise ValueError("哈希值长度不匹配")
    
    # 十六进制转二进制
    bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
    bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
    
    return sum(c1 != c2 for c1, c2 in zip(bin1, bin2))


def similarity_score(hash1: str, hash2: str) -> float:
    """
    计算两个哈希值的相似度分数 (0-1)
    
    Args:
        hash1: 第一个哈希值
        hash2: 第二个哈希值
    
    Returns:
        相似度分数，1.0 表示完全相同
    """
    try:
        max_bits = len(hash1) * 4  # 十六进制每位 4 bit
        distance = hamming_distance(hash1, hash2)
        similarity = 1 - (distance / max_bits)
        return max(0.0, min(1.0, similarity))
    except Exception:
        return 0.0
