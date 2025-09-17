"""
RSI - 相对强弱指标因子模块
Relative Strength Index - 动量震荡指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("rsi_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

RSI = core_module.RSI

# 保持向后兼容性
__all__ = ['RSI']

# 工厂函数
def create_rsi(periods=None):
    """创建RSI指标因子实例"""
    return RSI({"periods": periods} if periods else None)

def create_default_rsi():
    """创建默认配置的RSI因子实例"""
    return RSI()

def create_custom_rsi(periods):
    """创建自定义周期的RSI因子实例"""
    return RSI({"periods": periods})