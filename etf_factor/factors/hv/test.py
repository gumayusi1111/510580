"""
HV测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import HV
from validation import HvValidation


def test_hv_basic():
    print("🧪 测试HV基础功能...")

    # 创建测试数据（包含价格趋势和波动）
    np.random.seed(42)
    price_base = 10
    returns = np.random.normal(0.001, 0.02, 50)  # 模拟日收益率
    prices = [price_base]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 51,
        'trade_date': pd.date_range('2025-01-01', periods=51),
        'hfq_close': prices
    })

    factor = HV({"periods": [20, 60]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 检查结果
    hv_20_values = result['HV_20'].dropna()
    hv_60_values = result['HV_60'].dropna()

    if len(hv_20_values) > 0:
        print(f"   HV_20样例: 最新={hv_20_values.iloc[-1]:.2f}%, 平均={hv_20_values.mean():.2f}%")
    if len(hv_60_values) > 0:
        print(f"   HV_60样例: 最新={hv_60_values.iloc[-1]:.2f}%, 平均={hv_60_values.mean():.2f}%")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    if len(test_data) >= 21:
        recent_returns = test_data['hfq_close'].pct_change().tail(20)
        manual_std = recent_returns.std()
        manual_hv_20 = manual_std * np.sqrt(252) if pd.notna(manual_std) else np.nan

        print(f"   手工验证HV_20: {manual_hv_20:.6f}%")
        print(f"   因子结果HV_20: {result['HV_20'].iloc[-1]:.6f}%")

    return result


def test_hv_validation():
    print("🧪 测试HV验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(123)
    n_days = 80
    price_base = 100
    returns = np.random.normal(0.0005, 0.015, n_days)  # 模拟日收益率
    prices = [price_base]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    factor = HV()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = HvValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_hv_edge_cases():
    print("🧪 测试HV边界情况...")

    # 测试恒定价格（零波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': [10.0] * 30  # 恒定价格
    })

    factor = HV()
    result_constant = factor.calculate_vectorized(constant_data)

    hv_20_constant = result_constant['HV_20'].dropna()
    hv_60_constant = result_constant['HV_60'].dropna()

    print(f"   恒定价格HV_20: {hv_20_constant.iloc[-1] if len(hv_20_constant) > 0 else 'NaN'}")
    print(f"   恒定价格HV_60: {hv_60_constant.iloc[-1] if len(hv_60_constant) > 0 else 'NaN'}")

    # 恒定价格时，波动率应该为0或接近0
    if len(hv_20_constant) > 0:
        zero_vol_check = abs(hv_20_constant.iloc[-1]) < 0.001
        print(f"   零波动检查: {'✅ 正确' if zero_vol_check else '❌ 错误'} (接近零)")

    # 测试高波动数据
    high_vol_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': [10 * (1.1 if i % 2 == 0 else 0.9) ** (i // 2) for i in range(30)]  # 交替大幅波动
    })

    try:
        result_high_vol = factor.calculate_vectorized(high_vol_data)

        hv_20_high = result_high_vol['HV_20'].dropna()
        if len(hv_20_high) > 0:
            high_vol_value = hv_20_high.iloc[-1]
            print(f"   高波动HV_20: {high_vol_value:.1f}% ({'✅ 合理' if 10 < high_vol_value < 500 else '⚠️ 极端'})")

        # 测试不同周期参数
        factor_single = HV({"periods": [10]})
        result_single = factor_single.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 25,
            'trade_date': pd.date_range('2025-01-01', periods=25),
            'hfq_close': [10 + 0.1 * np.sin(i * 0.5) for i in range(25)]  # 正弦波价格
        }))

        factor_multi = HV({"periods": [5, 10, 20]})
        result_multi = factor_multi.calculate_vectorized(test_data)

        # 多周期因子应该有更多输出列
        single_cols = [col for col in result_single.columns if col.startswith('HV_')]
        multi_cols = [col for col in result_multi.columns if col.startswith('HV_')]

        period_check = len(multi_cols) > len(single_cols)
        print(f"   多周期测试: 单周期={len(single_cols)}列, 多周期={len(multi_cols)}列 ({'✅ 正确' if period_check else '❌ 错误'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_hv_different_periods():
    print("🧪 测试HV不同周期参数...")

    # 创建具有不同波动模式的测试数据
    np.random.seed(456)
    n_days = 100
    base_price = 50

    # 生成具有变化波动率的价格序列
    prices = [base_price]
    for i in range(n_days):
        if i < 30:
            vol = 0.01  # 低波动期
        elif i < 60:
            vol = 0.03  # 中波动期
        else:
            vol = 0.02  # 中低波动期

        daily_return = np.random.normal(0, vol)
        prices.append(prices[-1] * (1 + daily_return))

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * (n_days + 1),
        'trade_date': pd.date_range('2025-01-01', periods=n_days + 1),
        'hfq_close': prices
    })

    periods_to_test = [5, 10, 20, 60]
    results = {}

    for periods in [[p] for p in periods_to_test]:
        factor = HV({"periods": periods})
        result = factor.calculate_vectorized(test_data)
        results[periods[0]] = result

        period = periods[0]
        hv_col = f'HV_{period}'
        hv_values = result[hv_col].dropna()

        if len(hv_values) > 0:
            avg_hv = hv_values.mean()
            latest_hv = hv_values.iloc[-1]
            print(f"   HV_{period}: 平均={avg_hv:.2f}%, 最新={latest_hv:.2f}%")

    # 验证因子信息
    factor_info = HV({"periods": [20, 60]}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   支持周期: {factor_info['periods']}")

    return results


def run_all_tests():
    print("📊 历史波动率因子模块化测试")
    print("=" * 50)

    try:
        test_hv_basic()
        print()
        test_hv_validation()
        print()
        test_hv_edge_cases()
        print()
        test_hv_different_periods()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()