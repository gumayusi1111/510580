"""
SMA测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import SMA
from validation import SmaValidation


def test_sma_basic():
    print("🧪 测试SMA基础功能...")

    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })

    factor = SMA({"periods": [3, 5]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   SMA_3样例: {result['SMA_3'].iloc[-3:].tolist()}")
    print(f"   SMA_5样例: {result['SMA_5'].iloc[-3:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最后一个数据点的SMA_3
    manual_sma3 = test_data['hfq_close'].tail(3).mean()  # (8+9+10)/3 = 9.0
    calculated_sma3 = result['SMA_3'].iloc[-1]
    print(f"   手工验证SMA_3: {manual_sma3:.6f}")
    print(f"   因子结果SMA_3: {calculated_sma3:.6f}")
    print(f"   差异: {abs(calculated_sma3 - manual_sma3):.8f}")

    # 性能统计
    stats = factor.get_performance_stats(test_data, result)
    print(f"   数据完整性: {stats['data_completeness']}")

    return result


def test_sma_validation():
    print("🧪 测试SMA验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': np.random.uniform(9.8, 10.5, 15)
    })

    factor = SMA({"periods": [5, 10, 20]})
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = SmaValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_sma_edge_cases():
    print("🧪 测试SMA边界情况...")

    # 测试恒定价格
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [10.0] * 10  # 恒定价格
    })

    factor = SMA({"periods": [3, 5]})
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格SMA_3: {result_constant['SMA_3'].iloc[-1]:.1f}")
    print(f"   恒定价格SMA_5: {result_constant['SMA_5'].iloc[-1]:.1f}")

    # 恒定价格的SMA应该等于价格本身
    constant_check = (result_constant['SMA_3'].iloc[-1] == 10.0 and
                     result_constant['SMA_5'].iloc[-1] == 10.0)
    print(f"   恒定价格检查: {'✅ 正确' if constant_check else '❌ 错误'}")

    # 测试趋势数据
    trend_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 12,
        'trade_date': pd.date_range('2025-01-01', periods=12),
        'hfq_close': [10.0 + i * 0.1 for i in range(12)]  # 线性上升趋势
    })

    try:
        result_trend = factor.calculate_vectorized(trend_data)

        # 在上升趋势中，短期SMA应该高于长期SMA
        sma3_last = result_trend['SMA_3'].iloc[-1]
        sma5_last = result_trend['SMA_5'].iloc[-1]

        trend_check = sma3_last > sma5_last
        print(f"   上升趋势SMA_3: {sma3_last:.3f}")
        print(f"   上升趋势SMA_5: {sma5_last:.3f}")
        print(f"   趋势关系检查: {'✅ 正确' if trend_check else '❌ 错误'} (短期>长期)")

        # 测试波动性数据
        volatile_data = pd.DataFrame({
            'ts_code': ['510580.SH'] * 10,
            'trade_date': pd.date_range('2025-01-01', periods=10),
            'hfq_close': [10, 12, 8, 15, 7, 18, 5, 20, 3, 25]  # 高波动
        })

        result_volatile = factor.calculate_vectorized(volatile_data)

        # SMA应该比原始价格更平滑
        original_std = np.std(volatile_data['hfq_close'])
        sma3_std = np.std(result_volatile['SMA_3'].dropna())

        smoothness_check = sma3_std < original_std
        print(f"   原始价格标准差: {original_std:.3f}")
        print(f"   SMA_3标准差: {sma3_std:.3f}")
        print(f"   平滑性检查: {'✅ 正确' if smoothness_check else '❌ 错误'} (SMA更平滑)")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 SMA因子模块化测试")
    print("=" * 50)

    try:
        test_sma_basic()
        print()
        test_sma_validation()
        print()
        test_sma_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()