"""
IC计算逻辑验证测试
验证信息系数计算的准确性和金融合理性
"""

import unittest
import pandas as pd
import numpy as np
from scipy import stats
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from quant_trading.analyzers.ic.core import ICCalculator, ICStatistics


class TestICCalculations(unittest.TestCase):
    """IC计算测试类"""

    def setUp(self):
        """设置测试数据"""
        # 创建模拟因子数据和收益率数据
        np.random.seed(42)  # 确保结果可重现

        # 生成100个交易日的数据
        dates = pd.date_range('2023-01-01', periods=100, freq='D')

        # 模拟因子数据（具有一定预测能力）
        self.factor_data = pd.Series(
            np.random.normal(0, 1, 100),
            index=dates,
            name='test_factor'
        )

        # 模拟收益率数据（与因子有一定相关性）
        noise = np.random.normal(0, 0.02, 100)
        self.returns = pd.Series(
            self.factor_data * 0.1 + noise,  # 因子解释10%的收益
            index=dates,
            name='returns'
        )

        self.calculator = ICCalculator()
        self.statistics = ICStatistics()

    def test_ic_calculation_basic(self):
        """测试基本IC计算"""
        ic_value = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, forward_periods=1, method="pearson"
        )

        # IC值应该在-1到1之间
        self.assertGreaterEqual(ic_value, -1.0)
        self.assertLessEqual(ic_value, 1.0)

        # IC值应该是有效的数值（不为NaN）
        self.assertFalse(np.isnan(ic_value))

        print(f"基本IC值: {ic_value:.4f}")

    def test_ic_vs_scipy_correlation(self):
        """验证IC计算与scipy相关性计算的一致性"""
        ic_value = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, forward_periods=1, method="pearson"
        )

        # 手动计算相关性
        aligned_data = pd.concat([self.factor_data, self.returns], axis=1).dropna()
        factor_values = aligned_data.iloc[:-1, 0]  # 前n-1个因子值
        future_returns = aligned_data.iloc[1:, 1]   # 后n-1个收益率

        manual_corr, _ = stats.pearsonr(factor_values, future_returns)

        # IC值应该与手动计算的相关性非常接近
        self.assertAlmostEqual(ic_value, manual_corr, places=6)

        print(f"IC值: {ic_value:.6f}, 手动计算: {manual_corr:.6f}")

    def test_ic_forward_periods(self):
        """测试不同前瞻期的IC计算"""
        ic_1 = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, forward_periods=1
        )
        ic_5 = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, forward_periods=5
        )

        # 都应该是有效的IC值
        self.assertFalse(np.isnan(ic_1))
        self.assertFalse(np.isnan(ic_5))

        # 通常前瞻期越长，IC值会衰减
        print(f"1期前瞻IC: {ic_1:.4f}, 5期前瞻IC: {ic_5:.4f}")

    def test_rolling_ic_calculation(self):
        """测试滚动IC计算"""
        rolling_ic = self.calculator.calculate_rolling_ic(
            self.factor_data, self.returns, window=30, forward_periods=1
        )

        # 检查返回值类型和长度
        self.assertIsInstance(rolling_ic, pd.Series)
        self.assertGreater(len(rolling_ic), 0)

        # 所有IC值都应该在合理范围内
        self.assertTrue(all(rolling_ic.between(-1, 1, inclusive='both')))

        print(f"滚动IC数量: {len(rolling_ic)}, 均值: {rolling_ic.mean():.4f}")

    def test_ic_statistics(self):
        """测试IC统计量计算"""
        rolling_ic = self.calculator.calculate_rolling_ic(
            self.factor_data, self.returns, window=30
        )

        stats_result = self.statistics.calculate_ic_statistics(rolling_ic)

        # 检查必要的统计量
        required_keys = ['ic_mean', 'ic_std', 'ic_ir', 'ic_positive_ratio', 'ic_abs_mean']
        for key in required_keys:
            self.assertIn(key, stats_result)
            self.assertIsNotNone(stats_result[key])

        # IC信息比率应该等于均值除以标准差
        ic_ir_manual = stats_result['ic_mean'] / stats_result['ic_std']
        self.assertAlmostEqual(stats_result['ic_ir'], ic_ir_manual, places=6)

        # IC胜率应该在0-1之间
        self.assertGreaterEqual(stats_result['ic_positive_ratio'], 0)
        self.assertLessEqual(stats_result['ic_positive_ratio'], 1)

        print(f"IC统计量: {stats_result}")

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试数据不足的情况
        short_factor = self.factor_data.head(10)
        short_returns = self.returns.head(10)

        ic_short = self.calculator.calculate_single_ic(
            short_factor, short_returns, forward_periods=1, min_periods=20
        )

        # 数据不足时应该返回NaN
        self.assertTrue(np.isnan(ic_short))

        # 测试全为常数的因子
        constant_factor = pd.Series([1.0] * 100, index=self.factor_data.index)
        ic_constant = self.calculator.calculate_single_ic(
            constant_factor, self.returns, forward_periods=1
        )

        # 常数因子的IC应该接近0或为NaN
        self.assertTrue(np.isnan(ic_constant) or abs(ic_constant) < 1e-10)

    def test_spearman_ic(self):
        """测试Spearman IC计算"""
        ic_pearson = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, method="pearson"
        )
        ic_spearman = self.calculator.calculate_single_ic(
            self.factor_data, self.returns, method="spearman"
        )

        # 两种方法都应该给出有效结果
        self.assertFalse(np.isnan(ic_pearson))
        self.assertFalse(np.isnan(ic_spearman))

        # 对于单调数据，Spearman和Pearson应该相似
        print(f"Pearson IC: {ic_pearson:.4f}, Spearman IC: {ic_spearman:.4f}")

    def test_financial_reasonableness(self):
        """测试金融合理性"""
        # 创建明显的预测性因子
        strong_factor = pd.Series(range(100), index=self.factor_data.index)
        strong_returns = pd.Series([i * 0.01 for i in range(100)], index=self.returns.index)

        strong_ic = self.calculator.calculate_single_ic(strong_factor, strong_returns)

        # 强预测性因子应该有很高的IC
        self.assertGreater(abs(strong_ic), 0.8)

        # 创建反向预测因子
        reverse_returns = -strong_returns
        reverse_ic = self.calculator.calculate_single_ic(strong_factor, reverse_returns)

        # 反向关系应该产生负IC
        self.assertLess(reverse_ic, -0.8)

        print(f"强正相关IC: {strong_ic:.4f}, 强负相关IC: {reverse_ic:.4f}")


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)