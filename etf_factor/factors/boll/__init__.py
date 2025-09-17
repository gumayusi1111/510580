"""
BOLL - 布林带因子模块
Bollinger Bands - 波动率指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("boll_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

BOLL = core_module.BOLL

# 保持向后兼容性
__all__ = ['BOLL']

# 工厂函数
def create_boll(period=None, std_dev=None):
    """创建布林带因子实例"""
    if period is None and std_dev is None:
        return BOLL()
    params = {}
    if period is not None:
        params["period"] = period
    if std_dev is not None:
        params["std_dev"] = std_dev
    return BOLL(params)

def create_default_boll():
    """创建默认配置的布林带因子实例"""
    return BOLL()

def create_custom_boll(period, std_dev=2):
    """创建自定义参数的布林带因子实例"""
    return BOLL({"period": period, "std_dev": std_dev})