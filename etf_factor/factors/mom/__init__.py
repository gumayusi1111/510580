"""
MOM - 动量指标因子模块
Momentum - 价格变化绝对值的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("mom_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

MOM = core_module.MOM

# 保持向后兼容性
__all__ = ['MOM']

# 工厂函数
def create_mom(periods=None):
    """创建动量指标因子实例"""
    return MOM({"periods": periods} if periods else None)

def create_default_mom():
    """创建默认配置的MOM因子实例"""
    return MOM()

def create_custom_mom(periods):
    """创建自定义周期的MOM因子实例"""
    return MOM({"periods": periods})