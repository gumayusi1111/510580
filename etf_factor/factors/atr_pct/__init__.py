"""
ATR_PCT - ATR百分比因子模块
ATR Percentage - ATR相对于价格的百分比的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("atr_pct_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

ATR_PCT = core_module.ATR_PCT

# 保持向后兼容性
__all__ = ['ATR_PCT']

# 工厂函数
def create_atr_pct(periods=None):
    """创建ATR百分比因子实例"""
    return ATR_PCT({"periods": periods} if periods else None)

def create_default_atr_pct():
    """创建默认配置的ATR_PCT因子实例"""
    return ATR_PCT()

def create_custom_atr_pct(periods):
    """创建自定义周期的ATR_PCT因子实例"""
    return ATR_PCT({"periods": periods})