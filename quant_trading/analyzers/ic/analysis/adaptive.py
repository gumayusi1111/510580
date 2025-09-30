"""
适应性IC分析方法
根据因子类型自动选择合适的前瞻期进行IC计算
"""

import logging
import warnings
from typing import Dict, List

import numpy as np
import pandas as pd

from .result import AdaptiveICResult

# 抑制运行时警告
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")

logger = logging.getLogger(__name__)


class AdaptiveICAnalysis:
    """智能适应性IC分析（推荐方法）"""

    def __init__(self, analyzer):
        """
        Args:
            analyzer: ICAnalyzer实例
        """
        self.analyzer = analyzer

    def analyze(self, factor_data: pd.Series, returns: pd.Series) -> AdaptiveICResult:
        """
        智能适应性IC分析

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列

        Returns:
            适应性IC分析结果
        """
        if not self.analyzer.enable_adaptive or not self.analyzer.classifier:
            logger.warning("适应性分析未启用，回退到传统方法")
            from .traditional import TraditionalICAnalysis

            traditional = TraditionalICAnalysis(self.analyzer)
            traditional_result = traditional.analyze(factor_data, returns)
            return self._convert_to_adaptive_result(traditional_result)

        factor_name = getattr(factor_data, "name", "unknown_factor")
        logger.info(f"开始适应性IC分析: {factor_name}")

        # 1. 智能因子分类
        category = self.analyzer.classifier.classify_factor(factor_name)
        logger.info(
            f"因子分类: {category.name}, 适应性前瞻期: {category.forward_periods}"
        )

        # 2. 使用适应性前瞻期进行IC分析
        results = {
            "factor_name": factor_name,
            "factor_category": category.name,
            "adaptive_periods": category.forward_periods,
            "primary_period": category.primary_period,
            "statistics": {},
            "rolling_ic": {},
            "category_info": {
                "description": category.description,
                "evaluation_focus": category.evaluation_focus,
            },
        }

        for period in category.forward_periods:
            # 计算滚动IC（使用快速向量化方法）
            if self.analyzer.fast_mode:
                rolling_ic_pearson = (
                    self.analyzer.calculator.calculate_rolling_ic_vectorized(
                        factor_data,
                        returns,
                        window=self.analyzer.window_config.primary_window,
                        forward_periods=period,
                    )
                )
                rolling_ic_spearman = rolling_ic_pearson  # 快速模式下简化
            else:
                rolling_ic_pearson = self.analyzer.calculate_rolling_ic(
                    factor_data,
                    returns,
                    window=self.analyzer.window_config.primary_window,
                    forward_periods=period,
                    method="pearson",
                )
                rolling_ic_spearman = self.analyzer.calculate_rolling_ic(
                    factor_data,
                    returns,
                    window=self.analyzer.window_config.primary_window,
                    forward_periods=period,
                    method="spearman",
                )

            results["rolling_ic"][f"period_{period}"] = {
                "pearson": rolling_ic_pearson,
                "spearman": rolling_ic_spearman,
            }

            # 计算统计量（使用快速方法）
            if self.analyzer.fast_mode:
                ic_stats = self.analyzer.statistics.calculate_ic_statistics_batch(
                    rolling_ic_pearson
                )
            else:
                ic_stats = self.analyzer.statistics.calculate_ic_statistics(
                    rolling_ic_pearson
                )
            results["statistics"][f"period_{period}"] = ic_stats

        # 3. 新旧方法对比（可选）
        comparison_analysis = None
        if self.analyzer.enable_comparison:
            try:
                comparison_analysis = self._compare_with_original_method(
                    factor_data, returns, category.forward_periods
                )
                results["category_info"]["comparison"] = comparison_analysis
                logger.info(
                    f"对比分析完成，改进幅度: {comparison_analysis.get('improvement', {}).get('improvement_pct', 0):.1f}%"
                )
            except Exception as e:
                logger.warning(f"对比分析失败: {e}")

        return AdaptiveICResult(
            factor_name=factor_name,
            factor_category=category.name,
            adaptive_periods=category.forward_periods,
            primary_period=category.primary_period,
            statistics=results["statistics"],
            rolling_ic=results["rolling_ic"],
            category_info=results["category_info"],
            comparison_analysis=comparison_analysis,
        )

    def _compare_with_original_method(
        self, factor_data: pd.Series, returns: pd.Series, adaptive_periods: List[int]
    ) -> Dict:
        """新旧方法对比分析"""
        original_periods = [1, 3, 5, 10]  # 原始固定前瞻期

        # 原始方法的最佳IC
        original_ics = []
        for period in original_periods:
            ic = self.analyzer.calculate_ic(factor_data, returns, period, "pearson")
            if not np.isnan(ic):
                original_ics.append(abs(ic))

        best_original_ic = max(original_ics) if original_ics else 0

        # 适应性方法的最佳IC
        adaptive_ics = []
        for period in adaptive_periods:
            ic = self.analyzer.calculate_ic(factor_data, returns, period, "pearson")
            if not np.isnan(ic):
                adaptive_ics.append(abs(ic))

        best_adaptive_ic = max(adaptive_ics) if adaptive_ics else 0

        # 计算改进
        if best_original_ic > 0:
            improvement_pct = (
                (best_adaptive_ic - best_original_ic) / best_original_ic
            ) * 100
        else:
            improvement_pct = 0

        return {
            "original_best_ic": best_original_ic,
            "adaptive_best_ic": best_adaptive_ic,
            "improvement": {
                "absolute": best_adaptive_ic - best_original_ic,
                "improvement_pct": improvement_pct,
            },
            "original_periods": original_periods,
            "adaptive_periods": adaptive_periods,
        }

    def _convert_to_adaptive_result(self, traditional_result: Dict) -> AdaptiveICResult:
        """将传统结果转换为适应性结果格式"""
        return AdaptiveICResult(
            factor_name=traditional_result.get("factor_name", "unknown"),
            factor_category="unknown",
            adaptive_periods=[1, 3, 5, 10],
            primary_period=1,
            statistics=traditional_result.get("statistics", {}),
            rolling_ic=traditional_result.get("rolling_ic", {}),
            category_info={"description": "传统固定前瞻期分析"},
            comparison_analysis=None,
        )
