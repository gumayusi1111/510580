"""
TR - 真实波幅因子模块
True Range - 衡量价格波动幅度的指标的模块化实现
"""

# 使用绝对路径导入避免模块名冲突
import os
import sys
import importlib.util

# 直接使用绝对路径导入core模块
current_dir = os.path.dirname(__file__)
core_path = os.path.join(current_dir, 'core.py')

spec = importlib.util.spec_from_file_location("tr_core", core_path)
core_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core_module)

TR = core_module.TR

# 保持向后兼容性
__all__ = ['TR']

# 工厂函数
def create_tr():
    """创建真实波幅因子实例"""
    return TR()

def create_default_tr():
    """创建默认配置的TR因子实例"""
    return TR()