"""
VOLUME_RATIO - 量比因子模块
Volume Ratio - 当日成交量与前N日平均成交量的比值的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("volume_ratio_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

VOLUME_RATIO = core_module.VOLUME_RATIO

# 保持向后兼容性
__all__ = ['VOLUME_RATIO']

# 工厂函数
def create_volume_ratio(period=None):
    """创建量比因子实例"""
    if period is None:
        return VOLUME_RATIO()
    params = {"period": period}
    return VOLUME_RATIO(params)

def create_default_volume_ratio():
    """创建默认配置的量比因子实例"""
    return VOLUME_RATIO()

def create_custom_volume_ratio(period):
    """创建自定义周期的量比因子实例"""
    return VOLUME_RATIO({"period": period})