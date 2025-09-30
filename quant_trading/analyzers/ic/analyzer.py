"""
IC分析器 - 统一完善版本（重构版）
集成智能因子分类和适应性前瞻期的完整IC分析系统

✨ 核心特性：
- 智能因子分类和适应性前瞻期分配
- 基于因子类型的精准IC评估
- 新旧方法对比分析
- 改进效果量化评估
- 向量化高性能计算

📦 重构说明:
原508行代码已拆分为5个模块(analysis/子目录):
- result.py: 数据结构定义
- traditional.py: 传统IC分析
- adaptive.py: 适应性IC分析
- batch.py: 批量分析和排序
- 本文件: 主分析器类(向后兼容)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.window_config import get_window_config  # noqa: E402
from core.factor_classifier import FactorClassifier, get_global_classifier  # noqa: E402

from .analysis import (  # noqa: E402
    AdaptiveICAnalysis,
    AdaptiveICResult,
    BatchICAnalysis,
    TraditionalICAnalysis,
)
from .core import ICCalculator, ICStatistics  # noqa: E402
from .fast_core import FastICCalculator, FastICStatistics  # noqa: E402

logger = logging.getLogger(__name__)


class ICAnalyzer:
    """统一IC分析器 - 集成智能分类和适应性分析（重构版）"""

    def __init__(self,
                 min_periods: int = 20,
                 strategy_type: str = 'short_term',
                 fast_mode: bool = True,
                 factor_classifier: Optional[FactorClassifier] = None,
                 enable_adaptive: bool = True,
                 enable_comparison: bool = True):
        """
        初始化IC分析器

        Args:
            min_periods: 计算IC值的最小期数（金融标准：至少20个交易日）
            strategy_type: 策略类型，决定窗口配置
            fast_mode: 是否使用快速模式（向量化计算）
            factor_classifier: 因子分类器，None则使用全局分类器
            enable_adaptive: 是否启用适应性分析
            enable_comparison: 是否启用新旧方法对比
        """
        self.min_periods = min_periods
        self.fast_mode = fast_mode
        self.enable_adaptive = enable_adaptive
        self.enable_comparison = enable_comparison

        # 初始化计算器
        if fast_mode:
            self.calculator = FastICCalculator()
            self.statistics = FastICStatistics()
            logger.info("使用快速IC计算器（向量化）")
        else:
            self.calculator = ICCalculator()
            self.statistics = ICStatistics()

        # 加载策略配置
        self.window_config = get_window_config(strategy_type)
        self.strategy_type = strategy_type

        # 初始化因子分类器（仅在启用适应性分析时）
        if enable_adaptive:
            self.classifier = factor_classifier or get_global_classifier()
            logger.info("启用智能因子分类和适应性分析")
        else:
            self.classifier = None

        # 初始化子模块
        self._traditional = TraditionalICAnalysis(self)
        self._adaptive = AdaptiveICAnalysis(self)
        self._batch = BatchICAnalysis(self)

        logger.info(f"IC分析器初始化: {strategy_type} - {self.window_config.description}")
        logger.info(f"IC窗口配置: {self.window_config.ic_windows}")
        logger.info(f"主窗口: {self.window_config.primary_window}日")

    def calculate_ic(self, factor_data: pd.Series, returns: pd.Series,
                     forward_periods: int = 1, method: str = "pearson") -> float:
        """
        计算单个因子的IC值

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            forward_periods: 前瞻期数，默认1期
            method: 相关性计算方法 ['pearson', 'spearman']

        Returns:
            IC值
        """
        return self.calculator.calculate_single_ic(
            factor_data, returns, forward_periods, method, self.min_periods
        )

    def calculate_rolling_ic(self, factor_data: pd.Series, returns: pd.Series,
                           window: Optional[int] = None, forward_periods: int = 1,
                           method: str = "pearson") -> pd.Series:
        """
        计算滚动IC值

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            window: 滚动窗口大小，None则使用策略配置的主窗口
            forward_periods: 前瞻期数
            method: 相关性计算方法

        Returns:
            滚动IC序列
        """
        if window is None:
            window = self.window_config.primary_window

        if self.fast_mode:
            return self.calculator.calculate_rolling_ic_vectorized(
                factor_data, returns, window, forward_periods
            )
        else:
            return self.calculator.calculate_rolling_ic(
                factor_data, returns, window, forward_periods, method
            )

    def analyze_factor_ic(self, factor_data: pd.Series, returns: pd.Series,
                         forward_periods: List[int] = None) -> Dict:
        """
        传统IC分析方法（兼容性保留）

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列
            forward_periods: 前瞻期数列表

        Returns:
            IC分析结果字典
        """
        return self._traditional.analyze(factor_data, returns, forward_periods)

    def analyze_factor_ic_adaptive(self, factor_data: pd.Series, returns: pd.Series) -> AdaptiveICResult:
        """
        智能适应性IC分析（推荐方法）

        Args:
            factor_data: 因子数据序列
            returns: 收益率数据序列

        Returns:
            适应性IC分析结果
        """
        return self._adaptive.analyze(factor_data, returns)

    def analyze_all_factors(self, factor_data: pd.DataFrame, returns: pd.Series,
                          forward_periods: List[int] = None) -> Dict:
        """
        批量分析所有因子的IC表现

        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率数据序列
            forward_periods: 前瞻期数列表（传统模式使用）

        Returns:
            所有因子的IC分析结果
        """
        return self._batch.analyze_all(factor_data, returns, forward_periods)

    def rank_factors_by_ic(self, analysis_results: Dict, period: int = 1,
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
        return self._batch.rank_by_ic(analysis_results, period, metric)


def create_ic_analyzer(strategy_type: str = 'short_term',
                      fast_mode: bool = True,
                      enable_adaptive: bool = True,
                      enable_comparison: bool = True) -> ICAnalyzer:
    """
    工厂函数：创建IC分析器

    Args:
        strategy_type: 策略类型
        fast_mode: 是否使用快速模式
        enable_adaptive: 是否启用适应性分析
        enable_comparison: 是否启用对比分析

    Returns:
        IC分析器实例
    """
    return ICAnalyzer(
        strategy_type=strategy_type,
        fast_mode=fast_mode,
        enable_adaptive=enable_adaptive,
        enable_comparison=enable_comparison
    )


# 兼容性别名
AdaptiveICAnalyzer = ICAnalyzer


if __name__ == "__main__":
    # 简单测试
    analyzer = create_ic_analyzer()

    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')

    # 模拟短期因子数据（1-3日有效）
    short_factor = pd.Series(np.random.randn(100), index=dates, name='RSI_14')  # noqa: NPY002

    # 模拟收益率数据
    returns = pd.Series(np.random.randn(100) * 0.02, index=dates, name='returns')  # noqa: NPY002

    # 测试适应性分析
    result = analyzer.analyze_factor_ic_adaptive(short_factor, returns)

    print("🧪 IC分析器测试完成")
    print(f"因子: {result.factor_name}")
    print(f"分类: {result.factor_category}")
    print(f"适应性前瞻期: {result.adaptive_periods}")
    print(f"主前瞻期: {result.primary_period}")