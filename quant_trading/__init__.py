"""
量化交易分析框架

用于ETF因子分析、策略开发和回测的综合性框架
"""

__version__ = "1.0.0"
__author__ = "SingleETFs Project"

from .core import DataManager
from .analyzers import ICAnalyzer, CorrelationAnalyzer
from .strategies import BaseStrategy

__all__ = [
    "DataManager",
    "ICAnalyzer",
    "CorrelationAnalyzer",
    "BaseStrategy"
]