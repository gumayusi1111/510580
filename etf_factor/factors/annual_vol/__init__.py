"""
ANNUAL_VOL - 年化波动率因子模块
Annualized Volatility - 基于收益率标准差的年化波动率模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("annual_vol_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

ANNUAL_VOL = core_module.ANNUAL_VOL

# 保持向后兼容性
__all__ = ['ANNUAL_VOL']

# 工厂函数
def create_annual_vol(periods=None):
    """创建年化波动率因子实例"""
    return ANNUAL_VOL({"periods": periods} if periods else None)