"""
IC分析模块 - 模块化架构

包含:
- result: IC分析结果数据结构
- traditional: 传统固定前瞻期IC分析
- adaptive: 智能适应性IC分析
- batch: 批量分析和因子排序
"""

from .result import AdaptiveICResult
from .traditional import TraditionalICAnalysis
from .adaptive import AdaptiveICAnalysis
from .batch import BatchICAnalysis

__all__ = [
    'AdaptiveICResult',
    'TraditionalICAnalysis',
    'AdaptiveICAnalysis',
    'BatchICAnalysis'
]