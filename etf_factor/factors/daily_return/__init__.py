"""
DAILY_RETURN - 日收益率因子模块
Daily Return - 单日价格变化百分比的模块化实现
"""

# 修复相对导入问题
import os
import sys

# 添加当前目录到路径
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import DAILY_RETURN

# 保持向后兼容性 - 原有的导入方式仍然有效
__all__ = ['DAILY_RETURN']

# 工厂函数
def create_daily_return():
    """创建日收益率因子实例"""
    return DAILY_RETURN()