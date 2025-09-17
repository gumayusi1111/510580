"""
CCI测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import CCI
from validation import CciValidation


def test_cci_basic():
    print("🧪 测试CCI基础功能...")

    # 创建测试数据（模拟价格波动）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_high': [10.5, 10.8, 10.2, 11.0, 10.1, 10.6, 11.2, 10.4, 10.9, 11.5,
                     10.7, 11.3, 10.8, 10.5, 11.0, 10.3, 10.7, 11.1, 10.6, 10.9],
        'hfq_low': [10.0, 10.3, 9.8, 10.5, 9.6, 10.1, 10.7, 10.0, 10.4, 11.0,
                    10.2, 10.8, 10.3, 10.0, 10.5, 9.8, 10.2, 10.6, 10.1, 10.4],
        'hfq_close': [10.3, 10.6, 10.0, 10.8, 9.8, 10.4, 11.0, 10.2, 10.7, 11.2,
                      10.5, 11.1, 10.6, 10.3, 10.8, 10.1, 10.5, 10.9, 10.4, 10.7]
    })

    factor = CCI({"period": 14})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   CCI_14样例: {result['CCI_14'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    recent_data = test_data.tail(14)
    manual_tp = (recent_data['hfq_high'] + recent_data['hfq_low'] + recent_data['hfq_close']) / 3
    manual_ma = manual_tp.mean()
    manual_md = np.abs(manual_tp - manual_ma).mean()
    current_tp = manual_tp.iloc[-1]
    manual_cci = (current_tp - manual_ma) / (0.015 * manual_md)

    print(f"   手工验证CCI: {manual_cci:.4f}")
    print(f"   因子结果CCI: {result['CCI_14'].iloc[-1]:.4f}")
    print(f"   差异: {abs(result['CCI_14'].iloc[-1] - manual_cci):.6f}")

    # CCI信号解释
    latest_cci = result['CCI_14'].iloc[-1]
    print(f"   CCI信号解释:")
    print(f"     CCI值: {latest_cci:.2f}")

    if latest_cci > 100:
        print("     信号: 超买状态，价格可能回调")
    elif latest_cci < -100:
        print("     信号: 超卖状态，价格可能反弹")
    else:
        print("     信号: 正常震荡区间")

    return result


def test_cci_validation():
    print("🧪 测试CCI验证功能...")

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 18,
        'trade_date': pd.date_range('2025-01-01', periods=18),
        'hfq_high': np.random.uniform(10.5, 11.5, 18),
        'hfq_low': np.random.uniform(9.5, 10.5, 18),
        'hfq_close': np.random.uniform(10.0, 11.0, 18)
    })

    factor = CCI()
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = CciValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_cci_edge_cases():
    print("🧪 测试CCI边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': [10.0] * 15,
        'hfq_low': [10.0] * 15,
        'hfq_close': [10.0] * 15
    })

    factor = CCI()
    result_constant = factor.calculate_vectorized(constant_data)

    print(f"   恒定价格CCI: {result_constant['CCI_14'].iloc[-1]:.1f}")

    # 测试强烈趋势（超买超卖）
    trend_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 16,
        'trade_date': pd.date_range('2025-01-01', periods=16),
        # 模拟强劲上升趋势
        'hfq_high': [10 + i * 0.5 for i in range(16)],
        'hfq_low': [9.5 + i * 0.5 for i in range(16)],
        'hfq_close': [9.8 + i * 0.5 for i in range(16)]
    })

    try:
        result_trend = factor.calculate_vectorized(trend_data)
        cci_values = result_trend['CCI_14']

        print(f"   趋势CCI范围: [{cci_values.min():.1f}, {cci_values.max():.1f}]")

        # 检查超买超卖信号
        overbought = (cci_values > 100).sum()
        oversold = (cci_values < -100).sum()
        normal = len(cci_values) - overbought - oversold

        print(f"   信号分布: 超买{overbought}个, 超卖{oversold}个, 正常{normal}个")
        print(f"   异常值检查: {'✅ 正常' if cci_values.max() <= 1000 and cci_values.min() >= -1000 else '❌ 异常'}")

    except Exception as e:
        print(f"   趋势测试失败: {e}")

    return result_constant


def run_all_tests():
    print("📊 CCI因子模块化测试")
    print("=" * 50)

    try:
        test_cci_basic()
        print()
        test_cci_validation()
        print()
        test_cci_edge_cases()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()