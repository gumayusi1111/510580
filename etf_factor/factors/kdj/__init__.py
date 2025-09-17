"""
KDJ - 随机指标因子模块
KDJ Stochastic - 基于随机理论的技术指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("kdj_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

KDJ = core_module.KDJ

# 保持向后兼容性
__all__ = ['KDJ']

# 工厂函数
def create_kdj(period=None):
    """创建KDJ随机指标因子实例"""
    if period is None:
        return KDJ()
    params = {"period": period}
    return KDJ(params)

def create_default_kdj():
    """创建默认配置的KDJ因子实例"""
    return KDJ()

def create_custom_kdj(period):
    """创建自定义周期的KDJ因子实例"""
    return KDJ({"period": period})