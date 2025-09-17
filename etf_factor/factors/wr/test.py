"""
WR测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import WR
from validation import WrValidation


def test_wr_basic():
    print("🧪 测试WR基础功能...")

    # 创建测试数据（模拟价格波动）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 18,
        'trade_date': pd.date_range('2025-01-01', periods=18),
        'hfq_high': [10.5, 10.8, 10.2, 11.0, 10.1, 10.6, 11.2, 10.4, 10.9, 11.5,
                     10.7, 11.3, 10.8, 10.5, 11.0, 10.3, 10.7, 11.1],
        'hfq_low': [10.0, 10.3, 9.8, 10.5, 9.6, 10.1, 10.7, 10.0, 10.4, 11.0,
                    10.2, 10.8, 10.3, 10.0, 10.5, 9.8, 10.2, 10.6],
        'hfq_close': [10.3, 10.6, 10.0, 10.8, 9.8, 10.4, 11.0, 10.2, 10.7, 11.2,
                      10.5, 11.1, 10.6, 10.3, 10.8, 10.1, 10.5, 10.9]
    })

    factor = WR({"period": 14})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   WR_14样例: {result['WR_14'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_data = test_data.tail(14)
    manual_high = recent_data['hfq_high'].max()
    manual_low = recent_data['hfq_low'].min()
    current_close = recent_data['hfq_close'].iloc[-1]
    manual_wr = ((manual_high - current_close) / (manual_high - manual_low)) * (-100)

    print(f"   手工验证WR: {manual_wr:.4f}")
    print(f"   因子结果WR: {result['WR_14'].iloc[-1]:.4f}")
    print(f"   差异: {abs(result['WR_14'].iloc[-1] - manual_wr):.6f}")

    # WR信号解释
    latest_wr = result['WR_14'].iloc[-1]
    print(f"   WR信号解释:")
    print(f"     WR值: {latest_wr:.2f}")

    if latest_wr > -20:
        strength = "强烈超买" if latest_wr > -10 else "超买"
        print(f"     信号: 超买状态，价格可能回调 ({strength})")
    elif latest_wr < -80:
        strength = "强烈超卖" if latest_wr < -90 else "超卖"
        print(f"     信号: 超卖状态，价格可能反弹 ({strength})")
    else:
        print("     信号: 正常震荡区间")

    # 显示趋势
    recent_wr = result['WR_14'].iloc[-3:].tolist()
    if len(recent_wr) >= 2:
        if recent_wr[-1] > recent_wr[-2]:
            print("     趋势: WR上升（超卖程度减轻）")
        else:
            print("     趋势: WR下降（超卖程度加重）")

    return result


def test_wr_validation():
    print("🧪 测试WR验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 16,
        'trade_date': pd.date_range('2025-01-01', periods=16),
        'hfq_high': np.random.uniform(10.5, 11.5, 16),
        'hfq_low': np.random.uniform(9.5, 10.5, 16),
        'hfq_close': np.random.uniform(10.0, 11.0, 16)
    })

    factor = WR()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = WrValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_wr_edge_cases():
    print("🧪 测试WR边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': [10.0] * 15,
        'hfq_low': [10.0] * 15,
        'hfq_close': [10.0] * 15
    })

    factor = WR()
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格WR: {result_constant['WR_14'].iloc[-1]:.1f}")

    # 测试超买超卖情况
    overbought_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': [11.0] * 15,  # 恒定高价
        'hfq_low': [10.0] * 15,   # 恒定低价
        'hfq_close': [10.9] * 15  # 接近高价，应该超买
    })

    try:
        result_overbought = factor.calculate_vectorized(overbought_data)
        wr_overbought = result_overbought['WR_14'].iloc[-1]
        print(f"   超买情况WR: {wr_overbought:.1f} ({'✅超买' if wr_overbought > -20 else '❌正常'})")

        # 测试超卖情况
        oversold_data = pd.DataFrame({
            'ts_code': ['510580.SH'] * 15,
            'trade_date': pd.date_range('2025-01-01', periods=15),
            'hfq_high': [11.0] * 15,  # 恒定高价
            'hfq_low': [10.0] * 15,   # 恒定低价
            'hfq_close': [10.1] * 15  # 接近低价，应该超卖
        })

        result_oversold = factor.calculate_vectorized(oversold_data)
        wr_oversold = result_oversold['WR_14'].iloc[-1]
        print(f"   超卖情况WR: {wr_oversold:.1f} ({'✅超卖' if wr_oversold < -80 else '❌正常'})")

        # 检查范围
        all_values = [wr_overbought, wr_oversold, result_constant['WR_14'].iloc[-1]]
        range_check = all(val >= -100 and val <= 0 for val in all_values)
        print(f"   范围检查: {'✅ 正常' if range_check else '❌ 异常'}")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 威廉指标因子模块化测试")
    print("=" * 50)

    try:
        test_wr_basic()
        print()
        test_wr_validation()
        print()
        test_wr_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()