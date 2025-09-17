"""
OBV - 能量潮指标因子模块
On-Balance Volume - 成交量指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("obv_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

OBV = core_module.OBV

# 保持向后兼容性
__all__ = ['OBV']

# 工厂函数
def create_obv():
    """创建OBV因子实例"""
    return OBV()

def create_default_obv():
    """创建默认配置的OBV因子实例"""
    return OBV()