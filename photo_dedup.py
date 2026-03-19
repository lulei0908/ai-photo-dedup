#!/usr/bin/env python3
"""
AI 智能清理重复照片
使用感知哈希算法识别相似图片
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict
import concurrent.futures
from tqdm import tqdm

try:
    from PIL import Image
    import imagehash
    import numpy as np
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)


class PhotoDedup:
    def __init__(self, threshold: float = 0.9, recursive: bool = False):
        """
        初始化照片去重器
        
        Args:
            threshold: 相似度阈值 (0-1)，越高表示越相似
            recursive: 是否递归扫描子目录
        """
        self.threshold = threshold
        self.recursive = recursive
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.hash_cache: Dict[str, str] = {}
        
    def get_image_files(self, directory: str) -> List[Path]:
        """获取目录中的所有图片文件"""
        path = Path(directory)
        pattern = "**/*" if self.recursive else "*"
        
        files = []
        for ext in self.supported_formats:
            files.extend(path.glob(f"{pattern}{ext}"))
            files.extend(path.glob(f"{pattern}{ext.upper()}"))
        
        return sorted(set(files))
    
    def calculate_hash(self, image_path: Path) -> str:
        """计算图片的感知哈希值"""
        try:
            with Image.open(image_path) as img:
                # 使用 pHash (感知哈希)
                hash_value = str(imagehash.phash(img))
                return hash_value
        except Exception as e:
            print(f"处理图片失败 {image_path}: {e}")
            return None
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """计算两个哈希值的汉明距离"""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def calculate_similarity(self, hash1: str, hash2: str) -> float:
        """计算两个哈希值的相似度 (0-1)"""
        if not hash1 or not hash2:
            return 0.0
        
        max_distance = len(hash1) * 4  # 十六进制字符，每位4bit
        distance = self.hamming_distance(hash1, hash2)
        similarity = 1 - (distance / max_distance)
        return max(0.0, similarity)
    
    def get_image_quality_score(self, image_path: Path) -> float:
        """
        评估图片质量分数
        基于分辨率、文件大小综合评估
        """
        try:
            stat = image_path.stat()
            file_size = stat.st_size
            
            with Image.open(image_path) as img:
                width, height = img.size
                resolution = width * height
                
            # 综合评分：分辨率权重 0.7，文件大小权重 0.3
            # 归一化处理
            resolution_score = min(resolution / (1920 * 1080), 1.0)
            size_score = min(file_size / (2 * 1024 * 1024), 1.0)  # 2MB 为满分
            
            quality_score = resolution_score * 0.7 + size_score * 0.3
            return quality_score
        except Exception:
            return 0.0
    
    def find_duplicates(self, directory: str) -> List[List[Path]]:
        """查找重复照片组"""
        print(f"🔍 正在扫描目录: {directory}")
        image_files = self.get_image_files(directory)
        
        if not image_files:
            print("未找到图片文件")
            return []
        
        print(f"📸 找到 {len(image_files)} 张图片")
        
        # 计算所有图片的哈希值
        print("🧮 正在计算图片哈希...")
        hashes = {}
        for img_path in tqdm(image_files, desc="处理进度"):
            hash_value = self.calculate_hash(img_path)
            if hash_value:
                hashes[img_path] = hash_value
        
        # 分组查找相似图片
        print("🔄 正在比对相似图片...")
        duplicate_groups = []
        processed = set()
        
        paths = list(hashes.keys())
        hash_values = list(hashes.values())
        
        for i, (path1, hash1) in enumerate(tqdm(list(hashes.items()), desc="比对进度")):
            if path1 in processed:
                continue
            
            group = [path1]
            processed.add(path1)
            
            for path2, hash2 in list(hashes.items())[i+1:]:
                if path2 in processed:
                    continue
                
                similarity = self.calculate_similarity(hash1, hash2)
                if similarity >= self.threshold:
                    group.append(path2)
                    processed.add(path2)
            
            if len(group) > 1:
                # 按质量排序，质量最高的排在最前面
                group.sort(key=lambda p: self.get_image_quality_score(p), reverse=True)
                duplicate_groups.append(group)
        
        return duplicate_groups
    
    def preview_duplicates(self, duplicate_groups: List[List[Path]]):
        """预览重复照片组"""
        print(f"\n📋 发现 {len(duplicate_groups)} 组重复照片:\n")
        
        for i, group in enumerate(duplicate_groups, 1):
            print(f"【第 {i} 组】共 {len(group)} 张相似照片")
            for j, img_path in enumerate(group):
                marker = "✅ 保留" if j == 0 else "❌ 重复"
                quality = self.get_image_quality_score(img_path)
                size_mb = img_path.stat().st_size / (1024 * 1024)
                print(f"  {marker} {img_path.name}")
                print(f"     路径: {img_path}")
                print(f"     大小: {size_mb:.2f} MB | 质量分: {quality:.2f}")
            print()
    
    def auto_delete_duplicates(self, duplicate_groups: List[List[Path]], 
                                move_to: str = None) -> Tuple[int, int]:
        """
        自动清理重复照片
        
        Args:
            duplicate_groups: 重复照片组
            move_to: 如果指定，则移动到该目录；否则删除
            
        Returns:
            (删除/移动数量, 释放空间 MB)
        """
        deleted_count = 0
        freed_space = 0
        
        if move_to:
            move_path = Path(move_to)
            move_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 重复照片将移动到: {move_path}")
        
        for group in duplicate_groups:
            # 保留第一张（质量最高的），处理其余
            for img_path in group[1:]:
                try:
                    file_size = img_path.stat().st_size
                    
                    if move_to:
                        # 移动文件
                        dest = move_path / img_path.name
                        # 处理重名
                        counter = 1
                        while dest.exists():
                            stem = img_path.stem
                            suffix = img_path.suffix
                            dest = move_path / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        shutil.move(str(img_path), str(dest))
                        print(f"📦 已移动: {img_path.name}")
                    else:
                        # 删除文件
                        img_path.unlink()
                        print(f"🗑️  已删除: {img_path.name}")
                    
                    deleted_count += 1
                    freed_space += file_size
                    
                except Exception as e:
                    print(f"❌ 处理失败 {img_path}: {e}")
        
        freed_mb = freed_space / (1024 * 1024)
        return deleted_count, freed_mb


def main():
    parser = argparse.ArgumentParser(
        description="AI 智能清理重复照片工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python photo_dedup.py ./photos                    # 扫描并预览重复照片
  python photo_dedup.py ./photos --auto-delete      # 自动删除重复照片
  python photo_dedup.py ./photos --move-to ./dup    # 将重复照片移动到指定目录
  python photo_dedup.py ./photos --threshold 0.85   # 设置相似度阈值为 0.85
        """
    )
    
    parser.add_argument("directory", help="照片目录路径")
    parser.add_argument("--threshold", type=float, default=0.9,
                       help="相似度阈值 (0-1)，默认 0.9，越低越严格")
    parser.add_argument("--recursive", "-r", action="store_true",
                       help="递归扫描子目录")
    parser.add_argument("--auto-delete", action="store_true",
                       help="自动删除重复照片（保留质量最高的）")
    parser.add_argument("--move-to", type=str,
                       help="将重复照片移动到指定目录，而不是删除")
    
    args = parser.parse_args()
    
    # 验证目录
    if not os.path.isdir(args.directory):
        print(f"❌ 目录不存在: {args.directory}")
        sys.exit(1)
    
    # 初始化去重器
    dedup = PhotoDedup(threshold=args.threshold, recursive=args.recursive)
    
    # 查找重复照片
    duplicate_groups = dedup.find_duplicates(args.directory)
    
    if not duplicate_groups:
        print("✨ 未发现重复照片！")
        sys.exit(0)
    
    # 预览结果
    dedup.preview_duplicates(duplicate_groups)
    
    # 执行清理
    if args.auto_delete or args.move_to:
        deleted, freed = dedup.auto_delete_duplicates(duplicate_groups, args.move_to)
        action = "移动" if args.move_to else "删除"
        print(f"\n✅ 完成！已{action} {deleted} 张重复照片，释放 {freed:.2f} MB 空间")
    else:
        print("💡 提示：使用 --auto-delete 自动删除重复照片")
        print("    或使用 --move-to <目录> 将重复照片移动到指定位置")


if __name__ == "__main__":
    main()
