# IC分析核心计算模块包含IC值和滚动IC的核心计算逻辑


import pandas as pd
import numpy as np
from scipy import stats
import logging
import warnings

# 抑制运行时警告（numpy相关性计算中的除零警告）
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")

logger = logging.getLogger(__name__)


class ICCalculator:
    """IC值计算器"""

    @staticmethod
    def calculate_single_ic(
        factor_data: pd.Series,
        returns: pd.Series,
        forward_periods: int = 1,
        method: str = "pearson",
        min_periods: int = 20,
    ) -> float:
        """
        计算单个因子的IC值

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            forward_periods: 前瞻期数，默认1期
            method: 相关性计算方法 ['pearson', 'spearman']
            min_periods: 计算IC值的最小期数

        Returns:
            IC值

        Raises:
            ValueError: 当数据长度不足或方法不支持时
        """
        # 数据对齐和清洗
        aligned_data = pd.concat([factor_data, returns], axis=1, join="inner").dropna()

        if len(aligned_data) < min_periods + forward_periods:
            logger.warning(
                f"数据长度不足: {len(aligned_data)} < {min_periods + forward_periods}"
            )
            return np.nan

        # 因子值和前瞻收益对齐
        factor_values = aligned_data.iloc[:-forward_periods, 0]
        future_returns = aligned_data.iloc[forward_periods:, 1]

        # 重建索引确保对齐
        factor_values.index = future_returns.index

        # ★ 新增: Z-score标准化因子值，避免量纲影响
        # 百分制因子(RSI 0-100)和大范围因子会导致IC虚高
        factor_std = factor_values.std()
        if factor_std > 1e-8:  # 避免除零
            factor_values = (factor_values - factor_values.mean()) / factor_std
        else:
            logger.warning(f"因子标准差接近0 ({factor_std:.2e})，跳过标准化")

        try:
            if method == "pearson":
                ic_value, _ = stats.pearsonr(factor_values, future_returns)
            elif method == "spearman":
                ic_value, _ = stats.spearmanr(factor_values, future_returns)
            else:
                raise ValueError(f"不支持的相关性方法: {method}")

            return ic_value if not np.isnan(ic_value) else 0.0

        except Exception as e:
            logger.error(f"计算IC值失败: {e}")
            return np.nan

    @staticmethod
    def calculate_rolling_ic(
        factor_data: pd.Series,
        returns: pd.Series,
        window: int = 60,
        forward_periods: int = 1,
        method: str = "pearson",
    ) -> pd.Series:
        """
        计算滚动IC值序列

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            window: 滚动窗口大小（交易日）
            forward_periods: 前瞻期数
            method: 相关性计算方法

        Returns:
            滚动IC序列

        Note:
            使用60日滚动窗口是金融行业标准做法
        """
        # 数据对齐
        aligned_data = pd.concat([factor_data, returns], axis=1, join="inner").dropna()

        if len(aligned_data) < window + forward_periods:
            logger.warning("数据长度不足，无法计算滚动IC")
            return pd.Series(dtype=float, name=f"{factor_data.name}_IC")

        ic_values = []
        dates = []

        # 滚动计算IC
        for i in range(window, len(aligned_data) - forward_periods + 1):
            window_factor = aligned_data.iloc[i - window : i, 0]
            window_returns = aligned_data.iloc[
                i - window + forward_periods : i + forward_periods, 1
            ]

            # 确保索引对齐
            window_factor.index = window_returns.index

            # ★ 新增: Z-score标准化窗口内因子值
            factor_std = window_factor.std()
            if factor_std > 1e-8:
                window_factor = (window_factor - window_factor.mean()) / factor_std

            try:
                if method == "pearson":
                    ic_val, _ = stats.pearsonr(window_factor, window_returns)
                elif method == "spearman":
                    ic_val, _ = stats.spearmanr(window_factor, window_returns)
                else:
                    ic_val = np.nan

                ic_values.append(ic_val if not np.isnan(ic_val) else 0.0)
                dates.append(aligned_data.index[i])

            except Exception:
                ic_values.append(0.0)
                dates.append(aligned_data.index[i])

        return pd.Series(ic_values, index=dates, name=f"{factor_data.name}_IC")


class ICStatistics:
    """IC统计分析器"""

    @staticmethod
    def calculate_ic_statistics(ic_series: pd.Series) -> dict:
        """
        计算IC序列的统计指标

        Args:
            ic_series: IC值序列

        Returns:
            IC统计指标字典
        """
        if ic_series.empty:
            return {}

        clean_ic = ic_series.dropna()
        if clean_ic.empty:
            return {}

        # 核心统计指标
        ic_mean = clean_ic.mean()
        ic_std = clean_ic.std()

        # IC信息比率 (最重要的指标)
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0.0

        # IC胜率
        ic_positive_ratio = (clean_ic > 0).mean()

        # IC绝对值均值
        ic_abs_mean = clean_ic.abs().mean()

        return {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_ir,  # 信息比率：衡量IC的风险调整收益
            "ic_positive_ratio": ic_positive_ratio,  # 胜率
            "ic_abs_mean": ic_abs_mean,  # 预测强度
            "sample_size": len(clean_ic),
        }
