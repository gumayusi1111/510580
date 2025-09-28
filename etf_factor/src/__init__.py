"""
ETF Factor Library - Core Module
向量化因子计算库
"""

__version__ = "1.0.0"
__author__ = "Factor Library Team"

import os
import sys

# 动态导入解决相对导入问题
try:
    from .base_factor import BaseFactor
    from .engine import VectorizedEngine
    from .data_loader import DataLoader
    from .data_writer import DataWriter
    from .cache import CacheManager
    from .config import GlobalConfig, config
except ImportError:
    # 添加当前目录到sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from base_factor import BaseFactor
    from engine import VectorizedEngine
    from data_loader import DataLoader
    from data_writer import DataWriter
    from cache import CacheManager
    from config import GlobalConfig, config

# 应用全局pandas配置
config.apply_pandas_options()

__all__ = [
    "BaseFactor",
    "VectorizedEngine", 
    "DataLoader",
    "DataWriter",
    "CacheManager",
    "GlobalConfig",
    "config"
]