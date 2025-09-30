"""
IC分析模块 - 重构版
信息系数(Information Coefficient)分析

主要接口：
- ICAnalyzer: 统一IC分析器（集成智能分类和适应性分析）
- create_ic_analyzer: 工厂函数
- AdaptiveICResult: 适应性IC结果数据类

📦 模块结构:
- analyzer.py: 主分析器类(254行)
- analysis/: 子模块
  - result.py: 数据结构(18行)
  - traditional.py: 传统IC分析(89行)
  - adaptive.py: 适应性IC分析(172行)
  - batch.py: 批量分析(128行)
"""

from .analyzer import ICAnalyzer, AdaptiveICResult, create_ic_analyzer
from .core import ICCalculator, ICStatistics

__all__ = [
    "ICAnalyzer",
    "AdaptiveICResult",
    "create_ic_analyzer",
    "ICCalculator",
    "ICStatistics"
]