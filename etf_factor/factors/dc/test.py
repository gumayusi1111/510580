"""
DC测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import DC
from validation import DcValidation


def test_dc_basic():
    print("🧪 测试DC基础功能...")

    # 创建测试数据（包含一定波动性）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_high': [10.0 + 0.15 * i + 0.08 * (i % 4) for i in range(25)],
        'hfq_low': [9.5 + 0.12 * i + 0.05 * (i % 3) for i in range(25)]
    })

    factor = DC({"period": 20})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   DC样例: UPPER={result['DC_UPPER_20'].iloc[20]:.3f}, "
          f"LOWER={result['DC_LOWER_20'].iloc[20]:.3f}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_high = test_data['hfq_high'].tail(20)
    recent_low = test_data['hfq_low'].tail(20)
    manual_upper = recent_high.max()
    manual_lower = recent_low.min()

    print(f"   手工验证: UPPER={manual_upper:.6f}, LOWER={manual_lower:.6f}")
    print(f"   因子结果: UPPER={result['DC_UPPER_20'].iloc[-1]:.6f}, "
          f"LOWER={result['DC_LOWER_20'].iloc[-1]:.6f}")

    # 检查唐奇安通道关系
    latest_upper = result['DC_UPPER_20'].iloc[-1]
    latest_lower = result['DC_LOWER_20'].iloc[-1]

    relationship_ok = latest_upper >= latest_lower
    print(f"   通道关系检查: {'✅ 正确' if relationship_ok else '❌ 错误'} (上轨>=下轨)")

    return result


def test_dc_validation():
    print("🧪 测试DC验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(42)  # 固定随机种子以确保可重复性
    price_base = 10
    price_changes = np.random.normal(0, 0.03, 50)
    prices = price_base + np.cumsum(price_changes)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 50,
        'trade_date': pd.date_range('2025-01-01', periods=50),
        'hfq_high': prices + np.abs(np.random.normal(0, 0.02, 50)),  # 高价略高
        'hfq_low': prices - np.abs(np.random.normal(0, 0.02, 50))    # 低价略低
    })

    factor = DC()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = DcValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_dc_edge_cases():
    print("🧪 测试DC边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 22,
        'trade_date': pd.date_range('2025-01-01', periods=22),
        'hfq_high': [10.0] * 22,  # 恒定价格
        'hfq_low': [10.0] * 22    # 恒定价格
    })

    factor = DC()
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格DC: UPPER={result_constant['DC_UPPER_20'].iloc[-1]:.3f}, "
          f"LOWER={result_constant['DC_LOWER_20'].iloc[-1]:.3f}")

    # 恒定价格时，上下轨应该相等
    constant_check = (result_constant['DC_UPPER_20'].iloc[-1] ==
                      result_constant['DC_LOWER_20'].iloc[-1] == 10.0)
    print(f"   恒定价格检查: {'✅ 正确' if constant_check else '❌ 错误'} (上下轨相等)")

    # 测试高波动数据
    high_vol_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_high': [10, 12, 8, 15, 5, 18, 3, 20, 2, 25, 1, 30, 0.5, 35, 1.5,
                     40, 2.5, 45, 50, 55, 60, 65, 70, 75, 80],  # 极端波动
        'hfq_low': [9, 11, 7, 14, 4, 17, 2, 19, 1, 24, 0.5, 29, 0.3, 34, 1.2,
                    39, 2.2, 44, 49, 54, 59, 64, 69, 74, 79]   # 对应低价
    })

    try:
        result_high_vol = factor.calculate_vectorized(high_vol_data)

        # 检查通道宽度
        latest_upper = result_high_vol['DC_UPPER_20'].iloc[-1]
        latest_lower = result_high_vol['DC_LOWER_20'].iloc[-1]
        channel_width = (latest_upper - latest_lower) / latest_upper * 100

        print(f"   高波动通道宽度: {channel_width:.1f}% ({'✅ 正常' if channel_width > 5 else '❌ 异常'})")

        # 测试不同周期参数
        factor_short = DC({"period": 5})
        result_short = factor_short.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 25,
            'trade_date': pd.date_range('2025-01-01', periods=25),
            'hfq_high': [10.0 + 0.1 * i for i in range(25)],
            'hfq_low': [9.8 + 0.1 * i for i in range(25)]
        }))

        factor_long = DC({"period": 10})
        result_long = factor_long.calculate_vectorized(test_data)

        # 短周期通道应该更紧贴价格变化
        width_short = (result_short['DC_UPPER_5'].iloc[-1] - result_short['DC_LOWER_5'].iloc[-1])
        width_long = (result_long['DC_UPPER_10'].iloc[-1] - result_long['DC_LOWER_10'].iloc[-1])

        # 在趋势数据中，长周期通道通常比短周期通道宽
        width_check = width_long >= width_short
        print(f"   周期效果: 5日={width_short:.3f}, 10日={width_long:.3f} ({'✅ 符合预期' if width_check else '⚠️ 特殊情况'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_dc_different_periods():
    print("🧪 测试DC不同周期参数...")

    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_high': [10 + 0.1 * i + 0.05 * np.sin(i * 0.5) for i in range(30)],
        'hfq_low': [9.5 + 0.1 * i + 0.03 * np.cos(i * 0.3) for i in range(30)]
    })

    periods_to_test = [5, 10, 20, 15]
    results = {}

    for period in periods_to_test:
        factor = DC({"period": period})
        result = factor.calculate_vectorized(test_data)
        results[period] = result

        upper_col = f'DC_UPPER_{period}'
        lower_col = f'DC_LOWER_{period}'

        channel_width = (result[upper_col].iloc[-1] - result[lower_col].iloc[-1])
        print(f"   周期{period}: 通道宽度={channel_width:.4f}")

    # 验证因子信息
    factor_info = DC({"period": 20}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")

    return results


def run_all_tests():
    print("📊 唐奇安通道因子模块化测试")
    print("=" * 50)

    try:
        test_dc_basic()
        print()
        test_dc_validation()
        print()
        test_dc_edge_cases()
        print()
        test_dc_different_periods()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()