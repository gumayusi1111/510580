"""
BB_WIDTH - 布林带宽度因子模块
Bollinger Band Width - 衡量布林带宽度的波动率指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("bb_width_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

BB_WIDTH = core_module.BB_WIDTH

# 保持向后兼容性
__all__ = ['BB_WIDTH']

# 工厂函数
def create_bb_width(period=None, std_dev=None):
    """创建布林带宽度因子实例"""
    if period is None and std_dev is None:
        return BB_WIDTH()
    params = {}
    if period is not None:
        params["period"] = period
    if std_dev is not None:
        params["std_dev"] = std_dev
    return BB_WIDTH(params)

def create_default_bb_width():
    """创建默认配置的布林带宽度因子实例"""
    return BB_WIDTH()

def create_custom_bb_width(period, std_dev=2):
    """创建自定义参数的布林带宽度因子实例"""
    return BB_WIDTH({"period": period, "std_dev": std_dev})