"""
因子筛选模块
负责提供因子筛选建议
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class FactorSelection:
    """因子筛选建议处理类"""

    def __init__(self, evaluator):
        """
        Args:
            evaluator: FactorEvaluator实例
        """
        self.evaluator = evaluator

    def suggest(
        self, correlation_analysis: Dict, ic_analysis: Dict, factor_ranking: pd.DataFrame
    ) -> Dict:
        """
        提供因子筛选建议

        Args:
            correlation_analysis: 相关性分析结果
            ic_analysis: IC分析结果
            factor_ranking: 因子排序结果

        Returns:
            筛选建议
        """
        suggestions = {
            'high_quality_factors': [],
            'redundant_factors': [],
            'low_performance_factors': [],
            'recommended_factors': []
        }

        try:
            # 高质量因子（A级和B级）
            if not factor_ranking.empty:
                high_quality = factor_ranking[factor_ranking['grade'].isin(['A', 'B'])]
                suggestions['high_quality_factors'] = high_quality['factor'].tolist()

                # 低表现因子（D级和F级）
                low_performance = factor_ranking[factor_ranking['grade'].isin(['D', 'F'])]
                suggestions['low_performance_factors'] = low_performance['factor'].tolist()

            # 冗余因子
            if (
                'redundant_groups' in correlation_analysis
                and 'pearson' in correlation_analysis['redundant_groups']
            ):

                redundant_groups = correlation_analysis['redundant_groups']['pearson']
                redundant_factors = set()

                for group in redundant_groups.values():
                    # 保留每组第一个因子，其余标记为冗余
                    group_list = sorted(list(group))
                    redundant_factors.update(group_list[1:])

                suggestions['redundant_factors'] = list(redundant_factors)

            # 推荐因子集合
            if not factor_ranking.empty:
                recommended = set(suggestions['high_quality_factors']) - set(
                    suggestions['redundant_factors']
                )

                # 如果推荐因子太少，补充一些B级和C级因子
                if len(recommended) < 10:
                    additional_factors = (
                        factor_ranking[
                            (~factor_ranking['factor'].isin(recommended))
                            & (
                                ~factor_ranking['factor'].isin(
                                    suggestions['redundant_factors']
                                )
                            )
                            & (factor_ranking['grade'].isin(['B', 'C']))
                        ]['factor']
                        .head(10 - len(recommended))
                        .tolist()
                    )

                    recommended.update(additional_factors)

                suggestions['recommended_factors'] = sorted(list(recommended))

            logger.info(f"因子筛选建议完成，推荐 {len(suggestions['recommended_factors'])} 个因子")
            return suggestions

        except Exception as e:
            logger.error(f"生成因子筛选建议失败: {e}")
            return suggestions