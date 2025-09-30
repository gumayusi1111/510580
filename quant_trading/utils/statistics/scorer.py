"""
因子评分系统 - 向后兼容包装器

此文件保持向后兼容性，内部委托给模块化的scoring子包

重构说明:
- 原390行代码已拆分为5个模块
- 职责清晰，易于维护和测试
- 现有代码无需修改，自动使用新架构

模块结构:
    scoring/
    ├── config.py          - 评分配置和阈值
    ├── ic_scorer.py       - IC评分逻辑
    ├── stability_scorer.py- 稳定性评分
    ├── quality_scorer.py  - 数据质量和分布评分
    └── grading.py         - 评级分配
"""

# 导入模块化后的类，保持API兼容性
from .scoring import FactorScoring

# 保持向后兼容的导出
__all__ = ['FactorScoring']


# 如果需要直接访问子模块
def get_scoring_config():
    """获取评分配置"""
    from .scoring import DEFAULT_CONFIG
    return DEFAULT_CONFIG


def get_ic_scorer(config=None):
    """获取IC评分器"""
    from .scoring import ICScorer
    return ICScorer(config)


def get_stability_scorer(config=None):
    """获取稳定性评分器"""
    from .scoring import StabilityScorer
    return StabilityScorer(config)


def get_quality_scorer(config=None):
    """获取质量评分器"""
    from .scoring import QualityScorer
    return QualityScorer(config)


def get_grader(config=None):
    """获取评级器"""
    from .scoring import FactorGrader
    return FactorGrader(config)