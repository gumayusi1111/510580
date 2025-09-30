# 快速IC计算核心模块使用向量化操作大幅提升计算速度

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
import warnings

# 抑制运行时警告（numpy/pandas相关性计算中的除零警告）
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pandas")

logger = logging.getLogger(__name__)


class FastICCalculator:
    """快速IC计算器 - 使用向量化操作"""

    @staticmethod
    def calculate_single_ic(
        factor_data: pd.Series,
        returns: pd.Series,
        forward_periods: int = 1,
        method: str = "pearson",
        min_periods: int = 20,
    ) -> float:
        """
        快速计算单个IC值

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            forward_periods: 前瞻期数
            method: 相关性计算方法
            min_periods: 最小期数

        Returns:
            IC值
        """
        try:
            # 数据类型验证
            if not pd.api.types.is_numeric_dtype(factor_data):
                factor_data = pd.to_numeric(factor_data, errors="coerce")
                logger.warning("因子数据包含非数值，已尝试转换")

            if not pd.api.types.is_numeric_dtype(returns):
                returns = pd.to_numeric(returns, errors="coerce")
                logger.warning("收益率数据包含非数值，已尝试转换")

            # 数据对齐
            aligned_data = pd.concat(
                [factor_data, returns], axis=1, join="inner"
            ).dropna()

            if len(aligned_data) < min_periods + forward_periods:
                return np.nan

            # 计算前瞻收益
            factor_values = aligned_data.iloc[:-forward_periods, 0]
            future_returns = aligned_data.iloc[forward_periods:, 1]

            # 使用pandas的内置相关性计算（抑制警告）
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                ic_value = factor_values.corr(future_returns)

            return ic_value if not np.isnan(ic_value) else 0.0

        except Exception as e:
            logger.error(f"快速IC计算失败: {e}")
            return np.nan

    @staticmethod
    def calculate_rolling_ic_vectorized(
        factor_data: pd.Series,
        returns: pd.Series,
        window: int = 20,
        forward_periods: int = 1,
    ) -> pd.Series:
        """
        修复后的滚动IC计算 - 正确的数据对齐逻辑

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            window: 滚动窗口大小
            forward_periods: 前瞻期数

        Returns:
            滚动IC序列
        """
        try:
            # 数据对齐
            aligned_data = pd.concat(
                [factor_data, returns], axis=1, join="inner"
            ).dropna()

            if len(aligned_data) < window + forward_periods:
                logger.warning(
                    f"数据长度不足: {len(aligned_data)} < {window + forward_periods}"
                )
                return pd.Series(dtype=float, name=f"{factor_data.name}_IC")

            factor_values = aligned_data.iloc[:, 0]
            returns_values = aligned_data.iloc[:, 1]

            # 正确的滚动IC计算 - 逐窗口计算避免数据对齐错误
            rolling_ic_list = []
            rolling_ic_index = []

            for i in range(window - 1, len(factor_values) - forward_periods):
                # 取当前窗口的因子值
                window_factor = factor_values.iloc[i - window + 1 : i + 1]
                # 取对应的前瞻收益率（正确对齐）
                window_returns = returns_values.iloc[
                    i - window + 1 + forward_periods : i + 1 + forward_periods
                ]

                # 确保窗口大小正确
                if len(window_factor) == len(window_returns) == window:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', category=RuntimeWarning)
                        ic = window_factor.corr(window_returns)
                    if not np.isnan(ic):
                        rolling_ic_list.append(ic)
                        rolling_ic_index.append(factor_values.index[i])

            return pd.Series(
                rolling_ic_list, index=rolling_ic_index, name=f"{factor_data.name}_IC"
            )

        except Exception as e:
            logger.error(f"向量化IC计算失败: {e}")
            return pd.Series(dtype=float, name=f"{factor_data.name}_IC")

    @staticmethod
    def calculate_multi_window_ic_batch(
        factor_data: pd.Series,
        returns: pd.Series,
        windows: List[int],
        forward_periods: int = 1,
    ) -> Dict:
        """
        批量计算多窗口IC - 避免重复数据处理

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            windows: 窗口列表
            forward_periods: 前瞻期数

        Returns:
            多窗口IC结果字典
        """
        results = {}

        # 一次性数据对齐，避免重复处理
        aligned_data = pd.concat([factor_data, returns], axis=1, join="inner").dropna()

        if len(aligned_data) < max(windows) + forward_periods:
            logger.warning("数据长度不足，无法进行多窗口分析")
            return results

        factor_values = aligned_data.iloc[:, 0]
        future_returns = aligned_data.iloc[:, 1].shift(-forward_periods)

        # 批量计算所有窗口
        for window in windows:
            try:
                rolling_ic = factor_values.rolling(window=window).corr(future_returns)
                rolling_ic = rolling_ic.dropna()

                # 计算统计量
                if len(rolling_ic) > 0:
                    stats = {
                        "ic_mean": rolling_ic.mean(),
                        "ic_std": rolling_ic.std(),
                        "ic_ir": rolling_ic.mean() / rolling_ic.std()
                        if rolling_ic.std() > 0
                        else 0,
                        "ic_positive_ratio": (rolling_ic > 0).mean(),
                        "ic_abs_mean": rolling_ic.abs().mean(),
                    }
                else:
                    stats = {
                        "ic_mean": 0,
                        "ic_std": 0,
                        "ic_ir": 0,
                        "ic_positive_ratio": 0.5,
                        "ic_abs_mean": 0,
                    }

                results[f"window_{window}"] = {
                    "pearson": rolling_ic,
                    "statistics": stats,
                }

            except Exception as e:
                logger.error(f"计算{window}日窗口IC失败: {e}")
                continue

        return results


class FastICStatistics:
    """快速IC统计计算"""

    @staticmethod
    def calculate_ic_statistics_batch(ic_series: pd.Series) -> Dict:
        """
        批量计算IC统计量

        Args:
            ic_series: IC序列

        Returns:
            统计量字典
        """
        if len(ic_series) == 0:
            return {
                "ic_mean": 0,
                "ic_std": 0,
                "ic_ir": 0,
                "ic_positive_ratio": 0.5,
                "ic_abs_mean": 0,
                "ic_max": 0,
                "ic_min": 0,
            }

        # 向量化统计计算
        ic_clean = ic_series.dropna()

        ic_mean = ic_clean.mean()
        ic_std = ic_clean.std()

        return {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_mean / ic_std if ic_std > 0 else 0,
            "ic_positive_ratio": (ic_clean > 0).mean(),
            "ic_abs_mean": ic_clean.abs().mean(),
            "ic_max": ic_clean.max(),
            "ic_min": ic_clean.min(),
        }
