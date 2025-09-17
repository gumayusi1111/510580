"""
MA_DIFF - 移动均线差值因子模块
Moving Average Difference - 不同周期均线间的差值的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("ma_diff_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

MA_DIFF = core_module.MA_DIFF

# 保持向后兼容性
__all__ = ['MA_DIFF']

# 工厂函数
def create_ma_diff(pairs=None):
    """创建移动均线差值因子实例"""
    if pairs is None:
        return MA_DIFF()
    params = {"pairs": pairs}
    return MA_DIFF(params)

def create_default_ma_diff():
    """创建默认配置的移动均线差值因子实例"""
    return MA_DIFF()

def create_custom_ma_diff(pairs):
    """创建自定义差值对的移动均线差值因子实例"""
    return MA_DIFF({"pairs": pairs})