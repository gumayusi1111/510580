"""
MAX_DD测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import MAX_DD
from validation import MaxDdValidation


def test_maxdd_basic():
    print("🧪 测试MAX_DD基础功能...")

    # 创建测试数据（先上升后下降的价格模式）
    prices = []
    base = 100
    for i in range(30):
        if i < 15:  # 前15天上升
            price = base + 2 * i + np.random.normal(0, 0.5)
        else:  # 后15天下降
            price = base + 30 - 1.5 * (i - 15) + np.random.normal(0, 0.5)
        prices.append(max(price, 50))  # 确保价格不会过低

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': prices
    })

    factor = MAX_DD({"periods": [20, 30]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 检查结果
    dd_20_values = result['MAX_DD_20'].dropna()
    dd_30_values = result['MAX_DD_30'].dropna()

    if len(dd_20_values) > 0:
        print(f"   MAX_DD_20样例: 最新={dd_20_values.iloc[-1]:.2f}%, 平均={dd_20_values.mean():.2f}%")
    if len(dd_30_values) > 0:
        print(f"   MAX_DD_30样例: 最新={dd_30_values.iloc[-1]:.2f}%, 平均={dd_30_values.mean():.2f}%")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    if len(test_data) >= 20:
        recent_prices = test_data['hfq_close'].tail(20)
        cumulative_max = recent_prices.expanding().max()
        drawdown = (recent_prices - cumulative_max) / cumulative_max
        manual_max_dd = abs(drawdown.min()) * 100

        print(f"   手工验证MAX_DD_20: {manual_max_dd:.6f}%")
        print(f"   因子结果MAX_DD_20: {result['MAX_DD_20'].iloc[-1]:.6f}%")

    return result


def test_maxdd_validation():
    print("🧪 测试MAX_DD验证功能...")

    # 创建包含明显回撤的测试数据
    np.random.seed(42)
    n_days = 60

    # 生成具有回撤的价格序列
    prices = [100]
    for i in range(n_days):
        if i < 20:
            # 上升阶段
            daily_return = np.random.normal(0.01, 0.02)
        elif i < 35:
            # 下降阶段（产生回撤）
            daily_return = np.random.normal(-0.015, 0.02)
        else:
            # 恢复阶段
            daily_return = np.random.normal(0.008, 0.015)

        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    factor = MAX_DD()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = MaxDdValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_maxdd_edge_cases():
    print("🧪 测试MAX_DD边界情况...")

    # 测试恒定价格（无回撤）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [100.0] * 25  # 恒定价格
    })

    factor = MAX_DD()
    result_constant = factor.calculate_vectorized(constant_data)

    dd_20_constant = result_constant['MAX_DD_20'].iloc[-1]
    dd_60_constant = result_constant['MAX_DD_60'].iloc[-1]

    print(f"   恒定价格MAX_DD_20: {dd_20_constant:.2f}%")
    print(f"   恒定价格MAX_DD_60: {dd_60_constant:.2f}%")

    # 恒定价格时，最大回撤应该为0
    zero_dd_check = abs(dd_20_constant) < 0.001 and abs(dd_60_constant) < 0.001
    print(f"   零回撤检查: {'✅ 正确' if zero_dd_check else '❌ 错误'} (接近零)")

    # 测试严重回撤数据
    crash_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': [100] + [100 - 2*i for i in range(1, 21)] + [60 + i for i in range(9)]  # 先跌后涨
    })

    try:
        result_crash = factor.calculate_vectorized(crash_data)

        crash_dd_20 = result_crash['MAX_DD_20'].iloc[-1]
        crash_dd_60 = result_crash['MAX_DD_60'].iloc[-1]

        print(f"   严重回撤MAX_DD_20: {crash_dd_20:.1f}%")
        print(f"   严重回撤MAX_DD_60: {crash_dd_60:.1f}%")

        # 检查严重回撤是否在合理范围内
        severe_check = 20 < crash_dd_20 < 100 and 20 < crash_dd_60 < 100
        print(f"   严重回撤检查: {'✅ 合理' if severe_check else '⚠️ 异常'} (20%-100%范围)")

        # 测试不同周期参数
        factor_single = MAX_DD({"periods": [10]})
        result_single = factor_single.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 15,
            'trade_date': pd.date_range('2025-01-01', periods=15),
            'hfq_close': [100 - i * 2 for i in range(15)]  # 持续下跌
        }))

        factor_multi = MAX_DD({"periods": [5, 10, 15]})
        result_multi = factor_multi.calculate_vectorized(test_data)

        # 多周期因子应该有更多输出列
        single_cols = [col for col in result_single.columns if col.startswith('MAX_DD_')]
        multi_cols = [col for col in result_multi.columns if col.startswith('MAX_DD_')]

        period_check = len(multi_cols) > len(single_cols)
        print(f"   多周期测试: 单周期={len(single_cols)}列, 多周期={len(multi_cols)}列 ({'✅ 正确' if period_check else '❌ 错误'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_maxdd_different_periods():
    print("🧪 测试MAX_DD不同周期参数...")

    # 创建具有多个回撤周期的测试数据
    n_days = 100
    prices = [100]

    # 模拟多个上升下降周期
    for i in range(n_days):
        cycle_phase = (i // 20) % 4  # 每20天一个阶段
        if cycle_phase == 0:     # 上升
            daily_return = np.random.normal(0.005, 0.01)
        elif cycle_phase == 1:   # 高位震荡
            daily_return = np.random.normal(0.001, 0.015)
        elif cycle_phase == 2:   # 下跌
            daily_return = np.random.normal(-0.008, 0.01)
        else:                    # 底部反弹
            daily_return = np.random.normal(0.01, 0.01)

        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    periods_to_test = [10, 20, 40, 80]
    results = {}

    for period in periods_to_test:
        factor = MAX_DD({"periods": [period]})
        result = factor.calculate_vectorized(test_data)
        results[period] = result

        dd_col = f'MAX_DD_{period}'
        dd_values = result[dd_col].dropna()

        if len(dd_values) > 0:
            avg_dd = dd_values.mean()
            max_dd = dd_values.max()
            latest_dd = dd_values.iloc[-1]
            print(f"   MAX_DD_{period}: 平均={avg_dd:.2f}%, 最大={max_dd:.2f}%, 最新={latest_dd:.2f}%")

    # 验证因子信息
    factor_info = MAX_DD({"periods": [20, 60]}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   计算公式: {factor_info['formula']}")

    return results


def test_maxdd_drawdown_analysis():
    print("🧪 测试MAX_DD回撤分析...")

    # 创建包含典型市场回撤的数据
    market_phases = [
        ('牛市', 40, 0.008),   # 牛市阶段
        ('调整', 20, -0.015),  # 调整阶段
        ('熊市', 30, -0.01),   # 熊市阶段
        ('反弹', 25, 0.012),   # 反弹阶段
        ('震荡', 35, 0.002)    # 震荡阶段
    ]

    all_prices = [100]
    phase_boundaries = [0]

    for phase_name, days, trend in market_phases:
        for _ in range(days):
            noise = np.random.normal(0, 0.008)
            daily_return = trend + noise
            all_prices.append(all_prices[-1] * (1 + daily_return))
        phase_boundaries.append(len(all_prices) - 1)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * len(all_prices),
        'trade_date': pd.date_range('2025-01-01', periods=len(all_prices)),
        'hfq_close': all_prices
    })

    factor = MAX_DD({"periods": [20, 60]})
    result = factor.calculate_vectorized(test_data)

    # 分析各阶段的最大回撤
    print("   各市场阶段的最大回撤:")
    for i, (phase_name, days, expected_trend) in enumerate(market_phases):
        start_idx = phase_boundaries[i]
        end_idx = phase_boundaries[i + 1]

        if end_idx - start_idx >= 20:  # 确保有足够数据
            phase_dd_20 = result['MAX_DD_20'].iloc[start_idx:end_idx]
            phase_dd_60 = result['MAX_DD_60'].iloc[start_idx:end_idx]

            avg_dd_20 = phase_dd_20.mean()
            max_dd_20 = phase_dd_20.max()

            print(f"     {phase_name}阶段: 20日平均回撤={avg_dd_20:.2f}%, 最大回撤={max_dd_20:.2f}%")

    # 分析回撤的分布特征
    dd_20_all = result['MAX_DD_20'].dropna()
    dd_60_all = result['MAX_DD_60'].dropna()

    if len(dd_20_all) >= 20:
        # 计算回撤分位数
        percentiles = [25, 50, 75, 90, 95]
        print("   20日回撤分布:")
        for p in percentiles:
            value = dd_20_all.quantile(p/100)
            print(f"     {p}%分位: {value:.2f}%")

        # 分析极端回撤事件（>95%分位）
        extreme_threshold = dd_20_all.quantile(0.95)
        extreme_count = (dd_20_all > extreme_threshold).sum()
        print(f"   极端回撤事件(>{extreme_threshold:.1f}%): {extreme_count}次")

    # 分析回撤恢复时间
    dd_20_series = result['MAX_DD_20']
    recovery_times = []

    # 寻找回撤峰值和恢复点
    for i in range(10, len(dd_20_series) - 10):
        if pd.notna(dd_20_series.iloc[i]):
            current_dd = dd_20_series.iloc[i]
            # 如果是局部峰值（回撤最大点）
            window = dd_20_series.iloc[i-5:i+6]
            if current_dd == window.max() and current_dd > 5:  # 至少5%的回撤
                # 寻找恢复点（回撤降至峰值50%以下）
                recovery_target = current_dd * 0.5
                for j in range(i+1, min(i+21, len(dd_20_series))):  # 最多寻找20天
                    if pd.notna(dd_20_series.iloc[j]) and dd_20_series.iloc[j] < recovery_target:
                        recovery_times.append(j - i)
                        break

    if recovery_times:
        avg_recovery = sum(recovery_times) / len(recovery_times)
        print(f"   平均回撤恢复时间: {avg_recovery:.1f}天 (基于{len(recovery_times)}次回撤)")

    return result


def run_all_tests():
    print("📊 最大回撤因子模块化测试")
    print("=" * 50)

    try:
        test_maxdd_basic()
        print()
        test_maxdd_validation()
        print()
        test_maxdd_edge_cases()
        print()
        test_maxdd_different_periods()
        print()
        test_maxdd_drawdown_analysis()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()