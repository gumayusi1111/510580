"""
STOCH测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import STOCH
from validation import StochValidation


def test_stoch_basic():
    print("🧪 测试STOCH基础功能...")

    # 创建测试数据（模拟价格波动）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_high': [10.2, 10.5, 10.1, 10.8, 9.9, 10.3, 10.6, 10.0, 10.4, 10.7,
                     10.2, 10.9, 10.3, 10.1, 10.5, 10.8, 11.0, 10.6, 10.9, 11.2],
        'hfq_low': [9.8, 10.1, 9.7, 10.3, 9.5, 9.9, 10.2, 9.6, 10.0, 10.3,
                    9.8, 10.5, 9.9, 9.7, 10.1, 10.4, 10.6, 10.2, 10.5, 10.8],
        'hfq_close': [10.0, 10.3, 9.9, 10.6, 9.7, 10.1, 10.4, 9.8, 10.2, 10.5,
                      10.0, 10.7, 10.1, 9.9, 10.3, 10.6, 10.8, 10.4, 10.7, 11.0]
    })

    factor = STOCH({"k_period": 9, "d_period": 3})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   STOCH_K_9样例: {result['STOCH_K_9'].iloc[-5:].tolist()}")
    print(f"   STOCH_D_3样例: {result['STOCH_D_3'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_data = test_data.tail(9)
    manual_high = recent_data['hfq_high'].max()
    manual_low = recent_data['hfq_low'].min()
    manual_close = recent_data['hfq_close'].iloc[-1]
    manual_k = ((manual_close - manual_low) / (manual_high - manual_low)) * 100

    print(f"   手工验证%K: {manual_k:.4f}")
    print(f"   因子结果%K: {result['STOCH_K_9'].iloc[-1]:.4f}")
    print(f"   差异: {abs(result['STOCH_K_9'].iloc[-1] - manual_k):.6f}")

    return result


def test_stoch_validation():
    print("🧪 测试STOCH验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': np.random.uniform(10.5, 11.5, 15),
        'hfq_low': np.random.uniform(9.5, 10.5, 15),
        'hfq_close': np.random.uniform(10.0, 11.0, 15)
    })

    factor = STOCH()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = StochValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_stoch_edge_cases():
    print("🧪 测试STOCH边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high': [10.0] * 10,
        'hfq_low': [10.0] * 10,
        'hfq_close': [10.0] * 10
    })

    factor = STOCH()
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格%K: {result_constant['STOCH_K_9'].iloc[-1]:.1f}")
    print(f"   恒定价格%D: {result_constant['STOCH_D_3'].iloc[-1]:.1f}")

    # 测试极端波动
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 12,
        'trade_date': pd.date_range('2025-01-01', periods=12),
        'hfq_high': [10, 15, 5, 20, 1, 25, 0.5, 30, 0.1, 35, 50, 100],
        'hfq_low': [8, 12, 3, 15, 0.5, 20, 0.1, 25, 0.05, 30, 45, 90],
        'hfq_close': [9, 14, 4, 18, 0.8, 23, 0.3, 28, 0.08, 33, 48, 95]
    })

    try:
        result_extreme = factor.calculate_vectorized(extreme_data)
        k_values = result_extreme['STOCH_K_9']
        d_values = result_extreme['STOCH_D_3']

        print(f"   极端波动%K范围: [{k_values.min():.1f}, {k_values.max():.1f}]")
        print(f"   极端波动%D范围: [{d_values.min():.1f}, {d_values.max():.1f}]")
        print(f"   范围检查: {'✅ 正常' if k_values.min() >= 0 and k_values.max() <= 100 else '❌ 异常'}")
    except Exception as e:
        print(f"   极端波动测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 随机震荡器因子模块化测试")
    print("=" * 50)

    try:
        test_stoch_basic()
        print()
        test_stoch_validation()
        print()
        test_stoch_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()