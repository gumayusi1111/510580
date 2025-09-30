"""
因子选择模块
基于相关性分析进行因子筛选
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class FactorSelector:
    """因子选择器"""

    @staticmethod
    def suggest_factor_selection(correlation_matrix: pd.DataFrame,
                               ic_results: Dict = None,
                               selection_method: str = "ic_based",
                               threshold: float = 0.8) -> List[str]:
        """
        基于相关性分析建议因子选择

        Args:
            correlation_matrix: 相关性矩阵
            ic_results: IC分析结果（可选）
            selection_method: 选择方法 ['ic_based', 'random', 'first']
            threshold: 相关性阈值

        Returns:
            建议保留的因子列表

        Algorithm:
            1. 识别冗余因子组
            2. 从每个组中选择最优因子
            3. 保留所有独立因子
        """
        from .core import RedundancyDetector

        if correlation_matrix.empty:
            logger.warning("相关性矩阵为空，无法进行因子选择")
            return []

        # 识别冗余因子组
        detector = RedundancyDetector()
        redundant_groups = detector.identify_redundant_groups(correlation_matrix, threshold)

        # 所有因子
        all_factors = set(correlation_matrix.columns)

        # 非冗余因子（不在任何冗余组中的因子）
        factors_in_groups = set()
        for group in redundant_groups.values():
            factors_in_groups.update(group)

        independent_factors = all_factors - factors_in_groups

        # 从每个冗余组中选择一个代表因子
        selected_factors = list(independent_factors)

        for group_name, group_factors in redundant_groups.items():
            if selection_method == "ic_based" and ic_results:
                best_factor = FactorSelector._select_best_factor_by_ic(group_factors, ic_results)
            elif selection_method == "random":
                best_factor = np.random.choice(list(group_factors))
            else:  # "first" 或其他方法
                best_factor = min(group_factors)  # 字母序第一个

            selected_factors.append(best_factor)
            logger.info(f"{group_name}: 从 {len(group_factors)} 个因子中选择 {best_factor}")

        logger.info(f"因子选择完成，从 {len(all_factors)} 个因子中选择 {len(selected_factors)} 个")
        return sorted(selected_factors)

    @staticmethod
    def _select_best_factor_by_ic(factors: Set[str], ic_results: Dict) -> str:
        """
        基于IC表现选择最佳因子

        Args:
            factors: 因子集合
            ic_results: IC分析结果

        Returns:
            最佳因子名称

        Selection Criteria:
            1. 优先考虑IC_IR（信息比率）
            2. 其次考虑IC绝对值
            3. 最后考虑IC胜率
        """
        best_factor = None
        best_score = -999.0

        for factor in factors:
            if factor not in ic_results:
                continue

            # 获取period_1的统计数据（最重要的1期前瞻）
            factor_stats = ic_results[factor].get('statistics', {}).get('period_1', {})

            if not factor_stats:
                continue

            # 计算综合评分
            ic_ir = factor_stats.get('ic_ir', 0)
            ic_abs_mean = factor_stats.get('ic_abs_mean', 0)
            ic_positive_ratio = factor_stats.get('ic_positive_ratio', 0.5)

            # 加权评分：IC_IR占70%，IC绝对值占20%，胜率占10%
            score = (abs(ic_ir) * 0.7 +
                    ic_abs_mean * 0.2 +
                    abs(ic_positive_ratio - 0.5) * 2 * 0.1)

            if score > best_score:
                best_score = score
                best_factor = factor

        # 如果没有找到有效的IC数据，返回字母序第一个
        return best_factor if best_factor else min(factors)

    @staticmethod
    def select_by_total_score(factors: Set[str], ranking_data: pd.DataFrame) -> str:
        """
        基于总分选择最佳因子 (v3新增)

        Args:
            factors: 因子集合
            ranking_data: 包含total_score的排名数据

        Returns:
            最佳因子名称
        """
        best_factor = None
        best_score = -999.0

        for factor in factors:
            if factor in ranking_data.index:
                score = ranking_data.loc[factor, 'total_score']
                if score > best_score:
                    best_score = score
                    best_factor = factor

        return best_factor if best_factor else min(factors)

    @staticmethod
    def validate_selection(selected_factors: List[str],
                         correlation_matrix: pd.DataFrame,
                         max_correlation: float = 0.8) -> Dict:
        """
        验证因子选择结果

        Args:
            selected_factors: 选择的因子列表
            correlation_matrix: 相关性矩阵
            max_correlation: 最大允许相关性

        Returns:
            验证结果字典
        """
        if not selected_factors or correlation_matrix.empty:
            return {'valid': False, 'reason': 'empty_input'}

        # 检查选择的因子是否都在相关性矩阵中
        missing_factors = [f for f in selected_factors if f not in correlation_matrix.columns]
        if missing_factors:
            return {
                'valid': False,
                'reason': 'missing_factors',
                'missing_factors': missing_factors
            }

        # 提取选择因子的相关性子矩阵
        selected_corr = correlation_matrix.loc[selected_factors, selected_factors]

        # 检查选择因子间的最大相关性
        upper_triangle = selected_corr.where(
            np.triu(np.ones_like(selected_corr, dtype=bool), k=1)
        ).stack()

        valid_correlations = upper_triangle.dropna()

        if valid_correlations.empty:
            max_corr_in_selection = 0.0
        else:
            max_corr_in_selection = valid_correlations.abs().max()

        # 计算验证指标
        validation_result = {
            'valid': max_corr_in_selection <= max_correlation,
            'max_correlation_in_selection': max_corr_in_selection,
            'threshold': max_correlation,
            'selected_count': len(selected_factors),
            'correlation_violations': []
        }

        # 如果有违反阈值的情况，记录具体的因子对
        if max_corr_in_selection > max_correlation:
            violations = valid_correlations[valid_correlations.abs() > max_correlation]
            validation_result['correlation_violations'] = [
                {'factor1': idx[0], 'factor2': idx[1], 'correlation': val}
                for idx, val in violations.items()
            ]

        return validation_result