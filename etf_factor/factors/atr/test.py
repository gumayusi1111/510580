"""
ATR测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import ATR
from validation import AtrValidation


def test_atr_basic():
    print("🧪 测试ATR基础功能...")

    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_high':  [10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.2, 11.0, 11.3,
                      11.1, 11.4, 11.2, 11.5, 11.3, 11.6, 11.4, 11.7, 11.5, 11.8],
        'hfq_low':   [10.0, 10.2, 10.1, 10.3, 10.1, 10.4, 10.2, 10.5, 10.3, 10.6,
                      10.4, 10.7, 10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.1],
        'hfq_close': [10.2, 10.5, 10.3, 10.6, 10.4, 10.7, 10.5, 10.8, 10.6, 10.9,
                      10.7, 11.0, 10.8, 11.1, 10.9, 11.2, 11.0, 11.3, 11.1, 11.4]
    })

    factor = ATR({"periods": [14]})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   ATR_14样例: {result['ATR_14'].iloc[:5].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证第二个数据点的TR计算
    high = test_data['hfq_high'].iloc[1]  # 10.8
    low = test_data['hfq_low'].iloc[1]    # 10.2
    close = test_data['hfq_close'].iloc[1]  # 10.5
    prev_close = test_data['hfq_close'].iloc[0]  # 10.2

    hl = high - low  # 0.6
    hc = abs(high - prev_close)  # 0.6
    lc = abs(low - prev_close)   # 0.0
    manual_tr = max(hl, hc, lc)  # 0.6

    print(f"   手工验证TR: {manual_tr}")
    print(f"   ATR应>0且合理: {'✅' if result['ATR_14'].iloc[1] > 0 else '❌'}")

    return result


def test_atr_validation():
    print("🧪 测试ATR验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': np.random.uniform(10.5, 11.5, 15),
        'hfq_low': np.random.uniform(9.5, 10.5, 15),
        'hfq_close': np.random.uniform(10.0, 11.0, 15)
    })

    factor = ATR({"periods": [14, 20]})
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = AtrValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_atr_edge_cases():
    print("🧪 测试ATR边界情况...")

    # 测试极小波动
    low_volatility_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high': [10.01, 10.02, 10.01, 10.02, 10.01, 10.02, 10.01, 10.02, 10.01, 10.02],
        'hfq_low': [10.00, 10.01, 10.00, 10.01, 10.00, 10.01, 10.00, 10.01, 10.00, 10.01],
        'hfq_close': [10.005, 10.015, 10.005, 10.015, 10.005, 10.015, 10.005, 10.015, 10.005, 10.015]
    })

    factor = ATR()
    result_low_vol = factor.calculate_vectorized(low_volatility_data)

    print(f"   低波动ATR: {result_low_vol['ATR_14'].iloc[-1]:.4f}")

    # 测试高波动
    high_volatility_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high': [10, 12, 8, 15, 5, 18, 3, 20, 2, 25],
        'hfq_low': [8, 9, 6, 10, 3, 12, 1, 15, 0.5, 18],
        'hfq_close': [9, 11, 7, 12, 4, 15, 2, 18, 1, 20]
    })

    try:
        result_high_vol = factor.calculate_vectorized(high_volatility_data)
        max_atr = result_high_vol['ATR_14'].max()
        print(f"   高波动ATR最大值: {max_atr:.2f}")
        print(f"   合理性检查: {'✅ 正常' if max_atr < 100 else '❌ 异常'}")
    except Exception as e:
        print(f"   高波动测试失败: {e}")

    return result_low_vol


def run_all_tests():
    print("📊 ATR因子模块化测试")
    print("=" * 50)

    try:
        test_atr_basic()
        print()
        test_atr_validation()
        print()
        test_atr_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()