"""
样本外验证模块
提供因子健壮性验证和过拟合检测功能
"""

from .cross_validator import FactorCrossValidator, ValidationResult

__all__ = [
    'FactorCrossValidator',
    'ValidationResult'
]