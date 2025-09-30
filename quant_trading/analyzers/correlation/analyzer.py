"""
相关性分析器 - 重构简化版本
用于分析因子间的相关性关系
"""

import pandas as pd
from typing import Dict, List
import logging
from .core import CorrelationCalculator, RedundancyDetector
from .selection import FactorSelector

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """因子相关性分析器 - 专注于高级分析逻辑"""

    def __init__(self, correlation_threshold: float = 0.8):
        """
        初始化相关性分析器

        Args:
            correlation_threshold: 高相关性阈值（金融标准：0.8）
        """
        if not 0.5 <= correlation_threshold <= 1.0:
            raise ValueError("相关性阈值应在0.5-1.0之间")

        self.correlation_threshold = correlation_threshold
        self.calculator = CorrelationCalculator()
        self.detector = RedundancyDetector()
        self.selector = FactorSelector()

    def calculate_correlation_matrix(self, factor_data: pd.DataFrame,
                                   method: str = "pearson") -> pd.DataFrame:
        """
        计算因子相关性矩阵

        Args:
            factor_data: 因子数据DataFrame
            method: 相关性计算方法 ['pearson', 'spearman', 'kendall']

        Returns:
            相关性矩阵
        """
        return self.calculator.calculate_correlation_matrix(factor_data, method)

    def find_high_correlation_pairs(self, correlation_matrix: pd.DataFrame,
                                  threshold: float = None) -> List:
        """
        找出高相关性因子对

        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值，默认使用初始化时的阈值

        Returns:
            高相关性因子对列表
        """
        if threshold is None:
            threshold = self.correlation_threshold

        return self.calculator.find_high_correlation_pairs(correlation_matrix, threshold)

    def identify_redundant_factors(self, correlation_matrix: pd.DataFrame,
                                 threshold: float = None) -> Dict:
        """
        识别冗余因子组

        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值

        Returns:
            冗余因子组字典
        """
        if threshold is None:
            threshold = self.correlation_threshold

        return self.detector.identify_redundant_groups(correlation_matrix, threshold)

    def suggest_factor_selection(self, correlation_matrix: pd.DataFrame,
                               ic_results: Dict = None,
                               selection_method: str = "ic_based") -> List[str]:
        """
        基于相关性分析建议因子选择

        Args:
            correlation_matrix: 相关性矩阵
            ic_results: IC分析结果（可选）
            selection_method: 选择方法

        Returns:
            建议保留的因子列表
        """
        return self.selector.suggest_factor_selection(
            correlation_matrix, ic_results, selection_method, self.correlation_threshold
        )

    def analyze_correlation_structure(self, factor_data: pd.DataFrame) -> Dict:
        """
        全面分析因子相关性结构

        Args:
            factor_data: 因子数据DataFrame

        Returns:
            相关性分析结果
        """
        results = {
            'correlation_matrix': {},
            'high_correlation_pairs': {},
            'redundant_groups': {},
            'summary_statistics': {}
        }

        # 计算不同方法的相关性矩阵
        methods = ['pearson', 'spearman']

        for method in methods:
            logger.info(f"计算 {method} 相关性矩阵")

            corr_matrix = self.calculate_correlation_matrix(factor_data, method)

            if corr_matrix.empty:
                logger.warning(f"{method} 相关性矩阵计算失败")
                continue

            results['correlation_matrix'][method] = corr_matrix

            # 找出高相关性因子对
            high_corr_pairs = self.find_high_correlation_pairs(corr_matrix)
            results['high_correlation_pairs'][method] = high_corr_pairs

            # 识别冗余因子组
            redundant_groups = self.identify_redundant_factors(corr_matrix)
            results['redundant_groups'][method] = redundant_groups

            # 计算汇总统计
            summary_stats = self.detector.calculate_correlation_summary(corr_matrix)
            results['summary_statistics'][method] = summary_stats

        logger.info("相关性结构分析完成")
        return results

    def validate_factor_selection(self, selected_factors: List[str],
                                correlation_matrix: pd.DataFrame) -> Dict:
        """
        验证因子选择结果

        Args:
            selected_factors: 选择的因子列表
            correlation_matrix: 相关性矩阵

        Returns:
            验证结果
        """
        return self.selector.validate_selection(
            selected_factors, correlation_matrix, self.correlation_threshold
        )

    def get_correlation_summary(self, factor_data: pd.DataFrame) -> Dict:
        """
        获取相关性分析摘要

        Args:
            factor_data: 因子数据DataFrame

        Returns:
            分析摘要
        """
        # 计算pearson相关性矩阵
        corr_matrix = self.calculate_correlation_matrix(factor_data, "pearson")

        if corr_matrix.empty:
            return {'error': 'correlation_calculation_failed'}

        # 基本信息
        summary = {
            'total_factors': len(factor_data.columns),
            'data_points': len(factor_data),
            'correlation_threshold': self.correlation_threshold
        }

        # 高相关性统计
        high_corr_pairs = self.find_high_correlation_pairs(corr_matrix)
        summary['high_correlation_pairs_count'] = len(high_corr_pairs)

        # 冗余组统计
        redundant_groups = self.identify_redundant_factors(corr_matrix)
        summary['redundant_groups_count'] = len(redundant_groups)

        # 计算冗余因子总数
        redundant_factors = set()
        for group in redundant_groups.values():
            redundant_factors.update(group)

        summary['redundant_factors_count'] = len(redundant_factors)
        summary['independent_factors_count'] = len(factor_data.columns) - len(redundant_factors)

        # 相关性分布统计
        corr_stats = self.detector.calculate_correlation_summary(corr_matrix)
        summary['correlation_statistics'] = corr_stats

        return summary