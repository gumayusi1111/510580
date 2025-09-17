"""
BB_WIDTH测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import BB_WIDTH
from validation import BbWidthValidation


def test_bbwidth_basic():
    print("🧪 测试BB_WIDTH基础功能...")

    # 创建测试数据（包含趋势和震荡）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [
            10.0, 10.1, 10.2, 10.15, 10.3,  # 上升趋势
            10.25, 10.4, 10.35, 10.5, 10.45, # 继续上升
            10.6, 10.55, 10.7, 10.65, 10.8,  # 持续上升
            10.9, 10.85, 11.0, 10.95, 11.1,  # 高位震荡
            11.05, 11.2, 11.15, 11.3, 11.25  # 继续震荡
        ]
    })

    factor = BB_WIDTH({"period": 20, "std_dev": 2})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   BB_WIDTH_20样例: {result['BB_WIDTH_20'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_data = test_data['hfq_close'].tail(20)
    manual_mid = recent_data.mean()
    manual_std = recent_data.std()
    manual_upper = manual_mid + 2 * manual_std
    manual_lower = manual_mid - 2 * manual_std
    manual_width = ((manual_upper - manual_lower) / manual_mid) * 100

    print(f"   手工验证宽度: {manual_width:.4f}%")
    print(f"   因子结果宽度: {result['BB_WIDTH_20'].iloc[-1]:.4f}%")
    print(f"   计算误差: {abs(result['BB_WIDTH_20'].iloc[-1] - manual_width):.6f}%")

    return result


def test_bbwidth_validation():
    print("🧪 测试BB_WIDTH验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(42)
    n_days = 50
    base_price = 100

    # 生成具有不同波动阶段的价格序列
    prices = [base_price]
    for i in range(n_days):
        if i < 20:
            vol = 0.005  # 低波动期
        elif i < 35:
            vol = 0.02   # 高波动期
        else:
            vol = 0.01   # 中等波动期

        daily_return = np.random.normal(0, vol)
        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    factor = BB_WIDTH()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = BbWidthValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_bbwidth_edge_cases():
    print("🧪 测试BB_WIDTH边界情况...")

    # 测试恒定价格（零波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10.0] * 25  # 恒定价格
    })

    factor = BB_WIDTH()
    result_constant = factor.calculate_vectorized(constant_data)

    constant_width = result_constant['BB_WIDTH_20'].iloc[-1]
    print(f"   恒定价格BB_WIDTH: {constant_width:.4f}%")

    # 恒定价格时，布林带宽度应该为0或接近0
    zero_width_check = abs(constant_width) < 0.001
    print(f"   零宽度检查: {'✅ 正确' if zero_width_check else '❌ 错误'} (接近零)")

    # 测试高波动数据
    high_vol_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10 * (1.05 if i % 2 == 0 else 0.95) ** (i // 2) for i in range(25)]  # 交替大幅波动
    })

    try:
        result_high_vol = factor.calculate_vectorized(high_vol_data)

        high_vol_width = result_high_vol['BB_WIDTH_20'].iloc[-1]
        print(f"   高波动BB_WIDTH: {high_vol_width:.2f}% ({'✅ 合理' if 5 < high_vol_width < 200 else '⚠️ 极端'})")

        # 测试不同标准差参数
        factor_narrow = BB_WIDTH({"period": 20, "std_dev": 1})
        result_narrow = factor_narrow.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 25,
            'trade_date': pd.date_range('2025-01-01', periods=25),
            'hfq_close': [10 + 0.5 * np.sin(i * 0.3) for i in range(25)]  # 正弦波价格
        }))

        factor_wide = BB_WIDTH({"period": 20, "std_dev": 3})
        result_wide = factor_wide.calculate_vectorized(test_data)

        # 标准差越大，布林带越宽
        width_narrow = result_narrow['BB_WIDTH_20'].iloc[-1]
        width_wide = result_wide['BB_WIDTH_20'].iloc[-1]

        std_dev_check = width_wide > width_narrow
        print(f"   标准差效果: 1倍={width_narrow:.2f}%, 3倍={width_wide:.2f}% ({'✅ 正确' if std_dev_check else '❌ 错误'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_bbwidth_different_periods():
    print("🧪 测试BB_WIDTH不同周期参数...")

    # 创建具有不同波动模式的测试数据
    np.random.seed(123)
    n_days = 60
    base_price = 50

    # 生成波动率变化的价格序列
    prices = [base_price]
    for i in range(n_days):
        # 创建周期性波动率变化
        vol_cycle = 0.01 + 0.005 * np.sin(i * 2 * np.pi / 20)  # 20天周期的波动率变化
        daily_return = np.random.normal(0, vol_cycle)
        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    periods_to_test = [10, 20, 30, 40]
    results = {}

    for period in periods_to_test:
        factor = BB_WIDTH({"period": period, "std_dev": 2})
        result = factor.calculate_vectorized(test_data)
        results[period] = result

        width_col = f'BB_WIDTH_{period}'
        width_values = result[width_col].dropna()

        if len(width_values) > 0:
            avg_width = width_values.mean()
            latest_width = width_values.iloc[-1]
            print(f"   BB_WIDTH_{period}: 平均={avg_width:.2f}%, 最新={latest_width:.2f}%")

    # 验证因子信息
    factor_info = BB_WIDTH({"period": 20, "std_dev": 2}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   计算公式: {factor_info['formula']}")

    return results


def test_bbwidth_volatility_analysis():
    print("🧪 测试BB_WIDTH波动率分析...")

    # 创建包含不同波动率阶段的测试数据
    phases = {
        '低波动': (0.005, 20),  # (日波动率, 天数)
        '中波动': (0.015, 20),
        '高波动': (0.03, 20),
        '超高波动': (0.05, 10)
    }

    all_prices = [100]  # 起始价格
    phase_boundaries = [0]  # 阶段边界

    for phase_name, (vol, days) in phases.items():
        for _ in range(days):
            daily_return = np.random.normal(0, vol)
            all_prices.append(all_prices[-1] * (1 + daily_return))
        phase_boundaries.append(len(all_prices) - 1)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * len(all_prices),
        'trade_date': pd.date_range('2025-01-01', periods=len(all_prices)),
        'hfq_close': all_prices
    })

    factor = BB_WIDTH({"period": 20, "std_dev": 2})
    result = factor.calculate_vectorized(test_data)

    # 分析不同阶段的布林带宽度
    print("   各波动阶段的布林带宽度:")
    phase_names = list(phases.keys())

    for i, (phase_name, (expected_vol, days)) in enumerate(phases.items()):
        start_idx = max(phase_boundaries[i], 19)  # 确保有足够数据计算20日宽度
        end_idx = phase_boundaries[i + 1]

        if end_idx > start_idx:
            phase_widths = result['BB_WIDTH_20'].iloc[start_idx:end_idx].dropna()
            if len(phase_widths) > 0:
                avg_width = phase_widths.mean()
                max_width = phase_widths.max()
                print(f"     {phase_name}: 平均宽度={avg_width:.2f}%, 最大宽度={max_width:.2f}%")

    # 验证宽度与波动率的正相关性
    widths = result['BB_WIDTH_20'].dropna()
    if len(widths) >= 30:
        # 计算宽度的时间序列变化
        width_changes = widths.diff().abs()
        avg_width_change = width_changes.mean()
        print(f"   平均宽度变化: {avg_width_change:.3f}%")

        # 寻找宽度峰值（可能对应高波动期）
        width_peaks = widths[widths > widths.quantile(0.8)]
        print(f"   高宽度期(>80%分位): {len(width_peaks)}次, 平均宽度={width_peaks.mean():.2f}%")

    return result


def run_all_tests():
    print("📊 布林带宽度因子模块化测试")
    print("=" * 50)

    try:
        test_bbwidth_basic()
        print()
        test_bbwidth_validation()
        print()
        test_bbwidth_edge_cases()
        print()
        test_bbwidth_different_periods()
        print()
        test_bbwidth_volatility_analysis()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()