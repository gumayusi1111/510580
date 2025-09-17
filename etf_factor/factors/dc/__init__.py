"""
DC - 唐奇安通道因子模块
Donchian Channel - 突破系统指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("dc_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

DC = core_module.DC

# 保持向后兼容性
__all__ = ['DC']

# 工厂函数
def create_dc(period=None):
    """创建唐奇安通道因子实例"""
    if period is None:
        return DC()
    params = {"period": period}
    return DC(params)

def create_default_dc():
    """创建默认配置的唐奇安通道因子实例"""
    return DC()

def create_custom_dc(period):
    """创建自定义周期的唐奇安通道因子实例"""
    return DC({"period": period})