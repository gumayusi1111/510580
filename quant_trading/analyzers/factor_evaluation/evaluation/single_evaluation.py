"""
单因子评估模块
负责单个因子的完整评估流程
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class SingleFactorEvaluation:
    """单因子评估处理类"""

    def __init__(self, evaluator):
        """
        Args:
            evaluator: FactorEvaluator实例
        """
        self.evaluator = evaluator

    def evaluate(self, factor_name: str, etf_code: str = "510580") -> Dict:
        """
        评估单个因子的有效性

        Args:
            factor_name: 因子名称
            etf_code: ETF代码

        Returns:
            因子评估结果
        """
        logger.info(f"开始评估因子: {factor_name}")

        try:
            # 加载数据
            factor_data = self.evaluator.data_manager.get_factor_data([factor_name], etf_code)
            returns = self.evaluator.data_manager.get_returns_data(etf_code)

            if factor_data.empty or returns.empty:
                logger.warning(f"因子 {factor_name} 数据为空，跳过评估")
                return {'error': 'no_data', 'factor_name': factor_name}

            # 确保获取的是Series而不是DataFrame，并处理数据类型问题
            if factor_name in factor_data.columns:
                factor_series = factor_data[factor_name].copy()

                # 数据类型验证和清理
                if factor_series.dtype == 'object':
                    # 尝试转换为数值型，过滤掉非数值数据
                    factor_series = pd.to_numeric(factor_series, errors='coerce')
                    logger.info(f"因子 {factor_name} 从object类型转换为数值型")

                # 移除无效值
                factor_series = factor_series.dropna()

                if factor_series.empty:
                    logger.warning(f"因子 {factor_name} 清理后数据为空")
                    return {'error': 'empty_factor_data', 'factor_name': factor_name}

                # 检查是否仍有非数值数据
                if not pd.api.types.is_numeric_dtype(factor_series):
                    logger.warning(f"因子 {factor_name} 包含非数值数据，跳过评估")
                    return {'error': 'non_numeric_data', 'factor_name': factor_name}

            else:
                logger.warning(f"因子 {factor_name} 不在数据中")
                return {'error': 'factor_not_found', 'factor_name': factor_name}

            # 执行各项分析（使用智能适应性IC分析）
            adaptive_ic_result = self.evaluator.ic_analyzer.analyze_factor_ic_adaptive(
                factor_series, returns
            )

            # 转换AdaptiveICResult为兼容格式
            ic_results = self._convert_adaptive_result(adaptive_ic_result)
            basic_stats = self.evaluator.statistics.calculate_basic_statistics(factor_series)
            distribution_stats = self.evaluator.statistics.analyze_distribution(factor_series)
            stability_stats = self.evaluator.statistics.analyze_factor_stability(
                factor_series, window=self.evaluator.window_config.stability_window
            )

            # 计算综合评分
            evaluation_score = self.evaluator.scoring.calculate_evaluation_score(
                ic_results, basic_stats, stability_stats
            )

            evaluation_result = {
                'factor_name': factor_name,
                'etf_code': etf_code,
                'basic_statistics': basic_stats,
                'distribution_analysis': distribution_stats,
                'stability_analysis': stability_stats,
                'ic_analysis': adaptive_ic_result,  # 保存原始适应性结果
                'ic_analysis_converted': ic_results,  # 兼容格式
                'evaluation_score': evaluation_score
            }

            logger.info(f"因子 {factor_name} 评估完成，评级: {evaluation_score.get('grade', 'N/A')}")
            return evaluation_result

        except Exception as e:
            logger.error(f"评估因子 {factor_name} 失败: {e}")
            return {'error': 'evaluation_failed', 'factor_name': factor_name, 'details': str(e)}

    def _convert_adaptive_result(self, adaptive_result) -> Dict:
        """
        将AdaptiveICResult转换为兼容评分系统的格式

        Args:
            adaptive_result: AdaptiveICResult对象

        Returns:
            Dict: 兼容格式的IC结果
        """
        try:
            # 检查是否是AdaptiveICResult对象
            if hasattr(adaptive_result, 'statistics') and hasattr(adaptive_result, 'primary_period'):
                # 使用主要前瞻期的统计数据
                primary_period_key = f'period_{adaptive_result.primary_period}'

                # 构建兼容格式
                converted_result = {
                    'factor_name': adaptive_result.factor_name,
                    'factor_category': adaptive_result.factor_category,
                    'adaptive_periods': adaptive_result.adaptive_periods,
                    'primary_period': adaptive_result.primary_period,
                    'statistics': {},
                    'ic_analysis': {}
                }

                # 转换统计数据
                if primary_period_key in adaptive_result.statistics:
                    primary_stats = adaptive_result.statistics[primary_period_key]
                    converted_result['statistics']['period_1'] = primary_stats  # 评分系统期望period_1

                    # 构建ic_analysis格式
                    converted_result['ic_analysis']['period_1'] = {
                        'ic_pearson': primary_stats.get('ic_mean', 0),
                        'ic_spearman': primary_stats.get('ic_mean', 0)  # 简化处理
                    }

                # 复制所有统计数据
                converted_result['statistics'].update(adaptive_result.statistics)

                return converted_result
            else:
                # 如果已经是字典格式，直接返回
                return adaptive_result

        except Exception as e:
            logger.error(f"转换适应性结果失败: {e}")
            # 返回空的兼容结构
            return {
                'factor_name': 'unknown',
                'statistics': {'period_1': {'ic_mean': 0, 'ic_ir': 0, 'ic_positive_ratio': 0.5}},
                'ic_analysis': {'period_1': {'ic_pearson': 0, 'ic_spearman': 0}}
            }