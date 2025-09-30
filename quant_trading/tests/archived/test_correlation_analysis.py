"""
相关性分析逻辑验证测试
验证因子相关性计算和冗余检测的准确性
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from quant_trading.analyzers.correlation.core import CorrelationCalculator, RedundancyDetector


class TestCorrelationAnalysis(unittest.TestCase):
    """相关性分析测试类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)

        # 创建测试因子数据
        n_samples = 100
        dates = pd.date_range('2023-01-01', periods=n_samples, freq='D')

        # 创建不同相关性的因子
        base_factor = np.random.normal(0, 1, n_samples)

        self.factor_data = pd.DataFrame({
            'factor_A': base_factor,
            'factor_B': base_factor + np.random.normal(0, 0.1, n_samples),  # 高相关
            'factor_C': base_factor * 0.5 + np.random.normal(0, 0.5, n_samples),  # 中等相关
            'factor_D': np.random.normal(0, 1, n_samples),  # 独立因子
            'factor_E': -base_factor + np.random.normal(0, 0.1, n_samples),  # 负相关
        }, index=dates)

        self.calculator = CorrelationCalculator()
        self.detector = RedundancyDetector()

    def test_correlation_matrix_calculation(self):
        """测试相关性矩阵计算"""
        corr_matrix = self.calculator.calculate_correlation_matrix(
            self.factor_data, method="pearson"
        )

        # 验证矩阵形状
        expected_shape = (len(self.factor_data.columns), len(self.factor_data.columns))
        self.assertEqual(corr_matrix.shape, expected_shape)

        # 验证对角线为1
        diagonal = np.diag(corr_matrix.values)
        np.testing.assert_array_almost_equal(diagonal, np.ones(len(diagonal)), decimal=6)

        # 验证对称性
        np.testing.assert_array_almost_equal(
            corr_matrix.values, corr_matrix.values.T, decimal=6
        )

        # 验证值在[-1, 1]范围内
        self.assertTrue(np.all(corr_matrix.values >= -1))
        self.assertTrue(np.all(corr_matrix.values <= 1))

        print("相关性矩阵:")
        print(corr_matrix.round(3))

    def test_high_correlation_detection(self):
        """测试高相关性检测"""
        corr_matrix = self.calculator.calculate_correlation_matrix(self.factor_data)

        # 使用不同阈值测试
        high_corr_pairs_08 = self.calculator.find_high_correlation_pairs(
            corr_matrix, threshold=0.8
        )
        high_corr_pairs_05 = self.calculator.find_high_correlation_pairs(
            corr_matrix, threshold=0.5
        )

        # 较低阈值应该找到更多相关性对
        self.assertGreaterEqual(len(high_corr_pairs_05), len(high_corr_pairs_08))

        # 验证结果格式
        for factor1, factor2, corr_value in high_corr_pairs_08:
            self.assertIn(factor1, self.factor_data.columns)
            self.assertIn(factor2, self.factor_data.columns)
            self.assertNotEqual(factor1, factor2)
            self.assertGreaterEqual(abs(corr_value), 0.8)

        print(f"0.8阈值高相关对: {len(high_corr_pairs_08)}")
        print(f"0.5阈值高相关对: {len(high_corr_pairs_05)}")

        if high_corr_pairs_08:
            print("高相关因子对:")
            for pair in high_corr_pairs_08:
                print(f"  {pair[0]} - {pair[1]}: {pair[2]:.3f}")

    def test_redundancy_detection(self):
        """测试冗余因子组检测"""
        corr_matrix = self.calculator.calculate_correlation_matrix(self.factor_data)

        redundant_groups = self.detector.identify_redundant_groups(
            corr_matrix, threshold=0.8
        )

        # 验证组的格式
        for group_id, factors in redundant_groups.items():
            self.assertIsInstance(factors, set)
            self.assertGreater(len(factors), 1)  # 组内至少有2个因子

            # 验证因子名称有效
            for factor in factors:
                self.assertIn(factor, self.factor_data.columns)

        print(f"发现冗余组数量: {len(redundant_groups)}")
        for group_id, factors in redundant_groups.items():
            print(f"{group_id}: {sorted(factors)}")

    def test_correlation_summary_statistics(self):
        """测试相关性汇总统计"""
        corr_matrix = self.calculator.calculate_correlation_matrix(self.factor_data)

        summary = self.detector.calculate_correlation_summary(corr_matrix)

        # 验证必要的统计量
        required_keys = [
            'total_pairs', 'mean_correlation', 'std_correlation',
            'max_correlation', 'min_correlation'
        ]

        for key in required_keys:
            self.assertIn(key, summary)
            self.assertIsNotNone(summary[key])

        # 验证数值合理性
        n_factors = len(self.factor_data.columns)
        expected_pairs = n_factors * (n_factors - 1) // 2
        self.assertEqual(summary['total_pairs'], expected_pairs)

        self.assertGreaterEqual(summary['max_correlation'], summary['min_correlation'])
        self.assertLessEqual(summary['max_correlation'], 1.0)
        self.assertGreaterEqual(summary['min_correlation'], -1.0)

        print("相关性统计摘要:")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

    def test_known_correlations(self):
        """测试已知相关性的验证"""
        # 创建完全相关的因子
        perfect_corr_data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10],  # y = 2*x (完全正相关)
            'z': [-1, -2, -3, -4, -5]  # z = -x (完全负相关)
        })

        corr_matrix = self.calculator.calculate_correlation_matrix(perfect_corr_data)

        # 验证完全相关性
        self.assertAlmostEqual(corr_matrix.loc['x', 'y'], 1.0, places=6)
        self.assertAlmostEqual(corr_matrix.loc['x', 'z'], -1.0, places=6)
        self.assertAlmostEqual(corr_matrix.loc['y', 'z'], -1.0, places=6)

        # 检测高相关性
        high_corr = self.calculator.find_high_correlation_pairs(
            corr_matrix, threshold=0.9
        )

        # 应该找到3对高相关关系
        self.assertEqual(len(high_corr), 3)

        print("完全相关测试:")
        print(corr_matrix.round(6))

    def test_spearman_vs_pearson(self):
        """测试Spearman与Pearson相关性的差异"""
        # 创建非线性关系数据
        x = np.arange(100)
        y = x ** 2 + np.random.normal(0, 10, 100)  # 非线性关系

        nonlinear_data = pd.DataFrame({'x': x, 'y': y})

        pearson_corr = self.calculator.calculate_correlation_matrix(
            nonlinear_data, method="pearson"
        )
        spearman_corr = self.calculator.calculate_correlation_matrix(
            nonlinear_data, method="spearman"
        )

        pearson_xy = pearson_corr.loc['x', 'y']
        spearman_xy = spearman_corr.loc['x', 'y']

        # 对于非线性关系，Spearman通常更高
        print(f"非线性关系 - Pearson: {pearson_xy:.4f}, Spearman: {spearman_xy:.4f}")

        # 两者都应该检测到正相关
        self.assertGreater(pearson_xy, 0)
        self.assertGreater(spearman_xy, 0)

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试空数据
        empty_data = pd.DataFrame()
        empty_corr = self.calculator.calculate_correlation_matrix(empty_data)
        self.assertTrue(empty_corr.empty)

        # 测试单列数据
        single_col = pd.DataFrame({'single': [1, 2, 3, 4, 5]})
        single_corr = self.calculator.calculate_correlation_matrix(single_col)
        self.assertEqual(single_corr.shape, (1, 1))
        self.assertEqual(single_corr.iloc[0, 0], 1.0)

        # 测试常数列
        constant_data = pd.DataFrame({
            'const': [1, 1, 1, 1, 1],
            'var': [1, 2, 3, 4, 5]
        })
        const_corr = self.calculator.calculate_correlation_matrix(constant_data)

        # 常数与变量的相关性应该是NaN
        self.assertTrue(np.isnan(const_corr.loc['const', 'var']))

    def test_large_scale_performance(self):
        """测试大规模数据的性能"""
        # 创建更大的数据集
        np.random.seed(42)
        large_data = pd.DataFrame(
            np.random.normal(0, 1, (1000, 20)),
            columns=[f'factor_{i}' for i in range(20)]
        )

        # 计算相关性矩阵
        import time
        start_time = time.time()

        corr_matrix = self.calculator.calculate_correlation_matrix(large_data)

        end_time = time.time()
        computation_time = end_time - start_time

        # 验证结果正确性
        self.assertEqual(corr_matrix.shape, (20, 20))

        # 检查计算时间（应该在合理范围内）
        self.assertLess(computation_time, 5.0)  # 应该在5秒内完成

        print(f"大规模计算时间: {computation_time:.3f}秒")


if __name__ == '__main__':
    unittest.main(verbosity=2)