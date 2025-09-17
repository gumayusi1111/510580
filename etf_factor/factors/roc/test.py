"""
ROC测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import ROC


def create_test_data(length=20, change_pattern="gradual") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据变化模式生成价格序列
    if change_pattern == "gradual":
        # 渐进式变化：每天1%增长
        prices = [base_price * (1.01 ** i) for i in range(length)]
    elif change_pattern == "volatile":
        # 波动式变化：随机大幅波动
        prices = [base_price]
        for i in range(1, length):
            change = np.random.normal(0, 0.05)  # 5%标准差的随机变化
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 0.01))
    elif change_pattern == "step":
        # 阶跃式变化：特定时点大幅变化
        prices = [base_price] * (length // 2)
        prices.extend([base_price * 1.5] * (length - length // 2))  # 50%上涨
    else:  # stable
        # 稳定变化：基本无变化
        prices = [base_price + np.random.normal(0, 0.1) for _ in range(length)]

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_roc_basic():
    """基础功能测试"""
    print("🧪 测试ROC基础功能...")

    # 创建简单测试数据，方便手工验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0, 105.0, 110.0, 115.0, 120.0, 115.0, 110.0, 105.0, 100.0, 95.0]
    })

    # 创建因子实例
    factor = ROC({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证
    # ROC_3第4行(索引3): (115.0 - 100.0) / 100.0 * 100 = 15.0%
    # ROC_5第6行(索引5): (115.0 - 100.0) / 100.0 * 100 = 15.0%
    manual_roc3_idx3 = ((test_data['hfq_close'].iloc[3] - test_data['hfq_close'].iloc[0]) / test_data['hfq_close'].iloc[0]) * 100
    manual_roc5_idx5 = ((test_data['hfq_close'].iloc[5] - test_data['hfq_close'].iloc[0]) / test_data['hfq_close'].iloc[0]) * 100

    print(f"   手工验证ROC_3[3]: {manual_roc3_idx3:.1f}%, 计算结果: {result['ROC_3'].iloc[3]:.1f}%")
    print(f"   手工验证ROC_5[5]: {manual_roc5_idx5:.1f}%, 计算结果: {result['ROC_5'].iloc[5]:.1f}%")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查前几行是否正确为NaN
    print(f"   前3行ROC_3为NaN: {result['ROC_3'].iloc[:3].isnull().all()}")
    print(f"   前5行ROC_5为NaN: {result['ROC_5'].iloc[:5].isnull().all()}")

    return result


def test_roc_change_patterns():
    """不同变化模式测试"""
    print("\n🧪 测试ROC不同变化模式...")

    factor = ROC({"periods": [10]})

    # 测试渐进式变化
    gradual_data = create_test_data(20, "gradual")
    gradual_result = factor.calculate_vectorized(gradual_data)
    gradual_roc = gradual_result['ROC_10'].dropna()

    # 测试波动式变化
    volatile_data = create_test_data(20, "volatile")
    volatile_result = factor.calculate_vectorized(volatile_data)
    volatile_roc = volatile_result['ROC_10'].dropna()

    # 测试阶跃式变化
    step_data = create_test_data(20, "step")
    step_result = factor.calculate_vectorized(step_data)
    step_roc = step_result['ROC_10'].dropna()

    print(f"   渐进变化: 平均ROC {gradual_roc.mean():.2f}%, 标准差 {gradual_roc.std():.2f}%")
    print(f"   波动变化: 平均ROC {volatile_roc.mean():.2f}%, 标准差 {volatile_roc.std():.2f}%")
    print(f"   阶跃变化: 平均ROC {step_roc.mean():.2f}%, 范围 [{step_roc.min():.1f}%, {step_roc.max():.1f}%]")

    # 验证变化特征
    gradual_positive = gradual_roc.mean() > 0  # 渐进增长应该ROC为正
    volatile_varied = volatile_roc.std() > gradual_roc.std()  # 波动式应该标准差更大
    step_extreme = step_roc.max() > gradual_roc.max()  # 阶跃式应该有更高的峰值

    print(f"   模式验证: 渐进{'✅' if gradual_positive else '❌'} 波动{'✅' if volatile_varied else '❌'} 阶跃{'✅' if step_extreme else '❌'}")


def test_roc_edge_cases():
    """边界情况测试"""
    print("\n🧪 测试ROC边界情况...")

    factor = ROC({"periods": [5]})

    # 测试1: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 102.0, 104.0]
    })

    result1 = factor.calculate_vectorized(short_data)
    all_null = result1['ROC_5'].isnull().all()
    print(f"   短数据测试: {'✅ 全为NaN' if all_null else '❌ 应为NaN'}")

    # 测试2: 价格无变化
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100.0] * 10
    })

    result2 = factor.calculate_vectorized(flat_data)
    zero_roc = result2['ROC_5'].dropna()
    all_zero = (zero_roc == 0).all() if len(zero_roc) > 0 else True
    print(f"   无变化价格测试: {'✅ ROC为0' if all_zero else '❌ 应为0'}")

    # 测试3: 价格翻倍
    double_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 8,
        'trade_date': pd.date_range('2025-01-01', periods=8),
        'hfq_close': [100.0, 100.0, 100.0, 100.0, 100.0, 200.0, 200.0, 200.0]
    })

    result3 = factor.calculate_vectorized(double_data)
    double_roc = result3['ROC_5'].dropna()
    if len(double_roc) > 0:
        print(f"   翻倍变化测试: ROC范围 [{double_roc.min():.0f}%, {double_roc.max():.0f}%]")


def test_roc_vs_cumulative_return():
    """ROC与累计收益率对比测试"""
    print("\n🧪 测试ROC与累计收益率的关系...")

    # 创建测试数据
    test_data = create_test_data(15, "gradual")

    factor = ROC({"periods": [5, 10]})
    result = factor.calculate_vectorized(test_data)

    # ROC实际上就是累计收益率的百分比形式
    # ROC_5 应该等于 5日累计收益率
    for i in range(5, len(test_data)):
        current_price = test_data['hfq_close'].iloc[i]
        prev_price = test_data['hfq_close'].iloc[i-5]
        manual_cum_return = ((current_price - prev_price) / prev_price) * 100
        calculated_roc = result['ROC_5'].iloc[i]

        diff = abs(manual_cum_return - calculated_roc)
        if diff < 0.01:  # 精度容差
            continue
        else:
            print(f"   第{i+1}行: 手工计算{manual_cum_return:.2f}%, ROC计算{calculated_roc:.2f}%")
            break
    else:
        print("   ✅ ROC与手工计算的累计收益率完全一致")


def test_roc_performance():
    """性能测试"""
    print("\n🧪 测试ROC性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000)
    factor = ROC({"periods": [5, 10, 20, 60]})

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
        col_name = f'ROC_{period}'
        non_null_count = result[col_name].count()
        expected_count = max(0, len(result) - period)
        completeness = non_null_count / expected_count if expected_count > 0 else 1
        print(f"   {period}日数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 ROC因子模块化测试")
    print("=" * 50)

    try:
        test_roc_basic()
        test_roc_change_patterns()
        test_roc_edge_cases()
        test_roc_vs_cumulative_return()
        test_roc_performance()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()