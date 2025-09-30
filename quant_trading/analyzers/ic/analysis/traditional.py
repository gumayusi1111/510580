"""
传统IC分析方法
使用固定前瞻期(1,3,5,10)进行IC计算
"""

import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TraditionalICAnalysis:
    """传统IC分析方法（兼容性保留）"""

    def __init__(self, analyzer):
        """
        Args:
            analyzer: ICAnalyzer实例，提供calculate_ic等基础方法
        """
        self.analyzer = analyzer

    def analyze(self, factor_data: pd.Series, returns: pd.Series,
                forward_periods: List[int] = None) -> Dict:
        """
        传统IC分析

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            forward_periods: 前瞻期数列表，默认[1,3,5,10]

        Returns:
            IC分析结果字典
        """
        if forward_periods is None:
            forward_periods = [1, 3, 5, 10]  # 标准前瞻期

        # 确保factor_data是Series类型
        if isinstance(factor_data, pd.DataFrame):
            if len(factor_data.columns) == 1:
                factor_data = factor_data.iloc[:, 0]
            else:
                raise ValueError(f"传入的DataFrame包含多列，无法确定因子: {factor_data.columns.tolist()}")

        results = {
            'factor_name': getattr(factor_data, 'name', 'unknown_factor'),
            'strategy_type': self.analyzer.strategy_type,
            'window_config': {
                'ic_windows': self.analyzer.window_config.ic_windows,
                'primary_window': self.analyzer.window_config.primary_window,
                'description': self.analyzer.window_config.description
            },
            'ic_analysis': {},
            'rolling_ic': {},
            'multi_window_ic': {},
            'statistics': {}
        }

        for period in forward_periods:
            # 计算IC值
            ic_pearson = self.analyzer.calculate_ic(factor_data, returns, period, "pearson")
            ic_spearman = self.analyzer.calculate_ic(factor_data, returns, period, "spearman")

            results['ic_analysis'][f'period_{period}'] = {
                'ic_pearson': ic_pearson,
                'ic_spearman': ic_spearman
            }

            # 计算滚动IC
            rolling_ic_pearson = self.analyzer.calculate_rolling_ic(
                factor_data, returns, window=None, forward_periods=period, method="pearson"
            )

            results['rolling_ic'][f'period_{period}'] = {
                'pearson': rolling_ic_pearson,
                'spearman': rolling_ic_pearson if self.analyzer.fast_mode else self.analyzer.calculate_rolling_ic(
                    factor_data, returns, window=None, forward_periods=period, method="spearman"
                )
            }

            # 计算IC统计量
            if self.analyzer.fast_mode:
                ic_stats = self.analyzer.statistics.calculate_ic_statistics_batch(rolling_ic_pearson)
            else:
                ic_stats = self.analyzer.statistics.calculate_ic_statistics(rolling_ic_pearson)

            results['statistics'][f'period_{period}'] = ic_stats

        return results