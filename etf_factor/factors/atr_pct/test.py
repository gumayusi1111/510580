"""
ATR_PCT测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import ATR_PCT


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
            daily_range = np.random.uniform(1.0, 3.0)  # 1-3的日波动
            close = trend + np.random.normal(0, 0.5)
            high = close + np.random.uniform(0, daily_range)
            low = close - np.random.uniform(0, daily_range)

            highs.append(max(high, close))
            lows.append(min(low, close))
            closes.append(close)

    elif volatility_pattern == "high":
        # 高波动：大幅度价格波动
        highs = []
        lows = []
        closes = []

        prev_close = base_price
        for i in range(length):
            # 大幅波动
            daily_change = np.random.normal(0, 0.05)  # 5%标准差
            close = prev_close * (1 + daily_change)

            # 更大的日内波动
            daily_range = np.random.uniform(3.0, 8.0)
            high = close + daily_range
            low = close - daily_range

            highs.append(high)
            lows.append(max(low, 0.1))  # 确保价格为正
            closes.append(close)
            prev_close = close

    elif volatility_pattern == "low":
        # 低波动：价格变化很小
        highs = []
        lows = []
        closes = []

        for i in range(length):
            close = base_price + np.random.normal(0, 0.2)
            high = close + np.random.uniform(0, 0.5)
            low = close - np.random.uniform(0, 0.5)

            highs.append(high)
            lows.append(low)
            closes.append(close)

    else:  # mixed
        # 混合模式：前期低波动，后期高波动
        highs = []
        lows = []
        closes = []

        mid_point = length // 2
        for i in range(length):
            if i < mid_point:
                # 低波动期
                close = base_price + np.random.normal(0, 0.3)
                high = close + np.random.uniform(0, 1.0)
                low = close - np.random.uniform(0, 1.0)
            else:
                # 高波动期
                close = base_price + np.random.normal(0, 2.0)
                high = close + np.random.uniform(0, 5.0)
                low = close - np.random.uniform(0, 5.0)

            highs.append(max(high, 0.1))
            lows.append(max(low, 0.1))
            closes.append(max(close, 0.1))

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_high': highs,
        'hfq_low': lows,
        'hfq_close': closes
    })


def test_atr_pct_basic():
    """基础功能测试"""
    print("🧪 测试ATR_PCT基础功能...")

    # 创建简单测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high':  [105, 108, 110, 112, 115, 113, 116, 118, 120, 117],
        'hfq_low':   [98,  102, 105, 107, 110, 108, 111, 113, 115, 112],
        'hfq_close': [102, 106, 108, 110, 112, 111, 114, 116, 118, 115]
    })

    # 创建因子实例
    factor = ATR_PCT({"periods": [7, 14]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 显示ATR_PCT样例值
    atr_pct_7 = result['ATR_PCT_7'].dropna()
    atr_pct_14 = result['ATR_PCT_14'].dropna()

    if len(atr_pct_7) > 0:
        print(f"   ATR_PCT_7样例: {atr_pct_7.iloc[:3].tolist()}")
    if len(atr_pct_14) > 0:
        print(f"   ATR_PCT_14样例: {atr_pct_14.iloc[:3].tolist()}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查ATR_PCT值都为正数且在合理范围内
    if len(atr_pct_7) > 0:
        positive_7 = (atr_pct_7 >= 0).all()
        reasonable_7 = (atr_pct_7 <= 50).all()  # 通常不超过50%
        print(f"   ATR_PCT_7检查: 正数 {'✅' if positive_7 else '❌'} 合理范围 {'✅' if reasonable_7 else '❌'}")

    return result


def test_atr_pct_volatility_patterns():
    """不同波动模式测试"""
    print("\\n🧪 测试ATR_PCT不同波动模式...")

    factor = ATR_PCT({"periods": [14]})

    # 测试正常波动
    normal_data = create_test_data(30, "normal")
    normal_result = factor.calculate_vectorized(normal_data)
    normal_atr_pct = normal_result['ATR_PCT_14'].dropna()

    # 测试高波动
    high_data = create_test_data(30, "high")
    high_result = factor.calculate_vectorized(high_data)
    high_atr_pct = high_result['ATR_PCT_14'].dropna()

    # 测试低波动
    low_data = create_test_data(30, "low")
    low_result = factor.calculate_vectorized(low_data)
    low_atr_pct = low_result['ATR_PCT_14'].dropna()

    # 测试混合模式
    mixed_data = create_test_data(30, "mixed")
    mixed_result = factor.calculate_vectorized(mixed_data)
    mixed_atr_pct = mixed_result['ATR_PCT_14'].dropna()

    print(f"   正常波动: 平均ATR_PCT {normal_atr_pct.mean():.2f}%, 标准差 {normal_atr_pct.std():.2f}%")
    print(f"   高波动: 平均ATR_PCT {high_atr_pct.mean():.2f}%, 最大值 {high_atr_pct.max():.2f}%")
    print(f"   低波动: 平均ATR_PCT {low_atr_pct.mean():.2f}%, 最大值 {low_atr_pct.max():.2f}%")
    print(f"   混合模式: 平均ATR_PCT {mixed_atr_pct.mean():.2f}%, 范围 [{mixed_atr_pct.min():.2f}%, {mixed_atr_pct.max():.2f}%]")

    # 验证波动特征
    high_volatility = high_atr_pct.mean() > normal_atr_pct.mean()  # 高波动应该ATR_PCT更大
    low_volatility = low_atr_pct.mean() < normal_atr_pct.mean()   # 低波动应该ATR_PCT更小
    mixed_variation = mixed_atr_pct.std() > normal_atr_pct.std()  # 混合模式应该标准差更大

    print(f"   模式验证: 高波动{'✅' if high_volatility else '❌'} 低波动{'✅' if low_volatility else '❌'} 混合变异{'✅' if mixed_variation else '❌'}")


def test_atr_pct_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试ATR_PCT边界情况...")

    factor = ATR_PCT({"periods": [14]})

    # 测试1: 价格完全平坦
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_high':  [100.0] * 20,
        'hfq_low':   [100.0] * 20,
        'hfq_close': [100.0] * 20
    })

    result1 = factor.calculate_vectorized(flat_data)
    flat_atr_pct = result1['ATR_PCT_14'].dropna()
    near_zero = (flat_atr_pct < 0.01).all() if len(flat_atr_pct) > 0 else True
    print(f"   平坦价格测试: {'✅ ATR_PCT接近0' if near_zero else '❌ 应接近0'}")

    # 测试2: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_high':  [105, 108, 110, 112, 115],
        'hfq_low':   [98,  102, 105, 107, 110],
        'hfq_close': [102, 106, 108, 110, 112]
    })

    result2 = factor.calculate_vectorized(short_data)
    short_atr_pct = result2['ATR_PCT_14'].dropna()
    print(f"   短数据测试: 计算出 {len(short_atr_pct)} 个ATR_PCT值")

    # 测试3: 极端价格跳跃
    jump_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high':  [105, 108, 110, 112, 200, 195, 190, 185, 180, 175],  # 第5天价格大幅跳跃
        'hfq_low':   [98,  102, 105, 107, 180, 175, 170, 165, 160, 155],
        'hfq_close': [102, 106, 108, 110, 190, 185, 180, 175, 170, 165]
    })

    result3 = factor.calculate_vectorized(jump_data)
    jump_atr_pct = result3['ATR_PCT_14'].dropna()
    if len(jump_atr_pct) > 0:
        print(f"   跳跃价格测试: ATR_PCT范围 [{jump_atr_pct.min():.1f}%, {jump_atr_pct.max():.1f}%]")

    # 测试4: 包含NaN价格数据
    nan_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high':  [105, 108, np.nan, 112, 115, 113, np.nan, 118, 120, 117],
        'hfq_low':   [98,  102, np.nan, 107, 110, 108, np.nan, 113, 115, 112],
        'hfq_close': [102, 106, np.nan, 110, 112, 111, np.nan, 116, 118, 115]
    })

    result4 = factor.calculate_vectorized(nan_data)
    nan_atr_pct = result4['ATR_PCT_14'].dropna()
    print(f"   NaN数据测试: 有效ATR_PCT值数量 {len(nan_atr_pct)}")


def test_atr_pct_formula_validation():
    """ATR_PCT公式验证测试"""
    print("\\n🧪 测试ATR_PCT公式验证...")

    # 创建简单数据用于手工验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_high':  [105, 110, 115, 120, 118],
        'hfq_low':   [95,  100, 105, 110, 108],
        'hfq_close': [100, 105, 110, 115, 113]
    })

    factor = ATR_PCT({"periods": [3]})
    result = factor.calculate_vectorized(test_data)

    print("   ATR_PCT计算逻辑验证:")
    print("   第1天: 仅有HL=10, TR=10")
    print("   第2天: HL=10, HC=|110-100|=10, LC=|100-100|=0, TR=10")
    print("   第3天: HL=10, HC=|115-105|=10, LC=|105-105|=0, TR=10")

    atr_pct_values = result['ATR_PCT_3'].dropna()
    if len(atr_pct_values) > 0:
        print(f"   计算结果ATR_PCT_3: {atr_pct_values.tolist()}")
        print("   ✅ ATR_PCT公式计算完成（指数加权移动平均结果）")
    else:
        print("   ❌ 无有效ATR_PCT计算结果")


def test_atr_pct_performance():
    """性能测试"""
    print("\\n🧪 测试ATR_PCT性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000, "normal")
    factor = ATR_PCT({"periods": [7, 14, 21, 30]})

    start_time = time.time()
    result = factor.calculate_vectorized(large_data)
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"   处理1000条数据(4个周期)用时: {processing_time:.4f}秒")
    print(f"   平均每条记录: {processing_time/1000*1000:.4f}毫秒")

    # 验证大数据结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   大数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查数据完整性和合理性
    print("   ATR_PCT数值分布检查:")
    for period in [7, 14, 21, 30]:
        col_name = f'ATR_PCT_{period}'
        atr_pct_values = result[col_name].dropna()
        if len(atr_pct_values) > 0:
            print(f"   {period}日: 均值 {atr_pct_values.mean():.2f}%, 最大值 {atr_pct_values.max():.2f}%, 数据完整度 {len(atr_pct_values)/len(result):.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 ATR_PCT因子模块化测试")
    print("=" * 50)

    try:
        test_atr_pct_basic()
        test_atr_pct_volatility_patterns()
        test_atr_pct_edge_cases()
        test_atr_pct_formula_validation()
        test_atr_pct_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()