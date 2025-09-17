"""
BOLL测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import BOLL
from validation import BollValidation


def test_boll_basic():
    print("🧪 测试BOLL基础功能...")

    # 创建测试数据（包含一定波动性）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10.0 + 0.1 * i + 0.05 * (i % 3) for i in range(25)]
    })

    factor = BOLL({"period": 20, "std_dev": 2})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   BOLL样例: UPPER={result['BOLL_UPPER'].iloc[20]:.3f}, "
          f"MID={result['BOLL_MID'].iloc[20]:.3f}, LOWER={result['BOLL_LOWER'].iloc[20]:.3f}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_data = test_data['hfq_close'].tail(20)
    manual_mid = recent_data.mean()
    manual_std = recent_data.std()
    manual_upper = manual_mid + 2 * manual_std
    manual_lower = manual_mid - 2 * manual_std

    print(f"   手工验证: UPPER={manual_upper:.6f}, MID={manual_mid:.6f}, LOWER={manual_lower:.6f}")
    print(f"   因子结果: UPPER={result['BOLL_UPPER'].iloc[-1]:.6f}, "
          f"MID={result['BOLL_MID'].iloc[-1]:.6f}, LOWER={result['BOLL_LOWER'].iloc[-1]:.6f}")

    # 检查布林带关系
    latest_upper = result['BOLL_UPPER'].iloc[-1]
    latest_mid = result['BOLL_MID'].iloc[-1]
    latest_lower = result['BOLL_LOWER'].iloc[-1]

    relationship_ok = latest_upper >= latest_mid >= latest_lower
    print(f"   带间关系检查: {'✅ 正确' if relationship_ok else '❌ 错误'} (上>=中>=下)")

    return result


def test_boll_validation():
    print("🧪 测试BOLL验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(42)  # 固定随机种子以确保可重复性
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 50,
        'trade_date': pd.date_range('2025-01-01', periods=50),
        'hfq_close': 10 + np.cumsum(np.random.normal(0, 0.02, 50))  # 随机游走价格
    })

    factor = BOLL()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = BollValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_boll_edge_cases():
    print("🧪 测试BOLL边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 22,
        'trade_date': pd.date_range('2025-01-01', periods=22),
        'hfq_close': [10.0] * 22  # 恒定价格
    })

    factor = BOLL()
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格BOLL: UPPER={result_constant['BOLL_UPPER'].iloc[-1]:.3f}, "
          f"MID={result_constant['BOLL_MID'].iloc[-1]:.3f}, LOWER={result_constant['BOLL_LOWER'].iloc[-1]:.3f}")

    # 恒定价格时，上中下轨应该相等
    constant_check = (result_constant['BOLL_UPPER'].iloc[-1] == result_constant['BOLL_MID'].iloc[-1] ==
                      result_constant['BOLL_LOWER'].iloc[-1] == 10.0)
    print(f"   恒定价格检查: {'✅ 正确' if constant_check else '❌ 错误'} (三轨相等)")

    # 测试高波动数据
    high_vol_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10, 12, 8, 15, 5, 18, 3, 20, 2, 25, 1, 30, 0.5, 35, 0.1,
                      40, 0.05, 45, 50, 55, 60, 65, 70, 75, 80]  # 极端波动
    })

    try:
        result_high_vol = factor.calculate_vectorized(high_vol_data)

        # 检查布林带宽度
        latest_upper = result_high_vol['BOLL_UPPER'].iloc[-1]
        latest_mid = result_high_vol['BOLL_MID'].iloc[-1]
        latest_lower = result_high_vol['BOLL_LOWER'].iloc[-1]
        band_width = (latest_upper - latest_lower) / latest_mid * 100

        print(f"   高波动带宽: {band_width:.1f}% ({'✅ 正常' if band_width > 5 else '❌ 异常'})")

        # 测试不同标准差参数
        factor_small_std = BOLL({"period": 20, "std_dev": 1})
        result_small_std = factor_small_std.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 25,
            'trade_date': pd.date_range('2025-01-01', periods=25),
            'hfq_close': [10.0 + 0.1 * i for i in range(25)]
        }))

        factor_large_std = BOLL({"period": 20, "std_dev": 3})
        result_large_std = factor_large_std.calculate_vectorized(test_data)

        # 标准差越大，布林带越宽
        width_small = (result_small_std['BOLL_UPPER'].iloc[-1] - result_small_std['BOLL_LOWER'].iloc[-1])
        width_large = (result_large_std['BOLL_UPPER'].iloc[-1] - result_large_std['BOLL_LOWER'].iloc[-1])

        width_check = width_large > width_small
        print(f"   标准差效果: 1倍={width_small:.3f}, 3倍={width_large:.3f} ({'✅ 正确' if width_check else '❌ 错误'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 布林带因子模块化测试")
    print("=" * 50)

    try:
        test_boll_basic()
        print()
        test_boll_validation()
        print()
        test_boll_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()