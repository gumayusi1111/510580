"""
稳定性评分模块
负责计算因子稳定性相关评分
"""

import logging
from typing import Dict
from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class StabilityScorer:
    """
    稳定性评分器

    负责计算因子的稳定性相关评分

    Attributes:
        config: 评分配置实例
    """

    def __init__(self, config=None):
        """
        初始化稳定性评分器

        Args:
            config: 评分配置实例，默认使用DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG

    def calculate_stability_score(self, stability_stats: Dict, basic_stats: Dict) -> float:
        """
        计算增强的稳定性评分

        Args:
            stability_stats: 稳定性统计
            basic_stats: 基本统计量

        Returns:
            稳定性评分 (0-权重最大值)
        """
        score = 0.0

        # 1. 原有稳定性分数 (70%权重)
        if stability_stats and 'stability_score' in stability_stats:
            base_stability = stability_stats['stability_score']
            score += base_stability * 0.7

        # 2. 数据一致性加分 (30%权重)
        if basic_stats:
            std = basic_stats.get('std', 0)
            mean = basic_stats.get('mean', 0)

            # 稳定的变化趋势
            if abs(mean) > 0.001:
                cv = std / abs(mean)
                if cv < 2.0:  # 变异系数合理
                    score += 0.3
                elif cv < 5.0:
                    score += 0.2
                else:
                    score += 0.1

        # 限制最大值为1.0
        final_score = min(1.0, score)

        # 应用权重
        return final_score * self.config.weights.stability