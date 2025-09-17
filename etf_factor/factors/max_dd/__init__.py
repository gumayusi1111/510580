"""
MAX_DD - 最大回撤因子模块
Maximum Drawdown - 指定周期内的最大回撤率的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("max_dd_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

MAX_DD = core_module.MAX_DD

# 保持向后兼容性
__all__ = ['MAX_DD']

# 工厂函数
def create_max_dd(periods=None):
    """创建最大回撤因子实例"""
    if periods is None:
        return MAX_DD()
    params = {"periods": periods}
    return MAX_DD(params)

def create_default_max_dd():
    """创建默认配置的最大回撤因子实例"""
    return MAX_DD()

def create_custom_max_dd(periods):
    """创建自定义周期的最大回撤因子实例"""
    return MAX_DD({"periods": periods})