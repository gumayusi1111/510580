"""
SMA - 简单移动均线因子模块
Simple Moving Average - 趋势跟踪指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("sma_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

SMA = core_module.SMA

# 保持向后兼容性
__all__ = ['SMA']

# 工厂函数
def create_sma(periods=None):
    """创建SMA因子实例"""
    return SMA({"periods": periods} if periods else None)

def create_default_sma():
    """创建默认配置的SMA因子实例"""
    return SMA()

def create_custom_sma(periods):
    """创建自定义周期的SMA因子实例"""
    return SMA({"periods": periods})