"""
批量IC分析和因子排序
"""

import pandas as pd
from typing import Dict, List
import logging

from .result import AdaptiveICResult

logger = logging.getLogger(__name__)


class BatchICAnalysis:
    """批量分析所有因子的IC表现"""

    def __init__(self, analyzer):
        """
        Args:
            analyzer: ICAnalyzer实例
        """
        self.analyzer = analyzer

    def analyze_all(self, factor_data: pd.DataFrame, returns: pd.Series,
                   forward_periods: List[int] = None) -> Dict:
        """
        批量分析所有因子

        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率数据序列
            forward_periods: 前瞻期数列表（传统模式使用）

        Returns:
            所有因子的IC分析结果
        """
        if forward_periods is None:
            forward_periods = [1, 3, 5, 10]

        all_results = {}
        total_factors = len(factor_data.columns)

        logger.info(f"开始批量分析 {total_factors} 个因子的IC表现")

        for i, factor_name in enumerate(factor_data.columns, 1):
            logger.info(f"分析进度: {i}/{total_factors} - {factor_name}")

            try:
                factor_series = factor_data[factor_name]

                if self.analyzer.enable_adaptive:
                    # 使用适应性分析
                    from .adaptive import AdaptiveICAnalysis
                    adaptive = AdaptiveICAnalysis(self.analyzer)
                    result = adaptive.analyze(factor_series, returns)
                else:
                    # 使用传统分析
                    from .traditional import TraditionalICAnalysis
                    traditional = TraditionalICAnalysis(self.analyzer)
                    result = traditional.analyze(factor_series, returns, forward_periods)

                all_results[factor_name] = result

            except Exception as e:
                logger.error(f"分析因子 {factor_name} 失败: {e}")
                continue

        logger.info(f"批量分析完成，成功分析 {len(all_results)} 个因子")
        return all_results

    def rank_by_ic(self, analysis_results: Dict, period: int = 1,
                   metric: str = "ic_ir") -> pd.DataFrame:
        """
        根据IC指标对因子进行排序

        Args:
            analysis_results: IC分析结果
            period: 前瞻期数（默认1期）
            metric: 排序指标 ['ic_ir', 'ic_mean', 'ic_abs_mean', 'ic_positive_ratio']

        Returns:
            因子排序结果DataFrame
        """
        ranking_data = []
        period_key = f'period_{period}'

        for factor_name, results in analysis_results.items():
            # 处理适应性结果和传统结果
            if isinstance(results, AdaptiveICResult):
                if period_key not in results.statistics:
                    continue
                stats = results.statistics[period_key]
                # 从滚动IC计算单点IC
                rolling_ic = results.rolling_ic.get(period_key, {}).get('pearson', pd.Series())
                ic_pearson = rolling_ic.mean() if not rolling_ic.empty else 0
                ic_spearman = ic_pearson  # 简化
            else:
                if period_key not in results.get('statistics', {}):
                    continue
                stats = results['statistics'][period_key]
                ic_analysis = results['ic_analysis'][period_key]
                ic_pearson = ic_analysis['ic_pearson']
                ic_spearman = ic_analysis['ic_spearman']

            ranking_data.append({
                'factor': factor_name,
                'ic_pearson': ic_pearson,
                'ic_spearman': ic_spearman,
                'ic_mean': stats['ic_mean'],
                'ic_std': stats['ic_std'],
                'ic_ir': stats['ic_ir'],
                'ic_positive_ratio': stats['ic_positive_ratio'],
                'ic_abs_mean': stats['ic_abs_mean']
            })

        if not ranking_data:
            logger.warning("没有可用的IC分析结果进行排序")
            return pd.DataFrame()

        df = pd.DataFrame(ranking_data)

        # 验证排序指标
        if metric not in df.columns:
            logger.warning(f"未找到排序指标 {metric}，使用ic_ir进行排序")
            metric = 'ic_ir'

        # 按指标排序（降序）
        df = df.sort_values(metric, ascending=False, na_last=True)
        return df.reset_index(drop=True)