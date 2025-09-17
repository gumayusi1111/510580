"""
CCI - 顺势指标因子模块
Commodity Channel Index - 价格偏离度指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("cci_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

CCI = core_module.CCI

# 保持向后兼容性
__all__ = ['CCI']

# 工厂函数
def create_cci(period=None):
    """创建CCI因子实例"""
    return CCI({"period": period} if period else None)

def create_default_cci():
    """创建默认配置的CCI因子实例"""
    return CCI()

def create_custom_cci(period):
    """创建自定义周期的CCI因子实例"""
    return CCI({"period": period})