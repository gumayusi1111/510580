"""
批量因子评估模块
负责批量评估所有因子的完整流程
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class BatchFactorEvaluation:
    """批量因子评估处理类"""

    def __init__(self, evaluator):
        """
        Args:
            evaluator: FactorEvaluator实例
        """
        self.evaluator = evaluator

    def evaluate_all(self, etf_code: str = "510580") -> Dict:
        """
        评估所有因子的有效性

        Args:
            etf_code: ETF代码

        Returns:
            所有因子的评估结果
        """
        logger.info(f"开始评估所有因子，ETF代码: {etf_code}")

        try:
            # 加载数据
            all_factor_data = self.evaluator.data_manager.load_complete_factors(etf_code)
            returns = self.evaluator.data_manager.get_returns_data(etf_code)

            if all_factor_data.empty or returns.empty:
                logger.error("因子数据或收益率数据为空")
                return {'error': 'no_data'}

            # 单因子评估
            factor_evaluations = {}
            total_factors = len(all_factor_data.columns)

            for i, factor_name in enumerate(all_factor_data.columns, 1):
                print(
                    f"\r🔬 评估进度: {i:2d}/{total_factors} ({i/total_factors*100:5.1f}%) - {factor_name:<15}",
                    end="",
                    flush=True
                )
                logger.info(f"评估进度: {i}/{total_factors} - {factor_name}")

                # 调用单因子评估
                from .single_evaluation import SingleFactorEvaluation
                single_eval = SingleFactorEvaluation(self.evaluator)
                factor_eval = single_eval.evaluate(factor_name, etf_code)

                if 'error' not in factor_eval:
                    factor_evaluations[factor_name] = factor_eval
                    # 显示评级结果
                    grade = factor_eval.get('evaluation_score', {}).get('grade', 'N/A')
                    total_score = factor_eval.get('evaluation_score', {}).get('total_score', 0)
                    print(f" → 评级: {grade} (分数: {total_score:.3f})")
                else:
                    print(f" → ❌ 失败")

            print()  # 换行

            # 因子排序（提前生成用于相关性采样）
            print("🏆 生成因子排序...")
            from .ranking import FactorRanking
            ranking_module = FactorRanking(self.evaluator)
            factor_ranking = ranking_module.rank(factor_evaluations)

            # 相关性分析（采样优化）
            print("🔗 执行因子相关性分析...")
            logger.info("执行因子相关性分析")

            # 如果因子数量过多，只分析top因子的相关性
            if len(factor_evaluations) > 50:
                logger.info(f"因子数量({len(factor_evaluations)})较多，采样分析top 30因子的相关性")
                top_factors = (
                    factor_ranking.head(30)['factor'].tolist()
                    if not factor_ranking.empty
                    else list(all_factor_data.columns[:30])
                )
                sampled_factor_data = all_factor_data[top_factors]
                correlation_analysis = (
                    self.evaluator.correlation_analyzer.analyze_correlation_structure(
                        sampled_factor_data
                    )
                )
                logger.info(f"相关性分析完成（采样{len(top_factors)}个因子）")
            else:
                correlation_analysis = (
                    self.evaluator.correlation_analyzer.analyze_correlation_structure(
                        all_factor_data
                    )
                )
                logger.info("相关性分析完成（全量分析）")

            # IC批量分析（逐个使用适应性方法）
            print("📊 执行智能适应性IC分析...")
            logger.info("执行智能适应性IC分析")
            ic_analysis = {}
            for factor_name in all_factor_data.columns:
                try:
                    factor_series = all_factor_data[factor_name]
                    if not factor_series.dropna().empty:
                        ic_analysis[factor_name] = (
                            self.evaluator.ic_analyzer.analyze_factor_ic_adaptive(
                                factor_series, returns
                            )
                        )
                except Exception as e:
                    logger.warning(f"IC分析失败 {factor_name}: {e}")
                    continue

            # 因子筛选建议
            print("🎯 生成筛选建议...")
            from .selection import FactorSelection
            selection_module = FactorSelection(self.evaluator)
            factor_selection = selection_module.suggest(
                correlation_analysis, ic_analysis, factor_ranking
            )

            # 获取实际的日期范围（从trade_date列）
            if 'trade_date' in all_factor_data.columns:
                start_date = all_factor_data['trade_date'].min()
                end_date = all_factor_data['trade_date'].max()
            else:
                # 如果没有trade_date列，使用索引
                start_date = all_factor_data.index.min()
                end_date = all_factor_data.index.max()

            # 确保日期是字符串格式（如果是Timestamp则转换）
            if hasattr(start_date, 'strftime'):
                start_date = start_date.strftime('%Y-%m-%d')
            if hasattr(end_date, 'strftime'):
                end_date = end_date.strftime('%Y-%m-%d')

            result = {
                'etf_code': etf_code,
                'evaluation_summary': {
                    'total_factors': len(all_factor_data.columns),
                    'evaluated_factors': len(factor_evaluations),
                    'data_period': (start_date, end_date)
                },
                'individual_evaluations': factor_evaluations,
                'correlation_analysis': correlation_analysis,
                'ic_analysis': ic_analysis,
                'factor_ranking': factor_ranking,
                'selection_recommendations': factor_selection
            }

            logger.info(f"全部因子评估完成，成功评估 {len(factor_evaluations)} 个因子")
            return result

        except Exception as e:
            logger.error(f"批量因子评估失败: {e}")
            return {'error': 'batch_evaluation_failed', 'details': str(e)}