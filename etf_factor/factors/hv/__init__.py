"""
HV - 历史波动率因子模块
Historical Volatility - 基于价格收益率标准差的年化波动率的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("hv_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

HV = core_module.HV

# 保持向后兼容性
__all__ = ['HV']

# 工厂函数
def create_hv(periods=None):
    """创建历史波动率因子实例"""
    if periods is None:
        return HV()
    params = {"periods": periods}
    return HV(params)

def create_default_hv():
    """创建默认配置的历史波动率因子实例"""
    return HV()

def create_custom_hv(periods):
    """创建自定义周期的历史波动率因子实例"""
    return HV({"periods": periods})