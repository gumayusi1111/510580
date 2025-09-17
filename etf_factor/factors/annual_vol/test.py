"""
ANNUAL_VOL测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import ANNUAL_VOL


def create_test_data(length=30, volatility_level="normal") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据波动率水平设置随机波动幅度
    if volatility_level == "low":
        noise_std = 0.005   # 0.5%日波动
    elif volatility_level == "high":
        noise_std = 0.03    # 3%日波动
    else:  # normal
        noise_std = 0.015   # 1.5%日波动

    # 生成价格序列
    returns = np.random.normal(0, noise_std, length)
    prices = [base_price]

    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 0.01))  # 确保价格为正

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_annual_vol_basic():
    """基础功能测试"""
    print("🧪 测试ANNUAL_VOL基础功能...")

    # 创建测试数据
    test_data = create_test_data(30, "normal")

    # 创建因子实例
    factor = ANNUAL_VOL({"periods": [10, 20]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 检查结果的合理性
    for period in [10, 20]:
        col_name = f'ANNUAL_VOL_{period}'
        vol_values = result[col_name].dropna()
        if len(vol_values) > 0:
            avg_vol = vol_values.mean()
            print(f"   {period}日年化波动率平均值: {avg_vol:.4f} ({avg_vol*100:.2f}%)")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查前几行是否正确为NaN
    print(f"   前10行ANNUAL_VOL_10为NaN: {result['ANNUAL_VOL_10'].iloc[:10].isnull().all()}")
    print(f"   前20行ANNUAL_VOL_20为NaN: {result['ANNUAL_VOL_20'].iloc[:20].isnull().all()}")

    return result


def test_annual_vol_different_volatility():
    """不同波动率水平测试"""
    print("\n🧪 测试ANNUAL_VOL不同波动率水平...")

    factor = ANNUAL_VOL({"periods": [20]})

    # 测试低波动率
    low_vol_data = create_test_data(30, "low")
    low_result = factor.calculate_vectorized(low_vol_data)
    low_vol_avg = low_result['ANNUAL_VOL_20'].dropna().mean()

    # 测试高波动率
    high_vol_data = create_test_data(30, "high")
    high_result = factor.calculate_vectorized(high_vol_data)
    high_vol_avg = high_result['ANNUAL_VOL_20'].dropna().mean()

    # 测试正常波动率
    normal_vol_data = create_test_data(30, "normal")
    normal_result = factor.calculate_vectorized(normal_vol_data)
    normal_vol_avg = normal_result['ANNUAL_VOL_20'].dropna().mean()

    print(f"   低波动率数据: 平均年化波动率 {low_vol_avg:.4f} ({low_vol_avg*100:.2f}%)")
    print(f"   正常波动率数据: 平均年化波动率 {normal_vol_avg:.4f} ({normal_vol_avg*100:.2f}%)")
    print(f"   高波动率数据: 平均年化波动率 {high_vol_avg:.4f} ({high_vol_avg*100:.2f}%)")

    # 验证波动率递增关系
    is_increasing = low_vol_avg < normal_vol_avg < high_vol_avg
    print(f"   波动率递增关系: {'✅ 正确' if is_increasing else '❌ 不正确'}")


def test_annual_vol_edge_cases():
    """边界情况测试"""
    print("\n🧪 测试ANNUAL_VOL边界情况...")

    factor = ANNUAL_VOL({"periods": [20]})

    # 测试1: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [100.0] * 15
    })

    result1 = factor.calculate_vectorized(short_data)
    expected_non_null = max(0, len(short_data) - 20)  # 期望的非空数据点
    actual_non_null = result1['ANNUAL_VOL_20'].count()
    print(f"   短数据测试: 期望{expected_non_null}个非空值，实际{actual_non_null}个")

    # 测试2: 价格无变化（零波动率）
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [100.0] * 25
    })

    result2 = factor.calculate_vectorized(flat_data)
    zero_vol_values = result2['ANNUAL_VOL_20'].dropna()
    all_zero = (zero_vol_values == 0).all() if len(zero_vol_values) > 0 else True
    print(f"   无变化价格测试: {'✅ 波动率为0' if all_zero else '❌ 应为0'}")

    # 测试3: 单一极端变化
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [100.0] * 10 + [200.0] + [100.0] * 14  # 中间一个极端值
    })

    result3 = factor.calculate_vectorized(extreme_data)
    extreme_vol_values = result3['ANNUAL_VOL_20'].dropna()
    if len(extreme_vol_values) > 0:
        print(f"   极端变化测试: 最大年化波动率 {extreme_vol_values.max():.4f}")


def test_annual_vol_manual_verification():
    """手工验证测试"""
    print("\n🧪 测试ANNUAL_VOL手工验证...")

    # 创建简单的测试数据，方便手工验证
    simple_prices = [100, 102, 98, 105, 95, 101, 99, 103, 97, 104]
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': simple_prices
    })

    factor = ANNUAL_VOL({"periods": [5]})
    result = factor.calculate_vectorized(test_data)

    # 手工验证最后一个数据点（第10行，索引9）
    # 计算第6-10行的收益率（索引5-9）
    manual_returns = []
    for i in range(5, 10):
        ret = (simple_prices[i] - simple_prices[i-1]) / simple_prices[i-1]
        manual_returns.append(ret)

    manual_std = np.std(manual_returns, ddof=1)  # 样本标准差
    manual_annual_vol = manual_std * np.sqrt(252)

    calculated_vol = result['ANNUAL_VOL_5'].iloc[9]

    print(f"   手工验证收益率: {[f'{r:.4f}' for r in manual_returns]}")
    print(f"   手工计算标准差: {manual_std:.6f}")
    print(f"   手工年化波动率: {manual_annual_vol:.6f}")
    print(f"   因子计算结果: {calculated_vol:.6f}")
    print(f"   差异: {abs(manual_annual_vol - calculated_vol):.8f}")


def test_annual_vol_performance():
    """性能测试"""
    print("\n🧪 测试ANNUAL_VOL性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(500)
    factor = ANNUAL_VOL({"periods": [20, 60, 120]})

    start_time = time.time()
    result = factor.calculate_vectorized(large_data)
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"   处理500条数据(3个周期)用时: {processing_time:.4f}秒")
    print(f"   平均每条记录: {processing_time/500*1000:.4f}毫秒")

    # 验证大数据结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   大数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查数据完整性
    for period in [20, 60, 120]:
        col_name = f'ANNUAL_VOL_{period}'
        non_null_count = result[col_name].count()
        expected_count = max(0, len(result) - period)
        completeness = non_null_count / expected_count if expected_count > 0 else 1
        print(f"   {period}日数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 ANNUAL_VOL因子模块化测试")
    print("=" * 50)

    try:
        test_annual_vol_basic()
        test_annual_vol_different_volatility()
        test_annual_vol_edge_cases()
        test_annual_vol_manual_verification()
        test_annual_vol_performance()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()