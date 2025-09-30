"""
IC分析结果数据结构
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AdaptiveICResult:
    """适应性IC分析结果"""
    factor_name: str
    factor_category: str
    adaptive_periods: List[int]
    primary_period: int
    statistics: Dict
    rolling_ic: Dict
    category_info: Dict
    comparison_analysis: Optional[Dict] = None