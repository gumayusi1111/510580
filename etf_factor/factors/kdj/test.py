"""
KDJ测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import KDJ
from validation import KdjValidation


def test_kdj_basic():
    print("🧪 测试KDJ基础功能...")

    # 创建测试数据（模拟价格趋势变化）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': [10.5, 10.8, 10.2, 11.0, 10.1, 10.6, 11.2, 10.4, 10.9, 11.5,
                     10.7, 11.3, 10.8, 10.5, 11.0],
        'hfq_low': [10.0, 10.3, 9.8, 10.5, 9.6, 10.1, 10.7, 10.0, 10.4, 11.0,
                    10.2, 10.8, 10.3, 10.0, 10.5],
        'hfq_close': [10.3, 10.6, 10.0, 10.8, 9.8, 10.4, 11.0, 10.2, 10.7, 11.2,
                      10.5, 11.1, 10.6, 10.3, 10.8]
    })

    factor = KDJ({"period": 9})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   KDJ_K_9样例: {result['KDJ_K_9'].iloc[-3:].tolist()}")
    print(f"   KDJ_D_9样例: {result['KDJ_D_9'].iloc[-3:].tolist()}")
    print(f"   KDJ_J_9样例: {result['KDJ_J_9'].iloc[-3:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 验证J值关系：J = 3*K - 2*D
    latest_k = result['KDJ_K_9'].iloc[-1]
    latest_d = result['KDJ_D_9'].iloc[-1]
    latest_j = result['KDJ_J_9'].iloc[-1]
    calculated_j = 3 * latest_k - 2 * latest_d

    print(f"   J值关系验证: J={latest_j:.2f}, 3K-2D={calculated_j:.2f}")

    # 简单的信号解释
    print(f"   KDJ信号解释:")
    print(f"     K值: {latest_k:.2f}")
    print(f"     D值: {latest_d:.2f}")
    print(f"     J值: {latest_j:.2f}")

    if latest_k > latest_d:
        print("     信号: K>D，多头趋势")
    else:
        print("     信号: K<D，空头趋势")

    if latest_k > 80:
        print("     状态: 超买区域")
    elif latest_k < 20:
        print("     状态: 超卖区域")
    else:
        print("     状态: 正常区域")

    return result


def test_kdj_validation():
    print("🧪 测试KDJ验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(42)
    n_days = 30
    base_price = 100

    # 生成有趋势的价格数据
    prices_high = []
    prices_low = []
    prices_close = []

    for i in range(n_days):
        base = base_price + 0.1 * i  # 轻微上涨趋势
        volatility = 2 + 0.5 * np.sin(i * 0.2)  # 变化的波动率

        daily_high = base + abs(np.random.normal(0, volatility))
        daily_low = base - abs(np.random.normal(0, volatility))
        daily_close = base + np.random.normal(0, volatility * 0.5)

        # 确保价格逻辑正确
        daily_close = max(min(daily_close, daily_high), daily_low)

        prices_high.append(daily_high)
        prices_low.append(daily_low)
        prices_close.append(daily_close)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * n_days,
        'trade_date': pd.date_range('2025-01-01', periods=n_days),
        'hfq_high': prices_high,
        'hfq_low': prices_low,
        'hfq_close': prices_close
    })

    factor = KDJ()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = KdjValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_kdj_edge_cases():
    print("🧪 测试KDJ边界情况...")

    # 测试恒定价格（无波动）
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 12,
        'trade_date': pd.date_range('2025-01-01', periods=12),
        'hfq_high': [10.0] * 12,
        'hfq_low': [10.0] * 12,
        'hfq_close': [10.0] * 12
    })

    factor = KDJ()
    result_constant = factor.calculate_vectorized(constant_data)

    latest_k_const = result_constant['KDJ_K_9'].iloc[-1]
    latest_d_const = result_constant['KDJ_D_9'].iloc[-1]
    latest_j_const = result_constant['KDJ_J_9'].iloc[-1]

    print(f"   恒定价格KDJ: K={latest_k_const:.1f}, D={latest_d_const:.1f}, J={latest_j_const:.1f}")

    # 恒定价格时，RSV应该为50，最终K、D值也应该趋向50
    constant_check = abs(latest_k_const - 50) < 5 and abs(latest_d_const - 50) < 5
    print(f"   恒定价格检查: {'✅ 正确' if constant_check else '❌ 错误'} (K、D接近50)")

    # 测试极端波动数据
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_high': [10, 12, 8, 15, 5, 18, 3, 20, 2, 25, 1, 30, 35, 40, 45],
        'hfq_low': [9, 11, 7, 14, 4, 17, 2, 19, 1, 24, 0.5, 29, 34, 39, 44],
        'hfq_close': [9.5, 11.5, 7.5, 14.5, 4.5, 17.5, 2.5, 19.5, 1.5, 24.5, 0.75, 29.5, 34.5, 39.5, 44.5]
    })

    try:
        result_extreme = factor.calculate_vectorized(extreme_data)

        latest_k_ext = result_extreme['KDJ_K_9'].iloc[-1]
        latest_d_ext = result_extreme['KDJ_D_9'].iloc[-1]
        latest_j_ext = result_extreme['KDJ_J_9'].iloc[-1]

        print(f"   极端波动KDJ: K={latest_k_ext:.1f}, D={latest_d_ext:.1f}, J={latest_j_ext:.1f}")

        # 极端波动数据中，KDJ应该反应激烈的价格变化
        extreme_check = 0 <= latest_k_ext <= 100 and 0 <= latest_d_ext <= 100
        print(f"   极端波动检查: {'✅ 合理' if extreme_check else '⚠️ 异常'} (K、D在0-100范围)")

        # 测试不同周期参数
        factor_short = KDJ({"period": 5})
        result_short = factor_short.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 20,
            'trade_date': pd.date_range('2025-01-01', periods=20),
            'hfq_high': [10 + 0.5 * np.sin(i * 0.3) + 0.2 * i for i in range(20)],
            'hfq_low': [9.5 + 0.4 * np.sin(i * 0.3) + 0.2 * i for i in range(20)],
            'hfq_close': [9.75 + 0.45 * np.sin(i * 0.3) + 0.2 * i for i in range(20)]
        }))

        factor_long = KDJ({"period": 14})
        result_long = factor_long.calculate_vectorized(test_data)

        # 不同周期的KDJ应该有不同的敏感性
        k5 = result_short['KDJ_K_5'].iloc[-5:].std()
        k14 = result_long['KDJ_K_14'].iloc[-5:].std()

        period_check = k5 >= k14  # 短周期通常比长周期更敏感
        print(f"   周期敏感性: K5波动={k5:.2f}, K14波动={k14:.2f} ({'✅ 符合预期' if period_check else '⚠️ 特殊情况'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_kdj_different_periods():
    print("🧪 测试KDJ不同周期参数...")

    # 创建具有明确趋势的测试数据
    n_days = 25
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * n_days,
        'trade_date': pd.date_range('2025-01-01', periods=n_days),
        'hfq_high': [50 + 2 * i + np.sin(i * 0.5) for i in range(n_days)],
        'hfq_low': [49 + 2 * i + np.sin(i * 0.5) for i in range(n_days)],
        'hfq_close': [49.5 + 2 * i + np.sin(i * 0.5) for i in range(n_days)]
    })

    periods_to_test = [5, 9, 14, 20]
    results = {}

    for period in periods_to_test:
        factor = KDJ({"period": period})
        result = factor.calculate_vectorized(test_data)
        results[period] = result

        k_col = f'KDJ_K_{period}'
        d_col = f'KDJ_D_{period}'
        j_col = f'KDJ_J_{period}'

        # 计算最后5个数据点的平均值和波动性
        k_values = result[k_col].tail(5)
        d_values = result[d_col].tail(5)
        j_values = result[j_col].tail(5)

        k_avg = k_values.mean()
        k_vol = k_values.std()

        print(f"   KDJ_{period}: K平均={k_avg:.1f}, K波动={k_vol:.2f}")

    # 验证因子信息
    factor_info = KDJ({"period": 9}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   计算公式: {factor_info['formula']}")

    return results


def test_kdj_signal_analysis():
    print("🧪 测试KDJ信号分析...")

    # 创建包含买卖信号的测试数据
    # 先上涨然后下跌的价格模式
    prices = []
    base = 100
    for i in range(30):
        if i < 15:  # 前15天上涨
            price = base + 2 * i + np.random.normal(0, 0.5)
        else:  # 后15天下跌
            price = base + 30 - 1.5 * (i - 15) + np.random.normal(0, 0.5)
        prices.append(price)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_high': [p + abs(np.random.normal(0, 0.5)) for p in prices],
        'hfq_low': [p - abs(np.random.normal(0, 0.5)) for p in prices],
        'hfq_close': prices
    })

    factor = KDJ({"period": 9})
    result = factor.calculate_vectorized(test_data)

    # 分析KDJ信号
    k_values = result['KDJ_K_9']
    d_values = result['KDJ_D_9']
    j_values = result['KDJ_J_9']

    # 找到金叉和死叉点
    golden_crosses = []
    death_crosses = []

    for i in range(1, len(result)):
        if k_values.iloc[i] > d_values.iloc[i] and k_values.iloc[i-1] <= d_values.iloc[i-1]:
            golden_crosses.append(i)
        elif k_values.iloc[i] < d_values.iloc[i] and k_values.iloc[i-1] >= d_values.iloc[i-1]:
            death_crosses.append(i)

    print(f"   金叉点(K上穿D): {golden_crosses}")
    print(f"   死叉点(K下穿D): {death_crosses}")

    # 分析超买超卖区域
    overbought = (k_values > 80).sum()
    oversold = (k_values < 20).sum()

    print(f"   超买区域(K>80): {overbought}次")
    print(f"   超卖区域(K<20): {oversold}次")

    # 最新的KDJ状态
    latest_k = k_values.iloc[-1]
    latest_d = d_values.iloc[-1]
    latest_j = j_values.iloc[-1]

    print(f"   最新KDJ状态: K={latest_k:.1f}, D={latest_d:.1f}, J={latest_j:.1f}")

    return result


def run_all_tests():
    print("📊 KDJ随机指标因子模块化测试")
    print("=" * 50)

    try:
        test_kdj_basic()
        print()
        test_kdj_validation()
        print()
        test_kdj_edge_cases()
        print()
        test_kdj_different_periods()
        print()
        test_kdj_signal_analysis()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()