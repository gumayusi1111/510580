"""
MOM测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import MOM


def create_test_data(length=20, trend="stable") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据趋势类型生成价格序列
    if trend == "upward":
        # 上升趋势：每天平均上涨1%，加上随机波动
        trend_component = np.linspace(0, 0.2, length)  # 20%总涨幅
        noise = np.random.normal(0, 0.01, length)  # 1%随机波动
    elif trend == "downward":
        # 下降趋势：每天平均下跌0.5%，加上随机波动
        trend_component = np.linspace(0, -0.1, length)  # 10%总跌幅
        noise = np.random.normal(0, 0.01, length)  # 1%随机波动
    else:  # stable
        # 震荡趋势：无明显趋势，只有随机波动
        trend_component = np.zeros(length)
        noise = np.random.normal(0, 0.015, length)  # 1.5%随机波动

    prices = []
    for i in range(length):
        price = base_price * (1 + trend_component[i] + noise[i])
        prices.append(max(price, 0.01))  # 确保价格为正

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_mom_basic():
    """基础功能测试"""
    print("🧪 测试MOM基础功能...")

    # 创建简单测试数据，方便验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0, 102.0, 98.0, 105.0, 95.0, 101.0, 99.0, 103.0, 97.0, 104.0]
    })

    # 创建因子实例
    factor = MOM({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证
    # MOM_3第4行(索引3): 105.0 - 100.0 = 5.0
    # MOM_5第6行(索引5): 101.0 - 100.0 = 1.0
    manual_mom3_idx3 = test_data['hfq_close'].iloc[3] - test_data['hfq_close'].iloc[0]  # 105-100=5
    manual_mom5_idx5 = test_data['hfq_close'].iloc[5] - test_data['hfq_close'].iloc[0]  # 101-100=1

    print(f"   手工验证MOM_3[3]: {manual_mom3_idx3}, 计算结果: {result['MOM_3'].iloc[3]}")
    print(f"   手工验证MOM_5[5]: {manual_mom5_idx5}, 计算结果: {result['MOM_5'].iloc[5]}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查前几行是否正确为NaN
    print(f"   前3行MOM_3为NaN: {result['MOM_3'].iloc[:3].isnull().all()}")
    print(f"   前5行MOM_5为NaN: {result['MOM_5'].iloc[:5].isnull().all()}")

    return result


def test_mom_trends():
    """不同趋势测试"""
    print("\n🧪 测试MOM不同趋势...")

    factor = MOM({"periods": [10]})

    # 测试上升趋势
    upward_data = create_test_data(20, "upward")
    upward_result = factor.calculate_vectorized(upward_data)
    upward_mom = upward_result['MOM_10'].dropna()

    # 测试下降趋势
    downward_data = create_test_data(20, "downward")
    downward_result = factor.calculate_vectorized(downward_data)
    downward_mom = downward_result['MOM_10'].dropna()

    # 测试震荡趋势
    stable_data = create_test_data(20, "stable")
    stable_result = factor.calculate_vectorized(stable_data)
    stable_mom = stable_result['MOM_10'].dropna()

    print(f"   上升趋势: 平均动量 {upward_mom.mean():.4f}, 最大动量 {upward_mom.max():.4f}")
    print(f"   下降趋势: 平均动量 {downward_mom.mean():.4f}, 最小动量 {downward_mom.min():.4f}")
    print(f"   震荡趋势: 平均动量 {stable_mom.mean():.4f}, 动量范围 [{stable_mom.min():.4f}, {stable_mom.max():.4f}]")

    # 验证趋势特征
    upward_positive = (upward_mom > 0).sum() / len(upward_mom) > 0.6  # 上升趋势应该多数为正
    downward_negative = (downward_mom < 0).sum() / len(downward_mom) > 0.6  # 下降趋势应该多数为负
    stable_mixed = abs(stable_mom.mean()) < abs(upward_mom.mean())  # 震荡趋势平均动量应该较小

    print(f"   趋势验证: 上升{'✅' if upward_positive else '❌'} 下降{'✅' if downward_negative else '❌'} 震荡{'✅' if stable_mixed else '❌'}")


def test_mom_edge_cases():
    """边界情况测试"""
    print("\n🧪 测试MOM边界情况...")

    factor = MOM({"periods": [5]})

    # 测试1: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 102.0, 104.0]
    })

    result1 = factor.calculate_vectorized(short_data)
    all_null = result1['MOM_5'].isnull().all()
    print(f"   短数据测试: {'✅ 全为NaN' if all_null else '❌ 应为NaN'}")

    # 测试2: 价格无变化
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0] * 10
    })

    result2 = factor.calculate_vectorized(flat_data)
    zero_mom = result2['MOM_5'].dropna()
    all_zero = (zero_mom == 0).all() if len(zero_mom) > 0 else True
    print(f"   无变化价格测试: {'✅ 动量为0' if all_zero else '❌ 应为0'}")

    # 测试3: 单步大幅变化
    step_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 8,
        'trade_date': pd.date_range('2025-01-01', periods=8),
        'hfq_close': [100.0, 100.0, 100.0, 100.0, 100.0, 150.0, 150.0, 150.0]
    })

    result3 = factor.calculate_vectorized(step_data)
    step_mom = result3['MOM_5'].dropna()
    if len(step_mom) > 0:
        print(f"   阶跃变化测试: 动量范围 [{step_mom.min():.1f}, {step_mom.max():.1f}]")


def test_mom_different_periods():
    """不同周期参数测试"""
    print("\n🧪 测试MOM不同周期...")

    test_data = create_test_data(30, "upward")

    # 测试单周期
    factor1 = MOM({"periods": [10]})
    result1 = factor1.calculate_vectorized(test_data)
    print(f"   单周期测试: 输出列 {[col for col in result1.columns if 'MOM' in col]}")

    # 测试多周期
    factor2 = MOM({"periods": [5, 10, 20]})
    result2 = factor2.calculate_vectorized(test_data)
    expected_cols = ['MOM_5', 'MOM_10', 'MOM_20']
    has_all_cols = all(col in result2.columns for col in expected_cols)
    print(f"   多周期测试: {'✅ 通过' if has_all_cols else '❌ 失败'}")

    # 测试默认参数
    factor3 = MOM()
    result3 = factor3.calculate_vectorized(test_data)
    default_cols = ['MOM_5', 'MOM_10', 'MOM_20']
    has_default_cols = all(col in result3.columns for col in default_cols)
    print(f"   默认参数测试: {'✅ 通过' if has_default_cols else '❌ 失败'}")

    # 周期长度关系验证
    mom_5 = result2['MOM_5'].dropna()
    mom_10 = result2['MOM_10'].dropna()
    mom_20 = result2['MOM_20'].dropna()

    # 在上升趋势中，长周期动量通常大于短周期动量
    if len(mom_5) > 0 and len(mom_10) > 0 and len(mom_20) > 0:
        avg_5 = mom_5.mean()
        avg_10 = mom_10.mean()
        avg_20 = mom_20.mean()
        print(f"   周期关系: MOM_5={avg_5:.2f}, MOM_10={avg_10:.2f}, MOM_20={avg_20:.2f}")


def test_mom_performance():
    """性能测试"""
    print("\n🧪 测试MOM性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000)
    factor = MOM({"periods": [5, 10, 20, 60]})

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
    for period in [5, 10, 20, 60]:
        col_name = f'MOM_{period}'
        non_null_count = result[col_name].count()
        expected_count = max(0, len(result) - period)
        completeness = non_null_count / expected_count if expected_count > 0 else 1
        print(f"   {period}日数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 MOM因子模块化测试")
    print("=" * 50)

    try:
        test_mom_basic()
        test_mom_trends()
        test_mom_edge_cases()
        test_mom_different_periods()
        test_mom_performance()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()