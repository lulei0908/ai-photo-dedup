# AI 智能清理重复照片

一个基于 AI 技术的智能重复照片清理工具，能够自动识别并清理相似或重复的照片。

## 功能特性

- 🔍 **智能识别**：使用感知哈希算法 (pHash) 和图像特征对比
- 🎯 **高精度匹配**：支持多种相似度阈值设置
- 📁 **批量处理**：支持递归扫描文件夹
- 🖼️ **多格式支持**：JPG、PNG、GIF、BMP、WebP 等
- ⚡ **快速扫描**：多线程并行处理
- 🛡️ **安全删除**：可预览后再删除，支持移动到回收站

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python photo_dedup.py /path/to/photos
```

### 高级选项

```bash
# 设置相似度阈值（默认 0.9）
python photo_dedup.py /path/to/photos --threshold 0.85

# 递归扫描子目录
python photo_dedup.py /path/to/photos --recursive

# 自动删除重复照片（保留质量最高的）
python photo_dedup.py /path/to/photos --auto-delete

# 将重复照片移动到指定文件夹
python photo_dedup.py /path/to/photos --move-to ./duplicates
```

## 工作原理

1. **图像哈希计算**：使用感知哈希算法计算每张照片的指纹
2. **相似度比较**：通过汉明距离计算图片相似度
3. **分组聚类**：将相似照片归类到同一组
4. **质量评估**：基于分辨率、文件大小、清晰度选择最佳照片
5. **清理执行**：根据用户选择删除或移动重复照片

## 项目结构

```
ai-photo-dedup/
├── photo_dedup.py      # 主程序
├── utils/
│   ├── __init__.py
│   ├── hasher.py       # 图像哈希算法
│   ├── comparator.py   # 相似度比较
│   └── quality.py      # 图像质量评估
├── requirements.txt
├── README.md
└── LICENSE
```

## 依赖

- Python 3.8+
- Pillow
- imagehash
- numpy
- tqdm

## 许可证

MIT License
