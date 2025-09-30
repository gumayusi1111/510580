"""
因子样本外验证框架
实现训练集/测试集划分、滚动窗口验证等关键功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# 导入IC计算模块
from ..analyzers.ic.core import ICCalculator, ICStatistics

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    factor_name: str
    validation_type: str

    # 样本内外IC结果
    in_sample_ic: Dict
    out_sample_ic: Dict

    # 性能衰减分析
    degradation_metrics: Dict

    # 健壮性判断
    is_robust: bool
    robustness_score: float

    # 详细统计
    detailed_stats: Dict

    # 时间戳
    validation_timestamp: datetime


class FactorCrossValidator:
    """
    因子样本外验证器

    核心功能：
    1. 训练集/测试集划分验证
    2. 滚动窗口验证
    3. IC衰减分析
    4. 健壮性评分
    """

    def __init__(self, min_train_periods: int = 252,
                 test_ratio: float = 0.3,
                 min_ic_samples: int = 20):
        """
        初始化验证器

        Args:
            min_train_periods: 最小训练期数（默认1年）
            test_ratio: 测试集比例（默认30%）
            min_ic_samples: IC计算最小样本数
        """
        self.min_train_periods = min_train_periods
        self.test_ratio = test_ratio
        self.min_ic_samples = min_ic_samples

        self.ic_calculator = ICCalculator()
        self.ic_statistics = ICStatistics()

        logger.info(f"验证器初始化: 训练期{min_train_periods}日, 测试比例{test_ratio}, 最小IC样本{min_ic_samples}")

    def train_test_split(self, data: pd.DataFrame,
                        test_ratio: Optional[float] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        时间序列友好的训练测试集划分

        Args:
            data: 输入数据（按时间排序）
            test_ratio: 测试集比例，默认使用初始化值

        Returns:
            (训练集, 测试集)
        """
        if test_ratio is None:
            test_ratio = self.test_ratio

        total_length = len(data)
        split_point = int(total_length * (1 - test_ratio))

        # 确保训练集有足够长度
        if split_point < self.min_train_periods:
            raise ValueError(f"训练集长度{split_point}小于最小要求{self.min_train_periods}")

        train_data = data.iloc[:split_point]
        test_data = data.iloc[split_point:]

        logger.info(f"数据划分: 训练集{len(train_data)}期, 测试集{len(test_data)}期")
        return train_data, test_data

    def validate_factor_simple(self, factor_data: pd.Series, returns: pd.Series,
                              forward_periods: List[int] = None) -> ValidationResult:
        """
        简单样本外验证

        Args:
            factor_data: 因子数据
            returns: 收益率数据
            forward_periods: 前瞻期列表

        Returns:
            验证结果
        """
        if forward_periods is None:
            forward_periods = [1, 5, 10]

        factor_name = getattr(factor_data, 'name', 'unknown_factor')

        # 数据对齐
        aligned_data = pd.concat([factor_data, returns], axis=1, join='inner').dropna()

        if len(aligned_data) < self.min_train_periods + 50:  # 至少需要测试集有50个样本
            raise ValueError(f"数据长度{len(aligned_data)}不足，无法进行验证")

        # 划分数据
        train_data, test_data = self.train_test_split(aligned_data)

        # 计算样本内外IC
        in_sample_ic = self._calculate_ic_multiple_periods(
            train_data.iloc[:, 0], train_data.iloc[:, 1], forward_periods
        )

        out_sample_ic = self._calculate_ic_multiple_periods(
            test_data.iloc[:, 0], test_data.iloc[:, 1], forward_periods
        )

        # 计算衰减指标
        degradation_metrics = self._calculate_degradation_metrics(in_sample_ic, out_sample_ic)

        # 健壮性评分
        robustness_score = self._calculate_robustness_score(degradation_metrics)
        is_robust = robustness_score > 0.7  # 70%阈值

        # 详细统计
        detailed_stats = self._compile_detailed_stats(
            train_data, test_data, in_sample_ic, out_sample_ic
        )

        return ValidationResult(
            factor_name=factor_name,
            validation_type='simple_split',
            in_sample_ic=in_sample_ic,
            out_sample_ic=out_sample_ic,
            degradation_metrics=degradation_metrics,
            is_robust=is_robust,
            robustness_score=robustness_score,
            detailed_stats=detailed_stats,
            validation_timestamp=datetime.now()
        )

    def walk_forward_validation(self, factor_data: pd.Series, returns: pd.Series,
                               window_size: int = 252, step_size: int = 21,
                               forward_periods: List[int] = None) -> ValidationResult:
        """
        滚动窗口验证 - 模拟真实预测场景

        Args:
            factor_data: 因子数据
            returns: 收益率数据
            window_size: 训练窗口大小（默认1年）
            step_size: 滚动步长（默认1月）
            forward_periods: 前瞻期列表

        Returns:
            验证结果
        """
        if forward_periods is None:
            forward_periods = [1, 5, 10]

        factor_name = getattr(factor_data, 'name', 'unknown_factor')

        # 数据对齐
        aligned_data = pd.concat([factor_data, returns], axis=1, join='inner').dropna()

        if len(aligned_data) < window_size + step_size + max(forward_periods):
            raise ValueError("数据长度不足以进行滚动窗口验证")

        # 滚动验证结果存储
        rolling_results = []
        validation_dates = []

        # 开始滚动验证
        start_idx = window_size
        while start_idx + step_size + max(forward_periods) <= len(aligned_data):
            # 当前训练窗口
            train_window = aligned_data.iloc[start_idx-window_size:start_idx]

            # 当前测试窗口
            test_window = aligned_data.iloc[start_idx:start_idx+step_size]

            # 计算训练期IC
            train_ic = self._calculate_ic_multiple_periods(
                train_window.iloc[:, 0], train_window.iloc[:, 1], forward_periods
            )

            # 计算测试期IC
            test_ic = self._calculate_ic_multiple_periods(
                test_window.iloc[:, 0], test_window.iloc[:, 1], forward_periods
            )

            rolling_results.append({
                'train_ic': train_ic,
                'test_ic': test_ic,
                'train_end_date': aligned_data.index[start_idx-1],
                'test_end_date': aligned_data.index[start_idx+step_size-1]
            })

            validation_dates.append(aligned_data.index[start_idx+step_size-1])
            start_idx += step_size

        logger.info(f"滚动验证完成：{len(rolling_results)}个窗口")

        # 汇总滚动验证结果
        aggregated_in_sample = self._aggregate_rolling_ic([r['train_ic'] for r in rolling_results])
        aggregated_out_sample = self._aggregate_rolling_ic([r['test_ic'] for r in rolling_results])

        # 计算衰减指标
        degradation_metrics = self._calculate_degradation_metrics(aggregated_in_sample, aggregated_out_sample)

        # 健壮性评分（滚动验证要求更严格）
        robustness_score = self._calculate_robustness_score(degradation_metrics, strict_mode=True)
        is_robust = robustness_score > 0.8  # 80%阈值

        # 详细统计
        detailed_stats = {
            'rolling_periods': len(rolling_results),
            'window_size': window_size,
            'step_size': step_size,
            'validation_dates': validation_dates,
            'rolling_results': rolling_results
        }

        return ValidationResult(
            factor_name=factor_name,
            validation_type='walk_forward',
            in_sample_ic=aggregated_in_sample,
            out_sample_ic=aggregated_out_sample,
            degradation_metrics=degradation_metrics,
            is_robust=is_robust,
            robustness_score=robustness_score,
            detailed_stats=detailed_stats,
            validation_timestamp=datetime.now()
        )

    def _calculate_ic_multiple_periods(self, factor_series: pd.Series,
                                     returns_series: pd.Series,
                                     forward_periods: List[int]) -> Dict:
        """计算多个前瞻期的IC值"""
        ic_results = {}

        for period in forward_periods:
            try:
                # 计算单期IC
                ic_pearson = self.ic_calculator.calculate_single_ic(
                    factor_series, returns_series, period, "pearson", self.min_ic_samples
                )
                ic_spearman = self.ic_calculator.calculate_single_ic(
                    factor_series, returns_series, period, "spearman", self.min_ic_samples
                )

                # 计算滚动IC统计
                rolling_ic = self.ic_calculator.calculate_rolling_ic(
                    factor_series, returns_series, window=60, forward_periods=period
                )
                ic_stats = self.ic_statistics.calculate_ic_statistics(rolling_ic)

                ic_results[f'period_{period}'] = {
                    'ic_pearson': ic_pearson,
                    'ic_spearman': ic_spearman,
                    'rolling_ic_stats': ic_stats
                }

            except Exception as e:
                logger.warning(f"计算{period}期IC失败: {e}")
                ic_results[f'period_{period}'] = {
                    'ic_pearson': np.nan,
                    'ic_spearman': np.nan,
                    'rolling_ic_stats': {}
                }

        return ic_results

    def _calculate_degradation_metrics(self, in_sample_ic: Dict, out_sample_ic: Dict) -> Dict:
        """计算性能衰减指标"""
        degradation = {}

        for period_key in in_sample_ic.keys():
            if period_key in out_sample_ic:
                in_ic = in_sample_ic[period_key].get('ic_pearson', np.nan)
                out_ic = out_sample_ic[period_key].get('ic_pearson', np.nan)

                if not (np.isnan(in_ic) or np.isnan(out_ic)) and abs(in_ic) > 1e-6:
                    # IC绝对值衰减率
                    abs_degradation = (abs(in_ic) - abs(out_ic)) / abs(in_ic)

                    # IC符号一致性
                    sign_consistency = 1.0 if (in_ic * out_ic > 0) else 0.0

                    degradation[period_key] = {
                        'in_sample_ic': in_ic,
                        'out_sample_ic': out_ic,
                        'abs_degradation': abs_degradation,
                        'sign_consistency': sign_consistency
                    }
                else:
                    degradation[period_key] = {
                        'in_sample_ic': in_ic,
                        'out_sample_ic': out_ic,
                        'abs_degradation': 1.0,  # 完全衰减
                        'sign_consistency': 0.0
                    }

        # 计算平均衰减
        if degradation:
            avg_abs_degradation = np.mean([d['abs_degradation'] for d in degradation.values()])
            avg_sign_consistency = np.mean([d['sign_consistency'] for d in degradation.values()])

            degradation['summary'] = {
                'avg_abs_degradation': avg_abs_degradation,
                'avg_sign_consistency': avg_sign_consistency,
                'degradation_severity': self._categorize_degradation(avg_abs_degradation)
            }

        return degradation

    def _calculate_robustness_score(self, degradation_metrics: Dict, strict_mode: bool = False) -> float:
        """计算健壮性评分"""
        if 'summary' not in degradation_metrics:
            return 0.0

        summary = degradation_metrics['summary']
        avg_degradation = summary['avg_abs_degradation']
        sign_consistency = summary['avg_sign_consistency']

        # 基础健壮性评分
        # 衰减小于30%得满分，衰减100%得零分
        degradation_score = max(0, 1 - avg_degradation / 0.7) if avg_degradation < 0.7 else 0

        # 符号一致性权重
        consistency_score = sign_consistency

        # 综合评分
        base_score = degradation_score * 0.7 + consistency_score * 0.3

        # 严格模式（用于滚动验证）
        if strict_mode:
            base_score *= 0.8  # 更严格的标准

        return min(1.0, max(0.0, base_score))

    def _categorize_degradation(self, avg_degradation: float) -> str:
        """分类衰减程度"""
        if avg_degradation < 0.1:
            return "轻微衰减"
        elif avg_degradation < 0.3:
            return "中等衰减"
        elif avg_degradation < 0.5:
            return "显著衰减"
        else:
            return "严重衰减"

    def _aggregate_rolling_ic(self, rolling_ic_list: List[Dict]) -> Dict:
        """汇总滚动验证的IC结果"""
        if not rolling_ic_list:
            return {}

        aggregated = {}

        # 获取所有周期
        all_periods = set()
        for ic_dict in rolling_ic_list:
            all_periods.update(ic_dict.keys())

        for period in all_periods:
            pearson_values = []
            spearman_values = []

            for ic_dict in rolling_ic_list:
                if period in ic_dict:
                    pearson_ic = ic_dict[period].get('ic_pearson')
                    spearman_ic = ic_dict[period].get('ic_spearman')

                    if not np.isnan(pearson_ic):
                        pearson_values.append(pearson_ic)
                    if not np.isnan(spearman_ic):
                        spearman_values.append(spearman_ic)

            # 计算平均IC
            aggregated[period] = {
                'ic_pearson': np.mean(pearson_values) if pearson_values else np.nan,
                'ic_spearman': np.mean(spearman_values) if spearman_values else np.nan,
                'ic_std': np.std(pearson_values) if len(pearson_values) > 1 else 0,
                'rolling_count': len(pearson_values)
            }

        return aggregated

    def _compile_detailed_stats(self, train_data: pd.DataFrame, test_data: pd.DataFrame,
                              in_sample_ic: Dict, out_sample_ic: Dict) -> Dict:
        """编译详细统计信息"""
        return {
            'train_period': {
                'start_date': train_data.index[0],
                'end_date': train_data.index[-1],
                'length': len(train_data)
            },
            'test_period': {
                'start_date': test_data.index[0],
                'end_date': test_data.index[-1],
                'length': len(test_data)
            },
            'data_quality': {
                'train_missing_ratio': train_data.isnull().mean().mean(),
                'test_missing_ratio': test_data.isnull().mean().mean()
            }
        }

    def batch_validate_factors(self, factor_data: pd.DataFrame, returns: pd.Series,
                             validation_type: str = 'simple',
                             forward_periods: List[int] = None) -> Dict[str, ValidationResult]:
        """
        批量验证多个因子

        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率序列
            validation_type: 验证类型 ['simple', 'walk_forward']
            forward_periods: 前瞻期列表

        Returns:
            因子名称到验证结果的映射
        """
        results = {}
        total_factors = len(factor_data.columns)

        logger.info(f"开始批量验证{total_factors}个因子，验证类型：{validation_type}")

        for i, factor_name in enumerate(factor_data.columns, 1):
            logger.info(f"验证进度: {i}/{total_factors} - {factor_name}")

            try:
                factor_series = factor_data[factor_name]

                if validation_type == 'simple':
                    result = self.validate_factor_simple(factor_series, returns, forward_periods)
                elif validation_type == 'walk_forward':
                    result = self.walk_forward_validation(factor_series, returns, forward_periods=forward_periods)
                else:
                    raise ValueError(f"不支持的验证类型: {validation_type}")

                results[factor_name] = result

            except Exception as e:
                logger.error(f"验证因子{factor_name}失败: {e}")
                continue

        logger.info(f"批量验证完成: 成功验证{len(results)}个因子")
        return results


def create_cross_validator(min_train_periods: int = 252,
                          test_ratio: float = 0.3) -> FactorCrossValidator:
    """工厂函数：创建验证器"""
    return FactorCrossValidator(
        min_train_periods=min_train_periods,
        test_ratio=test_ratio
    )


if __name__ == "__main__":
    # 简单测试
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='D')

    # 模拟因子（前期有效，后期衰减）
    factor_data = pd.Series(np.random.randn(500), index=dates, name='test_factor')

    # 模拟收益率（与因子前期相关，后期相关性降低）
    early_corr = 0.3
    late_corr = 0.1
    split_point = 300

    early_returns = early_corr * factor_data[:split_point] + np.random.randn(split_point) * 0.02
    late_returns = late_corr * factor_data[split_point:] + np.random.randn(200) * 0.02
    returns = pd.concat([early_returns, late_returns])
    returns.name = 'returns'

    # 测试验证器
    validator = create_cross_validator()

    print("=== 样本外验证测试 ===")

    # 简单验证
    result = validator.validate_factor_simple(factor_data, returns)
    print(f"因子: {result.factor_name}")
    print(f"健壮性: {result.is_robust}")
    print(f"健壮性评分: {result.robustness_score:.3f}")

    if 'summary' in result.degradation_metrics:
        summary = result.degradation_metrics['summary']
        print(f"平均衰减: {summary['avg_abs_degradation']:.3f}")
        print(f"符号一致性: {summary['avg_sign_consistency']:.3f}")
        print(f"衰减程度: {summary['degradation_severity']}")

    print("\n=== 测试完成 ===")