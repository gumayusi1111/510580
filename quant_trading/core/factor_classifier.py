"""
因子分类器模块
根据因子类型自动分配适合的评估周期，解决单一前瞻期问题
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FactorCategory:
    """因子类别配置"""
    name: str
    patterns: List[str]
    forward_periods: List[int]
    primary_period: int
    description: str
    evaluation_focus: str  # 评估重点


class FactorClassifier:
    """
    因子分类器 - 智能识别因子类型并分配评估周期

    核心目标：
    - 技术因子使用短期前瞻期（1-5日）
    - 基本面因子使用中期前瞻期（10-30日）
    - 宏观因子考虑滞后性（5-20日）
    """

    def __init__(self):
        self.categories = self._define_factor_categories()
        logger.info(f"因子分类器初始化完成，支持{len(self.categories)}个类别")

    def _define_factor_categories(self) -> Dict[str, FactorCategory]:
        """定义因子分类规则"""
        return {
            'technical_short': FactorCategory(
                name='technical_short',
                patterns=[
                    # 短期移动均线类
                    r'^SMA_[1-9]$', r'^SMA_1[0-5]$',  # SMA_5, SMA_10等短期均线
                    r'^EMA_[1-9]$', r'^EMA_1[0-5]$',  # EMA_5, EMA_10等
                    r'^WMA_[1-9]$', r'^WMA_1[0-5]$',  # WMA_5, WMA_10等

                    # 短期动量指标
                    r'^RSI_[1-9]$', r'^RSI_1[0-4]$',  # RSI_6, RSI_14等
                    r'^ROC_[1-9]$', r'^ROC_1[0-5]$',  # ROC_5, ROC_10等
                    r'^MOM_[1-9]$', r'^MOM_1[0-5]$',  # MOM_5, MOM_10等
                    r'^KDJ', r'^STOCH',               # KDJ, 随机震荡器

                    # 短期量价指标
                    r'^VMA_[1-9]$', r'^VMA_1[0-5]$',  # 成交量均线
                    r'^VOLUME_RATIO_[1-9]$',          # 量比
                    r'^WR_1[0-4]$',                   # 威廉指标
                ],
                forward_periods=[1, 3, 5],
                primary_period=1,
                description='短期技术因子：适合日内到周级交易，信号衰减快',
                evaluation_focus='捕捉短期价格动量和反转信号'
            ),

            'technical_medium': FactorCategory(
                name='technical_medium',
                patterns=[
                    # 中期移动均线类
                    r'^SMA_[2-6][0-9]$',  # SMA_20, SMA_60等中长期均线
                    r'^EMA_[2-6][0-9]$',  # EMA_20, EMA_60等
                    r'^WMA_[2-6][0-9]$',  # WMA_20, WMA_60等
                    r'^MA_DIFF', r'^MA_SLOPE',  # 均线差值和斜率

                    # 中期趋势指标
                    r'^MACD',                    # MACD指标
                    r'^ATR', r'^ATR_PCT',        # 真实波幅
                    r'^HV_[2-6][0-9]$',          # 历史波动率

                    # 中期通道指标
                    r'^BOLL', r'^BB_WIDTH',      # 布林带
                    r'^DC',                      # 唐奇安通道
                    r'^CCI',                     # CCI指标

                    # 中期收益风险指标
                    r'^ANNUAL_VOL', r'^MAX_DD',  # 年化波动率，最大回撤
                ],
                forward_periods=[3, 5, 10],
                primary_period=5,
                description='中期技术因子：适合周到半月级交易，趋势性较强',
                evaluation_focus='识别中期趋势和波动率变化'
            ),

            'fundamental': FactorCategory(
                name='fundamental',
                patterns=[
                    # ETF净值因子
                    r'^NAV_', r'^NET_ASSET',           # 净值相关

                    # 估值因子
                    r'^PE_', r'^PB_',                  # 市盈率、市净率相关
                    r'PERCENTILE$', r'_MA_[2-9][0-9]$', # 分位数、移动平均

                    # 基本面变化
                    r'^TURNOVER_RATE',                 # 换手率
                    r'^INDEX_VALUATION',               # 指数估值
                ],
                forward_periods=[10, 20, 30],
                primary_period=20,
                description='基本面因子：适合月级别价值回归，中长期有效',
                evaluation_focus='捕捉估值修复和基本面驱动的中长期机会'
            ),

            'macro_flow': FactorCategory(
                name='macro_flow',
                patterns=[
                    # 宏观利率因子
                    r'^SHIBOR', r'^RATE',              # 利率相关

                    # 资金流因子
                    r'^SHARE_CHANGE', r'^FUND_FLOW',   # 份额变化、资金流
                    r'^ETF_SHARE', r'^FD_SHARE',       # ETF份额

                    # 市场情绪因子
                    r'^OBV',                           # 能量潮
                    r'^VOLUME_RATIO_[2-9][0-9]$',      # 长期量比
                ],
                forward_periods=[5, 10, 20],
                primary_period=10,
                description='宏观资金流因子：考虑滞后性和流动性传导，中期影响',
                evaluation_focus='把握宏观环境变化和资金流向对市场的影响'
            ),

            'risk_return': FactorCategory(
                name='risk_return',
                patterns=[
                    # 收益率因子
                    r'^DAILY_RETURN', r'^RETURN',      # 收益率
                    r'^CUM_RETURN',                    # 累计收益率

                    # 风险因子
                    r'^TR$', r'^VOLATILITY',           # 真实波幅、波动率
                    r'^STD', r'^VAR',                  # 标准差、方差
                ],
                forward_periods=[1, 5, 10],
                primary_period=5,
                description='收益风险因子：衡量风险调整后收益，多时间尺度有效',
                evaluation_focus='评估风险调整后的收益特征'
            )
        }

    def classify_factor(self, factor_name: str) -> FactorCategory:
        """
        智能识别因子类型

        Args:
            factor_name: 因子名称

        Returns:
            因子类别配置
        """
        if not factor_name:
            logger.warning("因子名称为空，使用默认分类")
            return self._get_default_category()

        # 标准化因子名称
        standardized_name = factor_name.upper().strip()

        # 逐类别匹配
        for category_name, category in self.categories.items():
            for pattern in category.patterns:
                if re.match(pattern, standardized_name):
                    logger.debug(f"因子 {factor_name} 分类为 {category_name}")
                    return category

        # 未匹配到的因子使用启发式规则
        heuristic_category = self._heuristic_classification(standardized_name)
        logger.info(f"因子 {factor_name} 使用启发式分类: {heuristic_category.name}")
        return heuristic_category

    def _heuristic_classification(self, factor_name: str) -> FactorCategory:
        """启发式分类规则 - 处理未明确定义的因子"""

        # 包含数字的一般是技术指标
        if re.search(r'_\d+$', factor_name):
            # 提取数字判断周期
            numbers = re.findall(r'\d+', factor_name)
            if numbers:
                period = int(numbers[-1])
                if period <= 15:
                    return self.categories['technical_short']
                else:
                    return self.categories['technical_medium']

        # 根据关键词分类
        if any(keyword in factor_name for keyword in ['PE', 'PB', 'NAV', 'VALUATION']):
            return self.categories['fundamental']
        elif any(keyword in factor_name for keyword in ['SHIBOR', 'RATE', 'SHARE', 'FLOW']):
            return self.categories['macro_flow']
        elif any(keyword in factor_name for keyword in ['RETURN', 'VOL', 'STD', 'RISK']):
            return self.categories['risk_return']
        else:
            # 默认为中期技术因子
            return self.categories['technical_medium']

    def _get_default_category(self) -> FactorCategory:
        """获取默认分类"""
        return self.categories['technical_medium']

    def get_adaptive_periods(self, factor_name: str) -> Tuple[List[int], int]:
        """
        获取因子的适应性前瞻期配置

        Args:
            factor_name: 因子名称

        Returns:
            (前瞻期列表, 主要前瞻期)
        """
        category = self.classify_factor(factor_name)
        return category.forward_periods, category.primary_period

    def batch_classify_factors(self, factor_names: List[str]) -> Dict[str, FactorCategory]:
        """
        批量分类因子

        Args:
            factor_names: 因子名称列表

        Returns:
            因子名称到类别的映射
        """
        results = {}
        category_counts = {}

        for factor_name in factor_names:
            category = self.classify_factor(factor_name)
            results[factor_name] = category

            # 统计分类数量
            category_counts[category.name] = category_counts.get(category.name, 0) + 1

        # 输出分类统计
        logger.info("因子分类统计:")
        for cat_name, count in category_counts.items():
            logger.info(f"  {cat_name}: {count}个因子")

        return results

    def get_category_summary(self) -> Dict[str, Dict]:
        """获取分类体系总览"""
        summary = {}
        for name, category in self.categories.items():
            summary[name] = {
                'description': category.description,
                'evaluation_focus': category.evaluation_focus,
                'forward_periods': category.forward_periods,
                'primary_period': category.primary_period,
                'pattern_count': len(category.patterns)
            }
        return summary

    def validate_factor_name(self, factor_name: str) -> Dict[str, any]:
        """
        验证因子名称并提供分类建议

        Args:
            factor_name: 因子名称

        Returns:
            验证结果和建议
        """
        category = self.classify_factor(factor_name)

        # 检查是否为精确匹配
        is_exact_match = False
        matched_pattern = None

        standardized_name = factor_name.upper().strip()
        for pattern in category.patterns:
            if re.match(pattern, standardized_name):
                is_exact_match = True
                matched_pattern = pattern
                break

        return {
            'factor_name': factor_name,
            'category': category.name,
            'description': category.description,
            'forward_periods': category.forward_periods,
            'primary_period': category.primary_period,
            'is_exact_match': is_exact_match,
            'matched_pattern': matched_pattern,
            'confidence': 'high' if is_exact_match else 'medium'
        }


def create_factor_classifier() -> FactorClassifier:
    """工厂函数：创建因子分类器实例"""
    return FactorClassifier()


# 全局实例（单例模式）
_global_classifier = None

def get_global_classifier() -> FactorClassifier:
    """获取全局因子分类器实例"""
    global _global_classifier
    if _global_classifier is None:
        _global_classifier = create_factor_classifier()
    return _global_classifier


if __name__ == "__main__":
    # 简单测试
    classifier = create_factor_classifier()

    # 测试因子分类
    test_factors = [
        'SMA_5', 'SMA_20', 'SMA_60',
        'RSI_14', 'MACD_SIGNAL',
        'PE_PERCENTILE', 'PB_MA_20',
        'SHIBOR_1M', 'SHARE_CHANGE_PCT',
        'DAILY_RETURN', 'ANNUAL_VOL_60'
    ]

    print("=== 因子分类测试 ===")
    for factor in test_factors:
        result = classifier.validate_factor_name(factor)
        print(f"{factor:20s} -> {result['category']:15s} 主期: {result['primary_period']:2d}日 [{result['confidence']}]")

    print("\n=== 分类体系总览 ===")
    summary = classifier.get_category_summary()
    for cat_name, info in summary.items():
        print(f"{cat_name:15s}: {info['description']}")
        print(f"{'':15s}  前瞻期: {info['forward_periods']}, 主期: {info['primary_period']}日")