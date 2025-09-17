"""
OBV测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import OBV
from validation import ObvValidation


def test_obv_basic():
    print("🧪 测试OBV基础功能...")

    # 创建测试数据（模拟价格和成交量变化）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [10.0, 10.1, 10.0, 10.2, 9.9, 10.1, 10.3, 10.2, 10.4, 10.1,
                      10.5, 10.3, 10.6, 10.4, 10.7],
        'vol': [1000, 1200, 800, 1500, 900, 1100, 1300, 700, 1600, 1000,
                1400, 900, 1800, 1200, 2000]
    })

    factor = OBV()
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   OBV样例: {result['OBV'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证前几个数据点
    manual_obv = [0]  # 第一个点OBV为0
    for i in range(1, min(5, len(test_data))):
        price_change = test_data['hfq_close'].iloc[i] - test_data['hfq_close'].iloc[i-1]
        if price_change > 0:
            direction = 1
        elif price_change < 0:
            direction = -1
        else:
            direction = 0
        manual_obv.append(manual_obv[-1] + direction * test_data['vol'].iloc[i])

    print(f"   手工验证OBV前5个: {manual_obv}")
    print(f"   因子结果OBV前5个: {result['OBV'].iloc[:5].tolist()}")

    # OBV信号解释
    latest_obv = result['OBV'].iloc[-1]
    previous_obv = result['OBV'].iloc[-2]
    print(f"   OBV信号解释:")
    print(f"     最新OBV: {latest_obv:.0f}")
    print(f"     前一OBV: {previous_obv:.0f}")

    if latest_obv > previous_obv:
        print("     信号: 资金流入，买盘力量较强")
    elif latest_obv < previous_obv:
        print("     信号: 资金流出，卖盘力量较强")
    else:
        print("     信号: 资金平衡，多空力量相当")

    return result


def test_obv_validation():
    print("🧪 测试OBV验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 12,
        'trade_date': pd.date_range('2025-01-01', periods=12),
        'hfq_close': np.random.uniform(9.8, 10.5, 12),
        'vol': np.random.uniform(500, 2000, 12)
    })

    factor = OBV()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = ObvValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_obv_edge_cases():
    print("🧪 测试OBV边界情况...")

    # 测试恒定价格（所有价格变化为0）
    constant_price_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [10.0] * 10,  # 恒定价格
        'vol': [1000, 1200, 800, 1500, 900, 1100, 1300, 700, 1600, 1000]
    })

    factor = OBV()
    result_constant = factor.calculate_vectorized(constant_price_data)

    # 恒定价格下，除了第一个点，OBV应该保持不变
    obv_constant = result_constant['OBV'].iloc[1:].tolist()
    all_same = all(x == obv_constant[0] for x in obv_constant[1:])
    print(f"   恒定价格OBV: {obv_constant[:3]}... ({'✅ 恒定' if all_same else '❌ 变化'})")

    # 测试强烈上升趋势
    uptrend_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [10.0 + i * 0.1 for i in range(10)],  # 持续上涨
        'vol': [1000 + i * 100 for i in range(10)]  # 成交量递增
    })

    try:
        result_uptrend = factor.calculate_vectorized(uptrend_data)
        obv_uptrend = result_uptrend['OBV'].tolist()

        # 上升趋势下，OBV应该总体上升
        obv_trend = obv_uptrend[-1] - obv_uptrend[1]  # 跳过第一个0值
        print(f"   上升趋势OBV变化: {obv_trend:.0f} ({'✅ 上升' if obv_trend > 0 else '❌ 下降'})")

        # 测试下降趋势
        downtrend_data = pd.DataFrame({
            'ts_code': ['510580.SH'] * 10,
            'trade_date': pd.date_range('2025-01-01', periods=10),
            'hfq_close': [11.0 - i * 0.1 for i in range(10)],  # 持续下跌
            'vol': [1000 + i * 100 for i in range(10)]  # 成交量递增
        })

        result_downtrend = factor.calculate_vectorized(downtrend_data)
        obv_downtrend = result_downtrend['OBV'].tolist()

        # 下降趋势下，OBV应该总体下降
        obv_down_trend = obv_downtrend[-1] - obv_downtrend[1]  # 跳过第一个0值
        print(f"   下降趋势OBV变化: {obv_down_trend:.0f} ({'✅ 下降' if obv_down_trend < 0 else '❌ 上升'})")

        # 测试零成交量
        zero_volume_data = pd.DataFrame({
            'ts_code': ['510580.SH'] * 5,
            'trade_date': pd.date_range('2025-01-01', periods=5),
            'hfq_close': [10.0, 10.1, 10.2, 10.1, 10.3],
            'vol': [0, 0, 0, 0, 0]  # 零成交量
        })

        result_zero_vol = factor.calculate_vectorized(zero_volume_data)
        obv_zero_vol = result_zero_vol['OBV'].tolist()

        # 零成交量下，OBV应该保持为0
        all_zero = all(x == 0 for x in obv_zero_vol)
        print(f"   零成交量OBV: {obv_zero_vol} ({'✅ 全零' if all_zero else '❌ 非零'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 OBV因子模块化测试")
    print("=" * 50)

    try:
        test_obv_basic()
        print()
        test_obv_validation()
        print()
        test_obv_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()