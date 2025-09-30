"""
因子排序模块
负责对评估后的因子进行排序
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class FactorRanking:
    """因子排序处理类"""

    def __init__(self, evaluator):
        """
        Args:
            evaluator: FactorEvaluator实例
        """
        self.evaluator = evaluator

    def rank(self, factor_evaluations: Dict) -> pd.DataFrame:
        """
        对所有因子进行排序

        Args:
            factor_evaluations: 因子评估结果

        Returns:
            因子排序DataFrame
        """
        ranking_data = []

        for factor_name, evaluation in factor_evaluations.items():
            if 'evaluation_score' not in evaluation:
                continue

            score_data = evaluation['evaluation_score']
            basic_stats = evaluation.get('basic_statistics', {})

            ranking_data.append({
                'factor': factor_name,
                'total_score': score_data.get('total_score', 0),
                'grade': score_data.get('grade', 'F'),
                'ic_score': score_data.get('ic_score', 0),
                'stability_score': score_data.get('stability_score', 0),
                'data_quality_score': score_data.get('data_quality_score', 0),
                'distribution_score': score_data.get('distribution_score', 0),
                'consistency_score': score_data.get('consistency_score', 0),
                'missing_ratio': basic_stats.get('missing_ratio', 1)
            })

        if not ranking_data:
            logger.warning("没有可用的评估结果进行排序")
            return pd.DataFrame()

        df = pd.DataFrame(ranking_data)
        df = df.sort_values('total_score', ascending=False).reset_index(drop=True)
        df['rank'] = range(1, len(df) + 1)

        return df