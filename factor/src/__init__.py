"""
ETF Factor Library - Core Module
向量化因子计算库
"""

__version__ = "1.0.0"
__author__ = "Factor Library Team"

from .base_factor import BaseFactor
from .engine import VectorizedEngine
from .data_loader import DataLoader
from .data_writer import DataWriter
from .cache import CacheManager
from .config import GlobalConfig, config

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