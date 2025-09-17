"""
CUM_RETURN - 累计收益率因子模块
Cumulative Return - 指定周期内累计收益率的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("cum_return_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

CUM_RETURN = core_module.CUM_RETURN

# 保持向后兼容性
__all__ = ['CUM_RETURN']

# 工厂函数
def create_cum_return(periods=None):
    """创建累计收益率因子实例"""
    return CUM_RETURN({"periods": periods} if periods else None)