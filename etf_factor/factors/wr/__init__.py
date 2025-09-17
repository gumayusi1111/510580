"""
WR - 威廉指标因子模块
Williams %R - 超买超卖指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("wr_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

WR = core_module.WR

# 保持向后兼容性
__all__ = ['WR']

# 工厂函数
def create_wr(period=None):
    """创建威廉指标因子实例"""
    return WR({"period": period} if period else None)

def create_default_wr():
    """创建默认配置的威廉指标因子实例"""
    return WR()

def create_custom_wr(period):
    """创建自定义周期的威廉指标因子实例"""
    return WR({"period": period})