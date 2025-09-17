"""
WMA测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import WMA
from validation import WmaValidation


def test_wma_basic():
    print("🧪 测试WMA基础功能...")

    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 6,
        'trade_date': pd.date_range('2025-01-01', periods=6),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    })

    factor = WMA({"periods": [3, 5]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   WMA_3样例: {result['WMA_3'].iloc[:3].tolist()}")
    print(f"   WMA_5样例: {result['WMA_5'].iloc[:3].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最后一个数据点的WMA_3
    # 价格序列: [4.0, 5.0, 6.0], 权重: [1, 2, 3]
    # WMA = (4*1 + 5*2 + 6*3) / (1+2+3) = (4+10+18) / 6 = 32/6 ≈ 5.333
    recent_prices = test_data['hfq_close'].tail(3).tolist()  # [4.0, 5.0, 6.0]
    weights = [1, 2, 3]
    manual_wma3 = sum(p * w for p, w in zip(recent_prices, weights)) / sum(weights)
    calculated_wma3 = result['WMA_3'].iloc[-1]

    print(f"   手工验证WMA_3: {manual_wma3:.6f}")
    print(f"   因子结果WMA_3: {calculated_wma3:.6f}")
    print(f"   差异: {abs(calculated_wma3 - manual_wma3):.8f}")

    return result


def test_wma_validation():
    print("🧪 测试WMA验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': np.random.uniform(9.8, 10.5, 15)
    })

    factor = WMA({"periods": [5, 10]})
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = WmaValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_wma_edge_cases():
    print("🧪 测试WMA边界情况...")

    # 测试恒定价格
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 8,
        'trade_date': pd.date_range('2025-01-01', periods=8),
        'hfq_close': [10.0] * 8  # 恒定价格
    })

    factor = WMA({"periods": [3, 5]})
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格WMA_3: {result_constant['WMA_3'].iloc[-1]:.1f}")
    print(f"   恒定价格WMA_5: {result_constant['WMA_5'].iloc[-1]:.1f}")

    # 恒定价格的WMA应该等于价格本身
    constant_check = (result_constant['WMA_3'].iloc[-1] == 10.0 and
                     result_constant['WMA_5'].iloc[-1] == 10.0)
    print(f"   恒定价格检查: {'✅ 正确' if constant_check else '❌ 错误'}")

    # 测试线性趋势数据
    trend_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [10.0 + i * 0.5 for i in range(10)]  # 线性上升趋势
    })

    try:
        result_trend = factor.calculate_vectorized(trend_data)

        # 在线性上升趋势中，WMA应该比SMA更接近最新价格
        recent_prices = trend_data['hfq_close'].tail(5)
        sma_5 = recent_prices.mean()
        wma_5_last = result_trend['WMA_5'].iloc[-1]
        current_price = trend_data['hfq_close'].iloc[-1]

        # WMA应该比SMA更接近当前价格
        wma_distance = abs(wma_5_last - current_price)
        sma_distance = abs(sma_5 - current_price)

        print(f"   上升趋势当前价格: {current_price:.2f}")
        print(f"   上升趋势WMA_5: {wma_5_last:.3f}")
        print(f"   上升趋势SMA_5: {sma_5:.3f}")
        print(f"   敏感性检查: {'✅ 正确' if wma_distance <= sma_distance else '❌ 错误'} (WMA更接近当前价格)")

        # 测试权重效果
        # WMA_3 对于序列 [a, b, c] = (a*1 + b*2 + c*3) / 6
        simple_test = pd.DataFrame({
            'ts_code': ['510580.SH'] * 3,
            'trade_date': pd.date_range('2025-01-01', periods=3),
            'hfq_close': [1.0, 2.0, 3.0]
        })

        result_simple = factor.calculate_vectorized(simple_test)
        wma3_result = result_simple['WMA_3'].iloc[-1]
        expected_wma3 = (1*1 + 2*2 + 3*3) / (1+2+3)  # = 14/6 = 2.333...

        weight_check = abs(wma3_result - expected_wma3) < 0.0001
        print(f"   权重计算WMA_3: {wma3_result:.6f}")
        print(f"   期望值: {expected_wma3:.6f}")
        print(f"   权重效果检查: {'✅ 正确' if weight_check else '❌ 错误'}")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 WMA因子模块化测试")
    print("=" * 50)

    try:
        test_wma_basic()
        print()
        test_wma_validation()
        print()
        test_wma_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()