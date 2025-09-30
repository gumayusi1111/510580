"""
IC评分模块
负责计算IC相关的评分指标
"""

import logging
from typing import Dict
from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ICScorer:
    """
    IC评分器

    负责计算因子的IC相关评分，包括IC强度、IR和胜率评分

    Attributes:
        config: 评分配置实例
        thresholds: IC阈值配置
    """

    def __init__(self, config=None):
        """
        初始化IC评分器

        Args:
            config: 评分配置实例，默认使用DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG
        self.thresholds = self.config.ic_thresholds

    def calculate_ic_score(self, ic_results: Dict) -> float:
        """
        计算IC综合评分

        Args:
            ic_results: IC分析结果

        Returns:
            IC评分 (0-权重最大值)
        """
        ic_available = False

        if ic_results and 'statistics' in ic_results and 'period_1' in ic_results['statistics']:
            ic_stats = ic_results['statistics']['period_1']

            # 检查IC数据有效性
            ic_mean = ic_stats.get('ic_mean', 0)
            ic_abs_mean = ic_stats.get('ic_abs_mean', 0)

            if abs(ic_mean) > 1e-6 or ic_abs_mean > 1e-6:
                ic_available = True
                ic_ir = ic_stats.get('ic_ir', 0)
                ic_positive_ratio = ic_stats.get('ic_positive_ratio', 0.5)

                # 使用IC均值的绝对值评估方向一致性
                ic_strength_value = abs(ic_mean)

                # IC子分数计算
                ic_strength_score = self._calculate_strength_score(ic_strength_value)
                ic_ir_score = self._calculate_ir_score(ic_ir)
                ic_win_score = self._calculate_win_rate_score(ic_positive_ratio)

                # IC综合评分 (强度50%, IR30%, 胜率20%)
                ic_score = (ic_strength_score * 0.5 + ic_ir_score * 0.3 + ic_win_score * 0.2)

                logger.info(
                    f"IC评分: IC均值={ic_mean:.6f}, 强度={ic_strength_value:.6f}, "
                    f"强度分={ic_strength_score:.3f}, IR分={ic_ir_score:.3f}, 胜率分={ic_win_score:.3f}"
                )

                return ic_score * self.config.weights.ic

        # IC失败时的替代评分
        if not ic_available:
            logger.warning("IC计算失败，返回0分")
            return 0.0

    def _calculate_strength_score(self, ic_abs_mean: float) -> float:
        """
        计算IC强度评分

        Args:
            ic_abs_mean: IC绝对值均值

        Returns:
            强度评分 (0-1)
        """
        t = self.thresholds

        if ic_abs_mean >= t.excellent:  # ≥0.08
            return 1.0
        elif ic_abs_mean >= t.good:  # 0.05-0.08
            return 0.7 + (ic_abs_mean - t.good) / (t.excellent - t.good) * 0.3
        elif ic_abs_mean >= t.fair:  # 0.03-0.05
            return 0.4 + (ic_abs_mean - t.fair) / (t.good - t.fair) * 0.3
        elif ic_abs_mean >= t.acceptable:  # 0.02-0.03
            return 0.2 + (ic_abs_mean - t.acceptable) / (t.fair - t.acceptable) * 0.2
        elif ic_abs_mean >= t.weak:  # 0.01-0.02
            return 0.1 + (ic_abs_mean - t.weak) / (t.acceptable - t.weak) * 0.1
        else:  # <0.01
            return ic_abs_mean / t.weak * 0.1

    def _calculate_ir_score(self, ic_ir: float) -> float:
        """
        计算IC信息比率评分

        Args:
            ic_ir: IC信息比率

        Returns:
            IR评分 (0-1)
        """
        t = self.thresholds
        abs_ir = abs(ic_ir)

        if abs_ir >= t.ir_excellent:  # IR≥1.0
            return 1.0
        elif abs_ir >= t.ir_good:  # IR≥0.5
            return 0.5 + (abs_ir - t.ir_good) / (t.ir_excellent - t.ir_good) * 0.5
        else:  # IR<0.5
            return abs_ir / t.ir_good * 0.5

    def _calculate_win_rate_score(self, ic_positive_ratio: float) -> float:
        """
        计算IC胜率评分

        Args:
            ic_positive_ratio: IC正比例

        Returns:
            胜率评分 (0-1)
        """
        t = self.thresholds

        if ic_positive_ratio >= t.win_rate_good:  # ≥60%
            return 0.5 + (ic_positive_ratio - t.win_rate_good) / (1.0 - t.win_rate_good) * 0.5
        elif ic_positive_ratio <= t.win_rate_poor:  # ≤40% (反向有效)
            return 0.5 + (t.win_rate_poor - ic_positive_ratio) / t.win_rate_poor * 0.5
        else:  # 40-60% (方向性不明确)
            return (0.5 - abs(ic_positive_ratio - 0.5)) / 0.1 * 0.5