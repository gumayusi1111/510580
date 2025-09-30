"""
数据质量和分布评分模块
负责计算数据质量、分布合理性和一致性评分
"""

import logging
from typing import Dict
from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    数据质量和分布评分器

    负责计算数据质量、分布合理性和一致性评分

    Attributes:
        config: 评分配置实例
    """

    def __init__(self, config=None):
        """
        初始化质量评分器

        Args:
            config: 评分配置实例，默认使用DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG

    def calculate_data_quality_score(self, basic_stats: Dict) -> float:
        """
        计算数据质量评分(优化后提高区分度)

        Args:
            basic_stats: 基本统计量

        Returns:
            数据质量评分 (0-权重最大值)
        """
        score = 0.0
        t = self.config.quality_thresholds

        if not basic_stats:
            return 0.0

        # 1. 缺失率评分 (50%权重)
        missing_ratio = basic_stats.get('missing_ratio', 1.0)
        if missing_ratio == t.missing_perfect:
            score += 0.5
        elif missing_ratio < t.missing_excellent:
            score += 0.45
        elif missing_ratio < t.missing_good:
            score += 0.35
        elif missing_ratio < t.missing_acceptable:
            score += 0.25
        else:
            score += 0.10

        # 2. 异常值比例评分 (30%权重)
        outlier_ratio = basic_stats.get('outlier_ratio', 0.5)
        if outlier_ratio < t.outlier_excellent:
            score += 0.30
        elif outlier_ratio < t.outlier_good:
            score += 0.25
        elif outlier_ratio < t.outlier_acceptable:
            score += 0.20
        elif outlier_ratio < t.outlier_warning:
            score += 0.10
        else:
            score += 0.05

        # 3. 数据变化性评分 (20%权重)
        std = basic_stats.get('std', 0)
        mean = abs(basic_stats.get('mean', 0))

        if std > 0 and mean > 0:
            cv = std / mean
            if t.cv_min < cv < t.cv_max:  # 合理变异系数
                score += 0.20
            elif cv <= t.cv_min:  # 变化太小
                score += 0.05
            else:  # 变化太大
                score += 0.10
        elif std > 0:
            score += 0.15  # 有变化但均值为0

        # 限制最大值并应用权重
        final_score = min(1.0, score)
        return final_score * self.config.weights.data_quality

    def calculate_distribution_score(self, basic_stats: Dict) -> float:
        """
        计算分布合理性评分(优化后提高区分度)

        Args:
            basic_stats: 基本统计量

        Returns:
            分布评分 (0-权重最大值)
        """
        score = 0.05  # 基础分
        t = self.config.distribution_thresholds

        if not basic_stats:
            return score * self.config.weights.distribution

        skewness = abs(basic_stats.get('skewness', 0))
        kurtosis = abs(basic_stats.get('kurtosis', 0))

        # 基于偏度和峰度的分层评分
        if skewness < t.skew_excellent and kurtosis < t.kurt_excellent:
            score = 1.0
        elif skewness < t.skew_good and kurtosis < t.kurt_good:
            score = 0.85
        elif skewness < t.skew_acceptable and kurtosis < t.kurt_acceptable:
            score = 0.65
        elif skewness < t.skew_warning and kurtosis < t.kurt_warning:
            score = 0.45
        elif skewness < t.skew_poor and kurtosis < t.kurt_poor:
            score = 0.25
        else:
            score = 0.10

        return score * self.config.weights.distribution

    def calculate_consistency_score(self, basic_stats: Dict, stability_stats: Dict) -> float:
        """
        计算一致性评分

        Args:
            basic_stats: 基本统计量
            stability_stats: 稳定性统计

        Returns:
            一致性评分 (0-权重最大值)
        """
        score = 0.5  # 基础分

        if basic_stats and stability_stats:
            # 数据质量与稳定性的一致性
            missing_ratio = basic_stats.get('missing_ratio', 0.5)
            stability_score = stability_stats.get('stability_score', 0.5)

            # 高质量数据应该有高稳定性
            if missing_ratio < 0.1 and stability_score > 0.7:
                score = 1.0
            elif missing_ratio < 0.2 and stability_score > 0.5:
                score = 0.8
            else:
                score = 0.6

        return score * self.config.weights.consistency