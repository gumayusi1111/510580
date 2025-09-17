"""
STOCH - 随机震荡器因子模块
Stochastic Oscillator - 动量震荡指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("stoch_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

STOCH = core_module.STOCH

# 保持向后兼容性
__all__ = ['STOCH']

# 工厂函数
def create_stoch(k_period=None, d_period=None):
    """创建随机震荡器因子实例"""
    if k_period is None and d_period is None:
        return STOCH()
    params = {}
    if k_period is not None:
        params["k_period"] = k_period
    if d_period is not None:
        params["d_period"] = d_period
    return STOCH(params)

def create_default_stoch():
    """创建默认配置的随机震荡器因子实例"""
    return STOCH()

def create_custom_stoch(k_period, d_period=3):
    """创建自定义参数的随机震荡器因子实例"""
    return STOCH({"k_period": k_period, "d_period": d_period})