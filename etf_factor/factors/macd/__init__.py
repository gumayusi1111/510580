"""
MACD - MACD指数平滑移动平均线指标因子模块
Moving Average Convergence Divergence - 经典趋势动量指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("macd_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

MACD = core_module.MACD

# 保持向后兼容性
__all__ = ['MACD']

# 工厂函数
def create_macd(fast_period=None, slow_period=None, signal_period=None):
    """创建MACD指标因子实例"""
    if fast_period is None and slow_period is None and signal_period is None:
        return MACD()
    return MACD({
        "fast_period": fast_period or 12,
        "slow_period": slow_period or 26,
        "signal_period": signal_period or 9
    })

def create_default_macd():
    """创建默认配置的MACD因子实例"""
    return MACD()

def create_custom_macd(fast_period, slow_period, signal_period):
    """创建自定义参数的MACD因子实例"""
    return MACD({
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period
    })