"""
ATR - 平均真实波幅因子模块
Average True Range - 波动性指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("atr_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

ATR = core_module.ATR

# 保持向后兼容性
__all__ = ['ATR']

# 工厂函数
def create_atr(periods=None):
    """创建ATR因子实例"""
    return ATR({"periods": periods} if periods else None)

def create_default_atr():
    """创建默认配置的ATR因子实例"""
    return ATR()

def create_custom_atr(periods):
    """创建自定义周期的ATR因子实例"""
    return ATR({"periods": periods})