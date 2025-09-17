"""
MA_SLOPE测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import MA_SLOPE


def create_test_data(length=20, trend_pattern="uptrend") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据趋势模式生成价格序列
    if trend_pattern == "uptrend":
        # 上升趋势：价格持续上涨
        prices = [base_price + i * 0.5 + np.random.normal(0, 0.1) for i in range(length)]
    elif trend_pattern == "downtrend":
        # 下降趋势：价格持续下跌
        prices = [base_price - i * 0.3 + np.random.normal(0, 0.1) for i in range(length)]
    elif trend_pattern == "sideways":
        # 横盘整理：价格基本保持水平
        prices = [base_price + np.random.normal(0, 0.2) for _ in range(length)]
    elif trend_pattern == "accelerating":
        # 加速上涨：斜率越来越大
        prices = []
        for i in range(length):
            acceleration = i * 0.02  # 加速因子
            price = base_price + i * 0.2 + (i ** 2) * acceleration + np.random.normal(0, 0.1)
            prices.append(price)
    elif trend_pattern == "volatile":
        # 剧烈波动：价格大幅上下波动
        prices = []
        for i in range(length):
            trend = base_price + i * 0.1
            volatility = 2.0 * np.sin(i * 0.5) + np.random.normal(0, 0.5)
            prices.append(trend + volatility)
    else:  # mixed
        # 混合模式：前半段上涨，后半段下跌
        mid_point = length // 2
        prices = []
        for i in range(length):
            if i < mid_point:
                price = base_price + i * 0.4  # 上涨段
            else:
                price = base_price + mid_point * 0.4 - (i - mid_point) * 0.6  # 下跌段
            prices.append(price + np.random.normal(0, 0.1))

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_ma_slope_basic():
    """基础功能测试"""
    print("🧪 测试MA_SLOPE基础功能...")

    # 创建简单测试数据，方便手工验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9]  # 每天增长0.1
    })

    # 创建因子实例
    factor = MA_SLOPE({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证：对于均匀递增数据，MA斜率应该约等于每日增长量
    # 3日MA斜率应该约为0.1/3 ≈ 0.033
    # 5日MA斜率应该约为0.1/5 = 0.02
    non_null_slope3 = result['MA_SLOPE_3'].dropna()
    non_null_slope5 = result['MA_SLOPE_5'].dropna()

    if len(non_null_slope3) > 0:
        print(f"   MA_SLOPE_3样例: 期望≈0.033, 实际={non_null_slope3.iloc[0]:.3f}")
    if len(non_null_slope5) > 0:
        print(f"   MA_SLOPE_5样例: 期望≈0.020, 实际={non_null_slope5.iloc[0]:.3f}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查前几行是否正确为NaN
    print(f"   前3行MA_SLOPE_3为NaN: {result['MA_SLOPE_3'].iloc[:3].isnull().all()}")
    print(f"   前5行MA_SLOPE_5为NaN: {result['MA_SLOPE_5'].iloc[:5].isnull().all()}")

    return result


def test_ma_slope_trend_patterns():
    """不同趋势模式测试"""
    print("\\n🧪 测试MA_SLOPE不同趋势模式...")

    factor = MA_SLOPE({"periods": [5, 10]})

    # 测试上升趋势
    uptrend_data = create_test_data(20, "uptrend")
    uptrend_result = factor.calculate_vectorized(uptrend_data)
    uptrend_slope5 = uptrend_result['MA_SLOPE_5'].dropna()

    # 测试下降趋势
    downtrend_data = create_test_data(20, "downtrend")
    downtrend_result = factor.calculate_vectorized(downtrend_data)
    downtrend_slope5 = downtrend_result['MA_SLOPE_5'].dropna()

    # 测试横盘趋势
    sideways_data = create_test_data(20, "sideways")
    sideways_result = factor.calculate_vectorized(sideways_data)
    sideways_slope5 = sideways_result['MA_SLOPE_5'].dropna()

    # 测试加速趋势
    accel_data = create_test_data(20, "accelerating")
    accel_result = factor.calculate_vectorized(accel_data)
    accel_slope5 = accel_result['MA_SLOPE_5'].dropna()

    print(f"   上升趋势: 平均斜率 {uptrend_slope5.mean():.4f}, 标准差 {uptrend_slope5.std():.4f}")
    print(f"   下降趋势: 平均斜率 {downtrend_slope5.mean():.4f}, 标准差 {downtrend_slope5.std():.4f}")
    print(f"   横盘趋势: 平均斜率 {sideways_slope5.mean():.4f}, 标准差 {sideways_slope5.std():.4f}")
    print(f"   加速趋势: 平均斜率 {accel_slope5.mean():.4f}, 最大值 {accel_slope5.max():.4f}")

    # 验证趋势特征
    upward_positive = uptrend_slope5.mean() > 0  # 上升趋势斜率为正
    downward_negative = downtrend_slope5.mean() < 0  # 下降趋势斜率为负
    sideways_near_zero = abs(sideways_slope5.mean()) < 0.1  # 横盘斜率接近零
    accel_increasing = accel_slope5.max() > uptrend_slope5.max()  # 加速趋势有更高峰值

    print(f"   趋势验证: 上升{'✅' if upward_positive else '❌'} 下降{'✅' if downward_negative else '❌'} 横盘{'✅' if sideways_near_zero else '❌'} 加速{'✅' if accel_increasing else '❌'}")


def test_ma_slope_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试MA_SLOPE边界情况...")

    factor = MA_SLOPE({"periods": [5]})

    # 测试1: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'hfq_close': [100.0, 102.0, 104.0]
    })

    result1 = factor.calculate_vectorized(short_data)
    all_null = result1['MA_SLOPE_5'].isnull().all()
    print(f"   短数据测试: {'✅ 全为NaN' if all_null else '❌ 应为NaN'}")

    # 测试2: 价格完全平坦
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [100.0] * 15
    })

    result2 = factor.calculate_vectorized(flat_data)
    flat_slope = result2['MA_SLOPE_5'].dropna()
    all_zero = (flat_slope.abs() < 0.0001).all() if len(flat_slope) > 0 else True
    print(f"   平坦价格测试: {'✅ 斜率近似为0' if all_zero else '❌ 应为0'}， 实际范围: [{flat_slope.min():.6f}, {flat_slope.max():.6f}]")

    # 测试3: 极端价格跳跃
    jump_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 12,
        'trade_date': pd.date_range('2025-01-01', periods=12),
        'hfq_close': [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0]  # 价格翻倍
    })

    result3 = factor.calculate_vectorized(jump_data)
    jump_slope = result3['MA_SLOPE_5'].dropna()
    if len(jump_slope) > 0:
        print(f"   价格跳跃测试: 斜率范围 [{jump_slope.min():.2f}, {jump_slope.max():.2f}]")

    # 测试4: 单个周期足够但总数据少
    minimal_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 6,
        'trade_date': pd.date_range('2025-01-01', periods=6),
        'hfq_close': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    })

    result4 = factor.calculate_vectorized(minimal_data)
    minimal_slope = result4['MA_SLOPE_5'].dropna()
    has_valid_result = len(minimal_slope) > 0
    print(f"   最小数据测试: {'✅ 有结果' if has_valid_result else '❌ 无结果'}， 有效计算数量: {len(minimal_slope)}")


def test_ma_slope_formula_validation():
    """MA斜率公式验证测试"""
    print("\\n🧪 测试MA_SLOPE公式验证...")

    # 创建简单线性增长数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [10 + i * 2 for i in range(15)]  # 每天增长2
    })

    factor = MA_SLOPE({"periods": [5]})
    result = factor.calculate_vectorized(test_data)

    # 手工验证MA_SLOPE_5计算
    # 对于线性增长数据，MA也应该线性增长
    # MA_SLOPE应该近似等于日增长量
    expected_slope = 2 / 5  # 日增长量/周期 = 2/5 = 0.4

    valid_slopes = result['MA_SLOPE_5'].dropna()
    if len(valid_slopes) > 0:
        # 检查斜率是否接近预期值
        actual_slope = valid_slopes.iloc[0]
        diff = abs(actual_slope - expected_slope)
        is_close = diff < 0.01
        print(f"   线性增长验证: 期望斜率 {expected_slope:.3f}, 实际斜率 {actual_slope:.3f}, 差异 {diff:.3f}")
        print(f"   公式验证: {'✅ 通过' if is_close else '❌ 失败'}")

        # 检查所有有效斜率是否一致（对于线性数据应该一致）
        slope_std = valid_slopes.std()
        is_consistent = slope_std < 0.01
        print(f"   一致性验证: 斜率标准差 {slope_std:.6f}, {'✅ 一致' if is_consistent else '❌ 不一致'}")
    else:
        print("   ❌ 无有效斜率数据")


def test_ma_slope_performance():
    """性能测试"""
    print("\\n🧪 测试MA_SLOPE性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000, "mixed")
    factor = MA_SLOPE({"periods": [5, 10, 20, 60]})

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
        col_name = f'MA_SLOPE_{period}'
        non_null_count = result[col_name].count()
        expected_count = max(0, len(result) - period)
        completeness = non_null_count / expected_count if expected_count > 0 else 1
        print(f"   {period}日数据完整度: {completeness:.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 MA_SLOPE因子模块化测试")
    print("=" * 50)

    try:
        test_ma_slope_basic()
        test_ma_slope_trend_patterns()
        test_ma_slope_edge_cases()
        test_ma_slope_formula_validation()
        test_ma_slope_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()