"""
WMA - 加权移动均线因子模块
Weighted Moving Average - 线性权重移动平均的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("wma_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

WMA = core_module.WMA

# 保持向后兼容性
__all__ = ['WMA']

# 工厂函数
def create_wma(periods=None):
    """创建WMA因子实例"""
    return WMA({"periods": periods} if periods else None)

def create_default_wma():
    """创建默认配置的WMA因子实例"""
    return WMA()

def create_custom_wma(periods):
    """创建自定义周期的WMA因子实例"""
    return WMA({"periods": periods})