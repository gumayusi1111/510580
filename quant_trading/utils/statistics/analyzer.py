"""
统计分析器 - 高级接口
整合统计计算和评分功能的主要接口
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

from .calculator import FactorStatistics
from .scorer import FactorScoring

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """统计分析器 - 统一接口"""

    def __init__(self):
        """初始化统计分析器"""
        self.calculator = FactorStatistics()
        self.scorer = FactorScoring()

    def comprehensive_analysis(self, factor_series: pd.Series,
                             ic_results: Dict = None) -> Dict:
        """
        综合统计分析

        Args:
            factor_series: 因子数据序列
            ic_results: IC分析结果（可选）

        Returns:
            完整的统计分析结果
        """
        try:
            # 基本统计分析
            basic_stats = self.calculator.calculate_basic_statistics(factor_series)
            if 'error' in basic_stats:
                return basic_stats

            # 分布分析
            distribution_analysis = self.calculator.analyze_distribution(factor_series)
            if 'error' in distribution_analysis:
                return distribution_analysis

            # 稳定性分析
            stability_analysis = self.calculator.analyze_factor_stability(factor_series)

            # 如果有IC结果，进行综合评分
            evaluation_scores = {}
            if ic_results:
                evaluation_scores = self.scorer.calculate_evaluation_score(
                    ic_results, basic_stats, stability_analysis
                )

            return {
                'basic_statistics': basic_stats,
                'distribution_analysis': distribution_analysis,
                'stability_analysis': stability_analysis,
                'evaluation_scores': evaluation_scores,
                'summary': self._generate_summary(basic_stats, stability_analysis, evaluation_scores)
            }

        except Exception as e:
            logger.error(f"综合统计分析失败: {e}")
            return {'error': 'comprehensive_analysis_failed'}

    def batch_analysis(self, factor_data: pd.DataFrame,
                      ic_results_dict: Dict = None) -> Dict:
        """
        批量因子统计分析

        Args:
            factor_data: 因子数据DataFrame
            ic_results_dict: IC结果字典 {因子名: IC结果}

        Returns:
            批量分析结果
        """
        results = {}

        for factor_name in factor_data.columns:
            if factor_name in ['ts_code', 'trade_date']:
                continue

            factor_series = factor_data[factor_name]
            ic_result = ic_results_dict.get(factor_name) if ic_results_dict else None

            results[factor_name] = self.comprehensive_analysis(factor_series, ic_result)

        return {
            'individual_results': results,
            'summary_statistics': self._generate_batch_summary(results)
        }

    def _generate_summary(self, basic_stats: Dict, stability_analysis: Dict,
                         evaluation_scores: Dict) -> Dict:
        """生成单因子分析摘要"""
        summary = {
            'data_quality': 'good' if basic_stats.get('missing_ratio', 1) < 0.1 else 'poor',
            'stability': 'stable' if stability_analysis.get('stability_score', 0) > 0.7 else 'unstable',
            'overall_grade': evaluation_scores.get('grade', 'Unknown'),
            'key_metrics': {
                'missing_ratio': basic_stats.get('missing_ratio', 0),
                'stability_score': stability_analysis.get('stability_score', 0),
                'total_score': evaluation_scores.get('total_score', 0)
            }
        }
        return summary

    def _generate_batch_summary(self, results: Dict) -> Dict:
        """生成批量分析摘要"""
        total_factors = len(results)
        successful_analyses = sum(1 for r in results.values() if 'error' not in r)

        # 统计评级分布
        grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        stability_scores = []
        total_scores = []

        for result in results.values():
            if 'error' not in result and 'evaluation_scores' in result:
                eval_scores = result['evaluation_scores']
                grade = eval_scores.get('grade', 'F')
                if grade in grade_distribution:
                    grade_distribution[grade] += 1

                if 'total_score' in eval_scores:
                    total_scores.append(eval_scores['total_score'])

            if 'error' not in result and 'stability_analysis' in result:
                stability_score = result['stability_analysis'].get('stability_score', 0)
                stability_scores.append(stability_score)

        return {
            'analysis_overview': {
                'total_factors': total_factors,
                'successful_analyses': successful_analyses,
                'success_rate': successful_analyses / total_factors if total_factors > 0 else 0
            },
            'grade_distribution': grade_distribution,
            'score_statistics': {
                'mean_total_score': np.mean(total_scores) if total_scores else 0,
                'mean_stability_score': np.mean(stability_scores) if stability_scores else 0,
                'top_score': max(total_scores) if total_scores else 0
            },
            'quality_metrics': {
                'high_quality_factors': grade_distribution['A'] + grade_distribution['B'],
                'usable_factors': grade_distribution['A'] + grade_distribution['B'] + grade_distribution['C'],
                'poor_factors': grade_distribution['F']
            }
        }