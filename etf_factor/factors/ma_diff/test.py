"""
MA_DIFF测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import MA_DIFF
from validation import MaDiffValidation


def test_madiff_basic():
    print("🧪 测试MA_DIFF基础功能...")

    # 创建测试数据（递增趋势）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })

    factor = MA_DIFF({"pairs": [(3, 5), (5, 10)]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   MA_DIFF_3_5样例: {result['MA_DIFF_3_5'].iloc[:5].tolist()}")
    print(f"   MA_DIFF_5_10样例: {result['MA_DIFF_5_10'].iloc[:5].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_3 = test_data['hfq_close'].tail(3).mean()  # 最近3天平均
    recent_5 = test_data['hfq_close'].tail(5).mean()  # 最近5天平均
    manual_diff_3_5 = recent_3 - recent_5

    print(f"   手工验证MA_DIFF_3_5: {manual_diff_3_5:.6f}")
    print(f"   因子结果MA_DIFF_3_5: {result['MA_DIFF_3_5'].iloc[-1]:.6f}")

    # 在上升趋势中，短期MA应该高于长期MA
    trend_check = result['MA_DIFF_3_5'].iloc[-1] > 0
    print(f"   趋势检查: {'✅ 正确' if trend_check else '❌ 错误'} (上升趋势中短期MA>长期MA)")

    return result


def test_madiff_validation():
    print("🧪 测试MA_DIFF验证功能...")

    # 创建更长的数据用于统计验证
    np.random.seed(42)
    n_days = 70
    base_price = 100

    # 生成带趋势的价格序列
    prices = [base_price]
    for i in range(n_days):
        # 添加趋势 + 随机噪声
        trend = 0.002  # 轻微上升趋势
        noise = np.random.normal(0, 0.01)
        daily_return = trend + noise
        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    factor = MA_DIFF()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = MaDiffValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_madiff_edge_cases():
    print("🧪 测试MA_DIFF边界情况...")

    # 测试恒定价格
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10.0] * 25  # 恒定价格
    })

    factor = MA_DIFF()
    result_constant = factor.calculate_vectorized(constant_data)

    # 恒定价格时，所有MA_DIFF应该为0
    all_zero = True
    for col in result_constant.columns:
        if col.startswith('MA_DIFF_'):
            if not result_constant[col].iloc[-1] == 0:
                all_zero = False
                break

    print(f"   恒定价格MA_DIFF: {'✅ 全为零' if all_zero else '❌ 存在非零值'}")

    # 测试极端波动数据
    volatile_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': [10 + 5 * np.sin(i * 0.5) for i in range(30)]  # 正弦波价格
    })

    try:
        result_volatile = factor.calculate_vectorized(volatile_data)

        # 检查波动数据中的MA_DIFF
        ma_diff_5_10 = result_volatile['MA_DIFF_5_10'].iloc[-5:]
        volatility = ma_diff_5_10.std()

        print(f"   波动数据MA_DIFF_5_10波动性: {volatility:.4f} ({'✅ 合理' if 0.1 < volatility < 10 else '⚠️ 异常'})")

        # 测试不同参数组合
        factor_custom = MA_DIFF({"pairs": [(2, 4), (4, 8), (8, 16)]})
        result_custom = factor_custom.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 20,
            'trade_date': pd.date_range('2025-01-01', periods=20),
            'hfq_close': [10 + i * 0.5 for i in range(20)]  # 线性上升
        }))

        # 检查自定义参数的结果
        custom_cols = [col for col in result_custom.columns if col.startswith('MA_DIFF_')]
        custom_check = len(custom_cols) == 3
        print(f"   自定义参数: 预期3列，实际{len(custom_cols)}列 ({'✅ 正确' if custom_check else '❌ 错误'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_madiff_different_pairs():
    print("🧪 测试MA_DIFF不同参数组合...")

    # 创建具有明显趋势的测试数据
    n_days = 60
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * n_days,
        'trade_date': pd.date_range('2025-01-01', periods=n_days),
        'hfq_close': [50 + i * 0.5 + 0.5 * np.sin(i * 0.3) for i in range(n_days)]
    })

    pairs_to_test = [
        [(5, 10)],
        [(5, 10), (10, 20)],
        [(5, 20), (10, 30), (20, 60)],
        [(3, 7), (7, 14), (14, 28), (28, 56)]
    ]

    for i, pairs in enumerate(pairs_to_test):
        factor = MA_DIFF({"pairs": pairs})
        result = factor.calculate_vectorized(test_data)

        # 统计输出
        diff_cols = [col for col in result.columns if col.startswith('MA_DIFF_')]
        print(f"   参数组{i+1}: {len(pairs)}对差值 -> {len(diff_cols)}列输出")

        # 分析最新差值
        latest_diffs = {}
        for col in diff_cols:
            latest_diffs[col] = result[col].iloc[-1]

        # 显示部分差值
        for col, value in list(latest_diffs.items())[:2]:
            print(f"     {col}: {value:.4f}")

    # 验证因子信息
    factor_info = MA_DIFF({"pairs": [(5, 10), (5, 20)]}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   计算公式: {factor_info['formula']}")

    return test_data


def test_madiff_trend_analysis():
    print("🧪 测试MA_DIFF趋势分析...")

    # 创建包含多个趋势阶段的数据
    phases = [
        ('上升', 30, 0.01),    # 上升阶段
        ('横盘', 20, 0.002),   # 横盘阶段
        ('下降', 30, -0.008),  # 下降阶段
        ('反弹', 20, 0.015)    # 反弹阶段
    ]

    all_prices = [100]
    phase_info = []

    for phase_name, days, trend in phases:
        start_idx = len(all_prices) - 1
        for _ in range(days):
            noise = np.random.normal(0, 0.005)
            daily_return = trend + noise
            all_prices.append(all_prices[-1] * (1 + daily_return))
        end_idx = len(all_prices) - 1
        phase_info.append((phase_name, start_idx, end_idx, trend))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * len(all_prices),
        'trade_date': pd.date_range('2025-01-01', periods=len(all_prices)),
        'hfq_close': all_prices
    })

    factor = MA_DIFF({"pairs": [(5, 20), (10, 30)]})
    result = factor.calculate_vectorized(test_data)

    # 分析各阶段的MA_DIFF特征
    print("   各趋势阶段的MA差值特征:")
    for phase_name, start_idx, end_idx, expected_trend in phase_info:
        if end_idx - start_idx >= 20:  # 确保有足够数据
            phase_data = result['MA_DIFF_5_20'].iloc[start_idx:end_idx]
            phase_diff_avg = phase_data.mean()
            phase_diff_trend = phase_data.iloc[-5:].mean() - phase_data.iloc[:5].mean()

            trend_direction = "↑" if phase_diff_avg > 0 else "↓" if phase_diff_avg < 0 else "→"
            print(f"     {phase_name}阶段: 平均差值={phase_diff_avg:.4f} {trend_direction}")

    # 分析金叉死叉点
    ma_diff_5_20 = result['MA_DIFF_5_20']
    golden_crosses = []  # 金叉：差值从负转正
    death_crosses = []   # 死叉：差值从正转负

    for i in range(1, len(ma_diff_5_20)):
        if pd.notna(ma_diff_5_20.iloc[i]) and pd.notna(ma_diff_5_20.iloc[i-1]):
            if ma_diff_5_20.iloc[i] > 0 and ma_diff_5_20.iloc[i-1] <= 0:
                golden_crosses.append(i)
            elif ma_diff_5_20.iloc[i] < 0 and ma_diff_5_20.iloc[i-1] >= 0:
                death_crosses.append(i)

    print(f"   MA金叉点(5MA上穿20MA): {len(golden_crosses)}次")
    print(f"   MA死叉点(5MA下穿20MA): {len(death_crosses)}次")

    return result


def run_all_tests():
    print("📊 移动均线差值因子模块化测试")
    print("=" * 50)

    try:
        test_madiff_basic()
        print()
        test_madiff_validation()
        print()
        test_madiff_edge_cases()
        print()
        test_madiff_different_pairs()
        print()
        test_madiff_trend_analysis()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()