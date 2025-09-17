"""
DAILY_RETURN测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import DAILY_RETURN


def create_test_data(length=10) -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    # 模拟价格序列：基础价格 + 随机波动
    base_price = 100
    price_changes = np.random.normal(0, 0.02, length)  # 平均2%的日波动
    prices = [base_price]

    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.01))  # 确保价格为正

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_daily_return_basic():
    """基础功能测试"""
    print("🧪 测试DAILY_RETURN基础功能...")

    # 创建简单测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_close': [100.0, 102.0, 99.96, 103.46, 101.38]
    })

    # 创建因子实例
    factor = DAILY_RETURN()

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证
    expected_returns = [
        np.nan,  # 第一天没有前一天数据
        (102.0 - 100.0) / 100.0 * 100,  # 2.0%
        (99.96 - 102.0) / 102.0 * 100,   # -2.0%
        (103.46 - 99.96) / 99.96 * 100,  # 3.5%
        (101.38 - 103.46) / 103.46 * 100 # -2.01%
    ]

    print("   手工验证vs因子结果:")
    for i, (expected, actual) in enumerate(zip(expected_returns, result['DAILY_RETURN'])):
        if pd.isna(expected):
            print(f"     第{i+1}天: 预期NaN, 实际{actual}")
        else:
            print(f"     第{i+1}天: 预期{expected:.2f}%, 实际{actual:.2f}%")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    return result


def test_daily_return_edge_cases():
    """边界情况测试"""
    print("\n🧪 测试DAILY_RETURN边界情况...")

    factor = DAILY_RETURN()

    # 测试1: 单行数据
    single_data = pd.DataFrame({
        'ts_code': ['510580.SH'],
        'trade_date': ['2025-01-01'],
        'hfq_close': [100.0]
    })

    result1 = factor.calculate_vectorized(single_data)
    print(f"   单行数据测试: {'✅ 通过' if pd.isna(result1['DAILY_RETURN'].iloc[0]) else '❌ 失败'}")

    # 测试2: 价格无变化
    no_change_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 100.0, 100.0]
    })

    result2 = factor.calculate_vectorized(no_change_data)
    zero_returns = result2['DAILY_RETURN'].dropna()
    all_zero = (zero_returns == 0).all()
    print(f"   无变化价格测试: {'✅ 通过' if all_zero else '❌ 失败'}")

    # 测试3: 极端价格变化
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 150.0, 75.0]  # +50%, -50%
    })

    result3 = factor.calculate_vectorized(extreme_data)
    print(f"   极端变化测试: 结果范围 {result3['DAILY_RETURN'].dropna().min():.1f}% 到 {result3['DAILY_RETURN'].dropna().max():.1f}%")


def test_daily_return_performance():
    """性能测试"""
    print("\n🧪 测试DAILY_RETURN性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(10000)
    factor = DAILY_RETURN()

    start_time = time.time()
    result = factor.calculate_vectorized(large_data)
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"   处理10000条数据用时: {processing_time:.4f}秒")
    print(f"   平均每条记录: {processing_time/10000*1000:.4f}毫秒")

    # 验证大数据结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   大数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")


def run_all_tests():
    """运行所有测试"""
    print("📊 DAILY_RETURN因子模块化测试")
    print("=" * 50)

    try:
        test_daily_return_basic()
        test_daily_return_edge_cases()
        test_daily_return_performance()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()