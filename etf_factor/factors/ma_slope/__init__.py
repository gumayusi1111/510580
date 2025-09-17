"""
MA_SLOPE - 移动均线斜率因子模块
Moving Average Slope - 反映移动均线趋势方向和强度的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("ma_slope_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

MA_SLOPE = core_module.MA_SLOPE

# 保持向后兼容性
__all__ = ['MA_SLOPE']

# 工厂函数
def create_ma_slope(periods=None):
    """创建移动均线斜率因子实例"""
    return MA_SLOPE({"periods": periods} if periods else None)

def create_default_ma_slope():
    """创建默认配置的MA_SLOPE因子实例"""
    return MA_SLOPE()

def create_custom_ma_slope(periods):
    """创建自定义周期的MA_SLOPE因子实例"""
    return MA_SLOPE({"periods": periods})