"""
ROC - 变动率指标因子模块
Rate of Change - 价格变动百分比的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("roc_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

ROC = core_module.ROC

# 保持向后兼容性
__all__ = ['ROC']

# 工厂函数
def create_roc(periods=None):
    """创建变动率指标因子实例"""
    return ROC({"periods": periods} if periods else None)

def create_default_roc():
    """创建默认配置的ROC因子实例"""
    return ROC()

def create_custom_roc(periods):
    """创建自定义周期的ROC因子实例"""
    return ROC({"periods": periods})