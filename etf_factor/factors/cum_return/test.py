"""
CUM_RETURN测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import CUM_RETURN


def create_test_data(length=25) -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    # 模拟价格序列：基础价格 + 趋势 + 随机波动
    base_price = 100
    trend = np.linspace(0, 0.2, length)  # 20%的总体上涨趋势
    noise = np.random.normal(0, 0.01, length)  # 1%的随机波动

    prices = []
    for i in range(length):
        price = base_price * (1 + trend[i] + noise[i])
        prices.append(max(price, 0.01))  # 确保价格为正

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_cum_return_basic():
    """基础功能测试"""
    print("🧪 测试CUM_RETURN基础功能...")

    # 创建简单测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0, 102.0, 104.04, 106.12, 108.24,  # 持续上涨
                     110.41, 112.62, 114.87, 117.17, 119.51]
    })

    # 创建因子实例
    factor = CUM_RETURN({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证最后一行的数据
    # 3日累计收益率: (117.17 - 114.87) / 114.87 * 100 ≈ 2.0%
    # 5日累计收益率: (117.17 - 108.24) / 108.24 * 100 ≈ 8.25%
    last_row = result.iloc[-2]  # 倒数第二行有完整数据
    print(f"   3日累计收益率样例: {last_row['CUM_RETURN_3']:.2f}%")
    print(f"   5日累计收益率样例: {last_row['CUM_RETURN_5']:.2f}%")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查前几行是否正确为NaN
    print(f"   前3行CUM_RETURN_3为NaN: {result['CUM_RETURN_3'].iloc[:3].isnull().all()}")
    print(f"   前5行CUM_RETURN_5为NaN: {result['CUM_RETURN_5'].iloc[:5].isnull().all()}")

    return result


def test_cum_return_edge_cases():
    """边界情况测试"""
    print("\n🧪 测试CUM_RETURN边界情况...")

    factor = CUM_RETURN({"periods": [5, 20]})

    # 测试1: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 102.0, 104.0]
    })

    result1 = factor.calculate_vectorized(short_data)
    all_null_20 = result1['CUM_RETURN_20'].isnull().all()
    print(f"   短数据测试(20日): {'✅ 全为NaN' if all_null_20 else '❌ 应为NaN'}")

    # 测试2: 价格无变化
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0] * 10
    })

    result2 = factor.calculate_vectorized(flat_data)
    non_null_5 = result2['CUM_RETURN_5'].dropna()
    all_zero = (non_null_5 == 0).all() if len(non_null_5) > 0 else True
    print(f"   平价格测试: {'✅ 收益率为0' if all_zero else '❌ 应为0'}")

    # 测试3: 极端价格变化
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 8,
        'trade_date': pd.date_range('2025-01-01', periods=8),
        'hfq_close': [100.0, 150.0, 200.0, 250.0, 300.0, 180.0, 120.0, 90.0]
    })

    result3 = factor.calculate_vectorized(extreme_data)
    extreme_returns = result3['CUM_RETURN_5'].dropna()
    if len(extreme_returns) > 0:
        print(f"   极端变化测试: 收益率范围 {extreme_returns.min():.1f}% 到 {extreme_returns.max():.1f}%")


def test_cum_return_different_periods():
    """不同周期参数测试"""
    print("\n🧪 测试CUM_RETURN不同周期...")

    # 测试多个周期
    test_data = create_test_data(30)

    # 测试单周期
    factor1 = CUM_RETURN({"periods": [10]})
    result1 = factor1.calculate_vectorized(test_data)
    print(f"   单周期测试: 输出列 {[col for col in result1.columns if 'CUM_RETURN' in col]}")

    # 测试多周期
    factor2 = CUM_RETURN({"periods": [5, 10, 20]})
    result2 = factor2.calculate_vectorized(test_data)
    expected_cols = ['CUM_RETURN_5', 'CUM_RETURN_10', 'CUM_RETURN_20']
    has_all_cols = all(col in result2.columns for col in expected_cols)
    print(f"   多周期测试: {'✅ 通过' if has_all_cols else '❌ 失败'}")

    # 测试默认参数
    factor3 = CUM_RETURN()
    result3 = factor3.calculate_vectorized(test_data)
    default_cols = ['CUM_RETURN_5', 'CUM_RETURN_20', 'CUM_RETURN_60']
    has_default_cols = all(col in result3.columns for col in default_cols)
    print(f"   默认参数测试: {'✅ 通过' if has_default_cols else '❌ 失败'}")


def test_cum_return_performance():
    """性能测试"""
    print("\n🧪 测试CUM_RETURN性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000)
    factor = CUM_RETURN({"periods": [5, 20, 60, 120]})

    start_time = time.time()
    result = factor.calculate_vectorized(large_data)
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"   处理1000条数据(4个周期)用时: {processing_time:.4f}秒")
    print(f"   平均每条记录: {processing_time/1000*1000:.4f}毫秒")

    # 验证大数据结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   大数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查数据完整性
    data_completeness = {}
    for period in [5, 20, 60, 120]:
        col_name = f'CUM_RETURN_{period}'
        non_null_count = result[col_name].count()
        expected_count = max(0, len(result) - period)
        completeness = non_null_count / expected_count if expected_count > 0 else 1
        data_completeness[period] = completeness
        print(f"   {period}日数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 CUM_RETURN因子模块化测试")
    print("=" * 50)

    try:
        test_cum_return_basic()
        test_cum_return_edge_cases()
        test_cum_return_different_periods()
        test_cum_return_performance()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()