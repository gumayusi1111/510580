"""
TR测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import TR


def create_test_data(length=20, volatility_pattern="normal") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据波动模式生成OHLC价格序列
    if volatility_pattern == "normal":
        # 正常波动：合理的日内波动
        highs = []
        lows = []
        closes = []

        for i in range(length):
            # 基础价格随时间变化
            trend = base_price + i * 0.5

            # 日内波动
            daily_range = np.random.uniform(0.5, 2.0)  # 0.5-2.0的日波动
            close = trend + np.random.normal(0, 0.3)
            high = close + np.random.uniform(0, daily_range)
            low = close - np.random.uniform(0, daily_range)

            highs.append(max(high, close))
            lows.append(min(low, close))
            closes.append(close)

    elif volatility_pattern == "high":
        # 高波动：大幅度价格跳动
        highs = []
        lows = []
        closes = []

        prev_close = base_price
        for i in range(length):
            # 大幅波动
            daily_change = np.random.normal(0, 0.05)  # 5%标准差
            close = prev_close * (1 + daily_change)

            # 更大的日内波动
            daily_range = np.random.uniform(2.0, 5.0)
            high = close + daily_range
            low = close - daily_range

            highs.append(high)
            lows.append(max(low, 0.1))  # 确保价格为正
            closes.append(close)
            prev_close = close

    elif volatility_pattern == "gap":
        # 跳空模式：价格有跳空gap
        highs = []
        lows = []
        closes = []

        prev_close = base_price
        for i in range(length):
            if i == 5:  # 在第6天制造跳空上涨
                gap = 5.0
            elif i == 10:  # 在第11天制造跳空下跌
                gap = -8.0
            else:
                gap = 0

            open_price = prev_close + gap
            close = open_price + np.random.uniform(-1, 1)
            high = max(open_price, close) + np.random.uniform(0, 1)
            low = min(open_price, close) - np.random.uniform(0, 1)

            highs.append(high)
            lows.append(max(low, 0.1))
            closes.append(close)
            prev_close = close

    else:  # stable
        # 稳定模式：低波动
        highs = []
        lows = []
        closes = []

        for i in range(length):
            close = base_price + np.random.normal(0, 0.1)
            high = close + np.random.uniform(0, 0.2)
            low = close - np.random.uniform(0, 0.2)

            highs.append(high)
            lows.append(low)
            closes.append(close)

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_high': highs,
        'hfq_low': lows,
        'hfq_close': closes
    })


def test_tr_basic():
    """基础功能测试"""
    print("🧪 测试TR基础功能...")

    # 创建简单测试数据，方便手工验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_high':  [10.5, 11.0, 10.8, 11.2, 10.9],
        'hfq_low':   [10.0, 10.3, 10.2, 10.5, 10.1],
        'hfq_close': [10.2, 10.7, 10.4, 10.8, 10.3]
    })

    # 创建因子实例
    factor = TR()

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证第二行（索引1）
    # TR = MAX(高-低, ABS(高-昨收), ABS(低-昨收))
    # 第2行: 高=11.0, 低=10.3, 收=10.7, 昨收=10.2
    # HL = 11.0 - 10.3 = 0.7
    # HC = |11.0 - 10.2| = 0.8
    # LC = |10.3 - 10.2| = 0.1
    # TR = MAX(0.7, 0.8, 0.1) = 0.8
    manual_tr_idx1 = max(
        test_data['hfq_high'].iloc[1] - test_data['hfq_low'].iloc[1],  # HL
        abs(test_data['hfq_high'].iloc[1] - test_data['hfq_close'].iloc[0]),  # HC
        abs(test_data['hfq_low'].iloc[1] - test_data['hfq_close'].iloc[0])   # LC
    )

    print(f"   手工验证TR[1]: {manual_tr_idx1:.1f}, 计算结果: {result['TR'].iloc[1]:.1f}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查第一行是否为NaN（缺少前一日收盘价）
    print(f"   第一行为NaN: {pd.isna(result['TR'].iloc[0])}")

    return result


def test_tr_volatility_patterns():
    """不同波动模式测试"""
    print("\\n🧪 测试TR不同波动模式...")

    factor = TR()

    # 测试正常波动
    normal_data = create_test_data(20, "normal")
    normal_result = factor.calculate_vectorized(normal_data)
    normal_tr = normal_result['TR'].dropna()

    # 测试高波动
    high_data = create_test_data(20, "high")
    high_result = factor.calculate_vectorized(high_data)
    high_tr = high_result['TR'].dropna()

    # 测试跳空模式
    gap_data = create_test_data(20, "gap")
    gap_result = factor.calculate_vectorized(gap_data)
    gap_tr = gap_result['TR'].dropna()

    print(f"   正常波动: 平均TR {normal_tr.mean():.2f}, 标准差 {normal_tr.std():.2f}")
    print(f"   高波动: 平均TR {high_tr.mean():.2f}, 标准差 {high_tr.std():.2f}")
    print(f"   跳空模式: 平均TR {gap_tr.mean():.2f}, 最大值 {gap_tr.max():.2f}")

    # 验证波动特征
    high_volatility = high_tr.mean() > normal_tr.mean()  # 高波动应该TR更大
    gap_extreme = gap_tr.max() > normal_tr.max()  # 跳空应该有更高的极值

    print(f"   模式验证: 高波动{'✅' if high_volatility else '❌'} 跳空极值{'✅' if gap_extreme else '❌'}")


def test_tr_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试TR边界情况...")

    factor = TR()

    # 测试1: 单行数据（无法计算TR）
    single_data = pd.DataFrame({
        'ts_code': ['510580.SH'],
        'trade_date': [pd.Timestamp('2025-01-01')],
        'hfq_high': [100.0],
        'hfq_low': [98.0],
        'hfq_close': [99.0]
    })

    result1 = factor.calculate_vectorized(single_data)
    first_null = pd.isna(result1['TR'].iloc[0])
    print(f"   单行数据测试: {'✅ 第一行为NaN' if first_null else '❌ 应为NaN'}")

    # 测试2: 价格无波动（高=低=收）
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_high': [100.0, 100.0, 100.0, 100.0, 100.0],
        'hfq_low': [100.0, 100.0, 100.0, 100.0, 100.0],
        'hfq_close': [100.0, 100.0, 100.0, 100.0, 100.0]
    })

    result2 = factor.calculate_vectorized(flat_data)
    flat_tr = result2['TR'].dropna()
    all_zero = (flat_tr == 0).all() if len(flat_tr) > 0 else True
    print(f"   无波动价格测试: {'✅ TR为0' if all_zero else '❌ 应为0'}")

    # 测试3: 极端跳空
    gap_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_high': [100.0, 120.0, 110.0],   # 大幅跳空上涨
        'hfq_low': [95.0, 115.0, 105.0],
        'hfq_close': [98.0, 118.0, 108.0]
    })

    result3 = factor.calculate_vectorized(gap_data)
    gap_tr = result3['TR'].dropna()
    if len(gap_tr) > 0:
        # 第二行的TR应该捕获跳空: 高120与昨收98的差异
        expected_tr = abs(120.0 - 98.0)  # HC = |120 - 98| = 22
        actual_tr = result3['TR'].iloc[1]
        print(f"   跳空测试: 预期TR≈{expected_tr:.0f}, 实际TR={actual_tr:.1f}")


def test_tr_formula_validation():
    """TR公式验证测试"""
    print("\\n🧪 测试TR公式验证...")

    # 创建精确测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 4,
        'trade_date': pd.date_range('2025-01-01', periods=4),
        'hfq_high':  [105, 108, 112, 109],
        'hfq_low':   [100, 103, 107, 104],
        'hfq_close': [102, 106, 110, 107]
    })

    factor = TR()
    result = factor.calculate_vectorized(test_data)

    # 验证每一行的TR计算
    for i in range(1, len(test_data)):  # 从第2行开始（第1行缺少前一日收盘）
        high = test_data['hfq_high'].iloc[i]
        low = test_data['hfq_low'].iloc[i]
        close = test_data['hfq_close'].iloc[i]
        prev_close = test_data['hfq_close'].iloc[i-1]

        hl = high - low
        hc = abs(high - prev_close)
        lc = abs(low - prev_close)

        manual_tr = max(hl, hc, lc)
        calculated_tr = result['TR'].iloc[i]

        diff = abs(manual_tr - calculated_tr)
        if diff < 0.01:  # 精度容差
            continue
        else:
            print(f"   第{i+1}行: 手工计算{manual_tr:.2f}, TR计算{calculated_tr:.2f}")
            break
    else:
        print("   ✅ TR公式计算与手工验证完全一致")


def test_tr_performance():
    """性能测试"""
    print("\\n🧪 测试TR性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000)
    factor = TR()

    start_time = time.time()
    result = factor.calculate_vectorized(large_data)
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"   处理1000条数据用时: {processing_time:.4f}秒")
    print(f"   平均每条记录: {processing_time/1000*1000:.4f}毫秒")

    # 验证大数据结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   大数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查数据完整性
    non_null_count = result['TR'].count()
    expected_count = max(0, len(result) - 1)  # 第一行为NaN
    completeness = non_null_count / expected_count if expected_count > 0 else 1
    print(f"   数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 TR因子模块化测试")
    print("=" * 50)

    try:
        test_tr_basic()
        test_tr_volatility_patterns()
        test_tr_edge_cases()
        test_tr_formula_validation()
        test_tr_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()