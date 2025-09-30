"""
相关性分析核心计算模块
包含相关性矩阵计算和冗余检测的核心算法
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class CorrelationCalculator:
    """相关性计算器"""

    @staticmethod
    def calculate_correlation_matrix(factor_data: pd.DataFrame,
                                   method: str = "pearson") -> pd.DataFrame:
        """
        计算因子相关性矩阵

        Args:
            factor_data: 因子数据DataFrame
            method: 相关性计算方法 ['pearson', 'spearman', 'kendall']

        Returns:
            相关性矩阵

        Raises:
            ValueError: 当计算方法不支持时
        """
        if method not in ['pearson', 'spearman', 'kendall']:
            raise ValueError(f"不支持的相关性方法: {method}")

        try:
            # 数据清洗
            clean_data = factor_data.dropna()

            if clean_data.empty:
                logger.warning("清理后的数据为空，无法计算相关性矩阵")
                return pd.DataFrame()

            # 检查数据质量
            if len(clean_data) < 30:  # 至少30个观测值
                logger.warning(f"数据量过少({len(clean_data)}行)，相关性计算可能不可靠")

            # 计算相关性矩阵（抑制RuntimeWarning）
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                corr_matrix = clean_data.corr(method=method)

            # 验证结果
            if corr_matrix.isnull().any().any():
                logger.warning("相关性矩阵包含NaN值")

            logger.info(f"成功计算相关性矩阵，形状: {corr_matrix.shape}, 方法: {method}")
            return corr_matrix

        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def find_high_correlation_pairs(correlation_matrix: pd.DataFrame,
                                  threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """
        找出高相关性因子对

        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值（建议0.7-0.9）

        Returns:
            高相关性因子对列表 [(factor1, factor2, correlation)]

        Note:
            行业标准：通常使用0.8作为高相关性阈值
        """
        if correlation_matrix.empty:
            return []

        high_corr_pairs = []

        # 遍历相关性矩阵的上三角（避免重复和自相关）
        n_factors = len(correlation_matrix.columns)

        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                factor1 = correlation_matrix.columns[i]
                factor2 = correlation_matrix.columns[j]
                corr_value = correlation_matrix.iloc[i, j]

                # 检查是否为有效数值
                if pd.isna(corr_value):
                    continue

                if abs(corr_value) >= threshold:
                    high_corr_pairs.append((factor1, factor2, corr_value))

        # 按相关性绝对值降序排序
        high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

        logger.info(f"找到 {len(high_corr_pairs)} 对高相关性因子 (阈值: {threshold})")
        return high_corr_pairs


class RedundancyDetector:
    """冗余检测器"""

    @staticmethod
    def identify_redundant_groups(correlation_matrix: pd.DataFrame,
                                threshold: float = 0.8) -> Dict[str, Set[str]]:
        """
        识别冗余因子组

        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值

        Returns:
            冗余因子组字典 {group_id: {factor_set}}

        Algorithm:
            使用图论中的连通分量算法，将高相关性因子聚类
        """
        if correlation_matrix.empty:
            return {}

        factor_connections = RedundancyDetector._build_factor_graph(
            correlation_matrix, threshold
        )

        redundant_groups = RedundancyDetector._find_connected_components(
            factor_connections
        )

        logger.info(f"识别出 {len(redundant_groups)} 个冗余因子组")
        return redundant_groups

    @staticmethod
    def _build_factor_graph(correlation_matrix: pd.DataFrame,
                          threshold: float) -> Dict[str, Set[str]]:
        """构建因子连接图"""
        calc = CorrelationCalculator()
        high_corr_pairs = calc.find_high_correlation_pairs(correlation_matrix, threshold)

        factor_connections = {}
        for factor1, factor2, _ in high_corr_pairs:
            factor_connections.setdefault(factor1, set()).add(factor2)
            factor_connections.setdefault(factor2, set()).add(factor1)

        return factor_connections

    @staticmethod
    def _find_connected_components(factor_connections: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """使用DFS找出所有连通分量"""
        visited = set()
        redundant_groups = {}
        group_id = 0

        for factor in factor_connections:
            if factor in visited:
                continue

            current_group = RedundancyDetector._dfs_component(
                factor, factor_connections, visited
            )

            if len(current_group) > 1:
                redundant_groups[f'group_{group_id}'] = current_group
                group_id += 1

        return redundant_groups

    @staticmethod
    def _dfs_component(start_factor: str, connections: Dict[str, Set[str]],
                      visited: Set[str]) -> Set[str]:
        """深度优先搜索单个连通分量"""
        component = set()
        stack = [start_factor]

        while stack:
            factor = stack.pop()
            if factor in visited:
                continue

            visited.add(factor)
            component.add(factor)

            if factor in connections:
                stack.extend(conn for conn in connections[factor] if conn not in visited)

        return component

    @staticmethod
    def calculate_correlation_summary(correlation_matrix: pd.DataFrame) -> Dict:
        """
        计算相关性汇总统计

        Args:
            correlation_matrix: 相关性矩阵

        Returns:
            汇总统计字典

        Note:
            提供相关性分布的关键统计指标
        """
        if correlation_matrix.empty:
            return {}

        # 获取上三角矩阵的值（排除对角线）
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
        ).stack()

        # 过滤NaN值
        valid_correlations = upper_triangle.dropna()

        if valid_correlations.empty:
            return {}

        summary = {
            'total_pairs': len(valid_correlations),
            'mean_correlation': valid_correlations.mean(),
            'std_correlation': valid_correlations.std(),
            'max_correlation': valid_correlations.max(),
            'min_correlation': valid_correlations.min(),
            'abs_mean_correlation': valid_correlations.abs().mean(),
            'median_correlation': valid_correlations.median(),
            'q75_correlation': valid_correlations.quantile(0.75),
            'q25_correlation': valid_correlations.quantile(0.25)
        }

        # 计算不同阈值下的高相关性比例
        for threshold in [0.3, 0.5, 0.7, 0.8, 0.9]:
            key = f'high_corr_ratio_{int(threshold*100)}'
            summary[key] = (valid_correlations.abs() >= threshold).mean()

        return summary