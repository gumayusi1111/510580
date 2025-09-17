"""
VMA - 成交量移动均线因子模块
Volume Moving Average - 分析量能趋势的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("vma_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

VMA = core_module.VMA

# 保持向后兼容性
__all__ = ['VMA']

# 工厂函数
def create_vma(periods=None):
    """创建成交量移动均线因子实例"""
    return VMA({"periods": periods} if periods else None)

def create_default_vma():
    """创建默认配置的VMA因子实例"""
    return VMA()

def create_custom_vma(periods):
    """创建自定义周期的VMA因子实例"""
    return VMA({"periods": periods})