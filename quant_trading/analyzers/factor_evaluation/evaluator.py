"""
因子有效性评估器 - 智能适应性版本
集成适应性IC分析和智能因子分类，综合评估因子的预测能力和实用性

✨ Phase 1-2 集成特性：
- 智能因子分类和适应性前瞻期
- 基于因子类型的精准IC评估
- 改进效果量化分析

📦 模块化架构：
- evaluation/single_evaluation: 单因子评估逻辑
- evaluation/batch_evaluation: 批量因子评估编排
- evaluation/ranking: 因子排序算法
- evaluation/selection: 因子筛选建议
"""

import logging
import sys
from pathlib import Path
from typing import Dict

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from analyzers.correlation.analyzer import CorrelationAnalyzer  # noqa: E402
from analyzers.ic.analyzer import ICAnalyzer  # noqa: E402
from config.window_config import get_window_config  # noqa: E402
from core.data_management import DataManager  # noqa: E402
from utils.statistics import FactorScoring, FactorStatistics  # noqa: E402

from .evaluation import (  # noqa: E402
    BatchFactorEvaluation,
    FactorRanking,
    FactorSelection,
    SingleFactorEvaluation,
)

logger = logging.getLogger(__name__)


class FactorEvaluator:
    """因子有效性评估器 - 专注于高级评估逻辑"""

    def __init__(self, data_manager: DataManager = None, strategy_type: str = 'short_term'):
        """
        初始化因子评估器

        Args:
            data_manager: 数据管理器实例
            strategy_type: 策略类型，决定窗口配置
                - 'short_term': 短线策略（推荐用于ETF择时）
                - 'ultra_short': 超短线策略
                - 'medium_short': 中短线策略
                - 'medium_term': 传统中线策略
                - 'multi_timeframe': 多时间框架
        """
        self.data_manager = data_manager or DataManager()
        self.strategy_type = strategy_type

        # 加载窗口配置
        self.window_config = get_window_config(strategy_type)

        # 使用配置初始化分析器 - 启用适应性IC分析
        self.ic_analyzer = ICAnalyzer(strategy_type=strategy_type, enable_adaptive=True)
        self.correlation_analyzer = CorrelationAnalyzer()
        self.statistics = FactorStatistics()
        self.scoring = FactorScoring()

        # 初始化子模块
        self._single_eval = SingleFactorEvaluation(self)
        self._batch_eval = BatchFactorEvaluation(self)
        self._ranking = FactorRanking(self)
        self._selection = FactorSelection(self)

        logger.info(f"🚀 智能因子评估器初始化: {strategy_type}")
        logger.info("📊 集成模块: 适应性IC分析 + 智能因子分类")
        logger.info(f"⚙️ 窗口配置: {self.window_config.description}")

    def evaluate_single_factor(self, factor_name: str, etf_code: str = "510580") -> Dict:
        """
        评估单个因子的有效性（委托给SingleFactorEvaluation）

        Args:
            factor_name: 因子名称
            etf_code: ETF代码

        Returns:
            因子评估结果
        """
        return self._single_eval.evaluate(factor_name, etf_code)

    def evaluate_all_factors(self, etf_code: str = "510580") -> Dict:
        """
        评估所有因子的有效性（委托给BatchFactorEvaluation）

        Args:
            etf_code: ETF代码

        Returns:
            所有因子的评估结果
        """
        return self._batch_eval.evaluate_all(etf_code)