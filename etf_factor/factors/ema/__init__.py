"""
EMA - 指数移动均线因子模块
Exponential Moving Average - 对近期价格给予更高权重的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("ema_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

EMA = core_module.EMA

# 保持向后兼容性
__all__ = ['EMA']

# 工厂函数
def create_ema(periods=None):
    """创建指数移动均线因子实例"""
    return EMA({"periods": periods} if periods else None)

def create_default_ema():
    """创建默认配置的EMA因子实例"""
    return EMA()

def create_custom_ema(periods):
    """创建自定义周期的EMA因子实例"""
    return EMA({"periods": periods})