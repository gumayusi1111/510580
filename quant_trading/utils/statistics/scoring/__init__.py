"""
评分系统模块化架构

模块职责:
- config: 评分配置和阈值
- ic_scorer: IC评分逻辑
- stability_scorer: 稳定性评分
- quality_scorer: 数据质量和分布评分
- grading: 评级分配

使用示例:
    from utils.statistics.scoring import FactorScoring

    scoring = FactorScoring()
    result = scoring.calculate_evaluation_score(ic_results, basic_stats, stability_stats)
"""

from .config import (
    ScoringConfig,
    ScoringWeights,
    ICThresholds,
    GradeThresholds,
    DEFAULT_CONFIG
)
from .ic_scorer import ICScorer
from .stability_scorer import StabilityScorer
from .quality_scorer import QualityScorer
from .grading import FactorGrader


class FactorScoring:
    """
    因子评分系统主类 - 模块化版本

    集成所有评分子模块，提供统一接口
    """

    def __init__(self, config=None):
        """
        初始化评分系统

        Args:
            config: 评分配置，默认使用DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG

        # 初始化各评分器
        self.ic_scorer = ICScorer(self.config)
        self.stability_scorer = StabilityScorer(self.config)
        self.quality_scorer = QualityScorer(self.config)
        self.grader = FactorGrader(self.config)

    def calculate_evaluation_score(self, ic_results: dict, basic_stats: dict,
                                  stability_stats: dict) -> dict:
        """
        计算因子综合评估分数 (主入口)

        Args:
            ic_results: IC分析结果
            basic_stats: 基本统计量
            stability_stats: 稳定性统计

        Returns:
            评估分数字典
        """
        scores = {
            'ic_score': 0.0,
            'stability_score': 0.0,
            'data_quality_score': 0.0,
            'distribution_score': 0.0,
            'consistency_score': 0.0
        }

        try:
            # 1. IC评分 (50%)
            scores['ic_score'] = self.ic_scorer.calculate_ic_score(ic_results)

            # 2. 稳定性评分 (20%)
            scores['stability_score'] = self.stability_scorer.calculate_stability_score(
                stability_stats, basic_stats
            )

            # 3. 数据质量评分 (10%)
            scores['data_quality_score'] = self.quality_scorer.calculate_data_quality_score(
                basic_stats
            )

            # 4. 分布合理性评分 (15%)
            scores['distribution_score'] = self.quality_scorer.calculate_distribution_score(
                basic_stats
            )

            # 5. 一致性表现评分 (5%)
            scores['consistency_score'] = self.quality_scorer.calculate_consistency_score(
                basic_stats, stability_stats
            )

            # 总分计算
            total_score = sum(scores.values())
            scores['total_score'] = total_score

            # 评级分配
            grade = self.grader.assign_grade(total_score, ic_results)
            scores['grade'] = grade
            scores['grade_details'] = self.grader.get_grade_details(grade)

            return scores

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"评分计算失败: {e}")
            return {
                'error': 'scoring_failed',
                'total_score': 0.0,
                'grade': 'F',
                **scores
            }


__all__ = [
    'FactorScoring',
    'ScoringConfig',
    'ScoringWeights',
    'ICThresholds',
    'GradeThresholds',
    'DEFAULT_CONFIG',
    'ICScorer',
    'StabilityScorer',
    'QualityScorer',
    'FactorGrader'
]