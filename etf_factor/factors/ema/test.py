"""
EMA测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import EMA


def create_test_data(length=20, price_pattern="uptrend") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据价格模式生成数据
    if price_pattern == "uptrend":
        # 上升趋势：价格逐步上涨
        prices = [base_price * (1.02 ** i) + np.random.normal(0, base_price * 0.01) for i in range(length)]
    elif price_pattern == "downtrend":
        # 下降趋势：价格逐步下跌
        prices = [base_price * (0.98 ** i) + np.random.normal(0, base_price * 0.01) for i in range(length)]
    elif price_pattern == "sideways":
        # 横盘整理：价格围绕基准波动
        prices = [base_price + np.random.normal(0, base_price * 0.02) for _ in range(length)]
    elif price_pattern == "volatile":
        # 高波动：价格剧烈波动
        prices = []
        current_price = base_price
        for i in range(length):
            change = np.random.normal(0, 0.05)  # 5%标准差的随机变化
            current_price *= (1 + change)
            prices.append(max(current_price, 0.1))  # 确保价格为正
    else:  # mixed
        # 混合模式：前期上涨，后期下跌
        mid_point = length // 2
        prices = []
        for i in range(length):
            if i < mid_point:
                price = base_price * (1.03 ** i)  # 上涨阶段
            else:
                price = base_price * (1.03 ** mid_point) * (0.97 ** (i - mid_point))  # 下跌阶段
            prices.append(price + np.random.normal(0, base_price * 0.005))

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_ema_basic():
    """基础功能测试"""
    print("🧪 测试EMA基础功能...")

    # 创建简单测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]  # 线性增长
    })

    # 创建因子实例
    factor = EMA({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # EMA特点：对近期价格更敏感，应该比SMA更贴近最新价格
    ema3_values = result['EMA_3'].dropna()
    ema5_values = result['EMA_5'].dropna()

    if len(ema3_values) > 0 and len(ema5_values) > 0:
        print(f"   EMA_3样例: {ema3_values.iloc[:3].round(2).tolist()}")
        print(f"   EMA_5样例: {ema5_values.iloc[:3].round(2).tolist()}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查EMA特性：短周期EMA应该比长周期EMA更接近最新价格
    if len(ema3_values) > 5 and len(ema5_values) > 5:
        # 在上升趋势中，短周期EMA应该更高
        ema3_recent = ema3_values.iloc[0]  # 最新值（排序后在前面）
        ema5_recent = ema5_values.iloc[0]
        latest_price = test_data['hfq_close'].iloc[-1]

        ema3_closer = abs(ema3_recent - latest_price) <= abs(ema5_recent - latest_price)
        print(f"   EMA特性验证: EMA_3更接近最新价格 {'✅' if ema3_closer else '❌'}")

    return result


def test_ema_trend_patterns():
    """不同趋势模式测试"""
    print("\\n🧪 测试EMA不同趋势模式...")

    factor = EMA({"periods": [10, 20]})

    # 测试上升趋势
    uptrend_data = create_test_data(30, "uptrend")
    uptrend_result = factor.calculate_vectorized(uptrend_data)
    uptrend_ema10 = uptrend_result['EMA_10'].dropna()
    uptrend_ema20 = uptrend_result['EMA_20'].dropna()

    # 测试下降趋势
    downtrend_data = create_test_data(30, "downtrend")
    downtrend_result = factor.calculate_vectorized(downtrend_data)
    downtrend_ema10 = downtrend_result['EMA_10'].dropna()
    downtrend_ema20 = downtrend_result['EMA_20'].dropna()

    # 测试横盘趋势
    sideways_data = create_test_data(30, "sideways")
    sideways_result = factor.calculate_vectorized(sideways_data)
    sideways_ema10 = sideways_result['EMA_10'].dropna()

    # 测试高波动
    volatile_data = create_test_data(30, "volatile")
    volatile_result = factor.calculate_vectorized(volatile_data)
    volatile_ema10 = volatile_result['EMA_10'].dropna()

    print(f"   上升趋势: EMA_10变化 {uptrend_ema10.iloc[0] - uptrend_ema10.iloc[-1]:.2f}")
    print(f"   下降趋势: EMA_10变化 {downtrend_ema10.iloc[0] - downtrend_ema10.iloc[-1]:.2f}")
    print(f"   横盘趋势: EMA_10标准差 {sideways_ema10.std():.2f}")
    print(f"   高波动: EMA_10标准差 {volatile_ema10.std():.2f}")

    # 验证趋势特征
    uptrend_positive = uptrend_ema10.iloc[0] > uptrend_ema10.iloc[-1]  # 上升趋势EMA应该递增
    downtrend_negative = downtrend_ema10.iloc[0] < downtrend_ema10.iloc[-1]  # 下降趋势EMA应该递减
    volatile_variation = volatile_ema10.std() > sideways_ema10.std()  # 高波动EMA变异更大

    print(f"   趋势验证: 上升{'✅' if uptrend_positive else '❌'} 下降{'✅' if downtrend_negative else '❌'} 波动{'✅' if volatile_variation else '❌'}")


def test_ema_vs_sma():
    """EMA与SMA对比测试"""
    print("\\n🧪 测试EMA与SMA特性对比...")

    # 创建有明显趋势变化的数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        # 前10天平稳，后5天快速上涨
        'hfq_close': [100]*10 + [105, 110, 115, 120, 125]
    })

    factor = EMA({"periods": [5]})
    result = factor.calculate_vectorized(test_data)

    # 计算简单移动平均作为对比
    sma_5 = test_data['hfq_close'].rolling(5).mean()

    ema_5 = result['EMA_5']

    print("   价格变化点分析 (第11天开始上涨):")
    for i in [10, 11, 12, 13, 14]:  # 价格变化期
        price = test_data['hfq_close'].iloc[i]
        ema_val = ema_5.iloc[len(test_data) - 1 - i]  # 注意排序
        sma_val = sma_5.iloc[i]
        print(f"   第{i+1}天: 价格{price:.0f}, EMA_5={ema_val:.2f}, SMA_5={sma_val:.2f}")

    # EMA应该比SMA更快响应价格变化
    latest_price = test_data['hfq_close'].iloc[-1]
    latest_ema = ema_5.iloc[0]  # 最新值在前
    latest_sma = sma_5.iloc[-1]

    ema_closer = abs(latest_ema - latest_price) < abs(latest_sma - latest_price)
    print(f"   响应性验证: EMA比SMA更接近最新价格 {'✅' if ema_closer else '❌'}")


def test_ema_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试EMA边界情况...")

    factor = EMA({"periods": [10]})

    # 测试1: 价格完全平坦
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_close': [100.0] * 20
    })

    result1 = factor.calculate_vectorized(flat_data)
    flat_ema = result1['EMA_10'].dropna()
    all_equal = (flat_ema == 100.0).all() if len(flat_ema) > 0 else True
    print(f"   平坦价格测试: {'✅ EMA为常数' if all_equal else '❌ 应为常数'}")

    # 测试2: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-01-01', periods=5),
        'hfq_close': [100, 102, 104, 106, 108]
    })

    result2 = factor.calculate_vectorized(short_data)
    short_ema = result2['EMA_10'].dropna()
    print(f"   短数据测试: 计算出 {len(short_ema)} 个EMA值")

    # 测试3: 包含NaN价格数据
    nan_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [100, 102, np.nan, 106, 108, np.nan, 112, 114, 116, 118, np.nan, 122, 124, 126, 128]
    })

    result3 = factor.calculate_vectorized(nan_data)
    nan_ema = result3['EMA_10'].dropna()
    print(f"   NaN数据测试: 有效EMA值 {len(nan_ema)} 个")

    # 测试4: 极端价格跳跃
    jump_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [100, 101, 102, 103, 1000, 105, 106, 107, 108, 109]  # 第5天价格异常高
    })

    result4 = factor.calculate_vectorized(jump_data)
    jump_ema = result4['EMA_10'].dropna()
    if len(jump_ema) > 0:
        print(f"   价格跳跃测试: EMA范围 [{jump_ema.min():.1f}, {jump_ema.max():.1f}]")


def test_ema_performance():
    """性能测试"""
    print("\\n🧪 测试EMA性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000, "mixed")
    factor = EMA({"periods": [5, 10, 20, 60]})

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
    print("   EMA数值分布检查:")
    for period in [5, 10, 20, 60]:
        col_name = f'EMA_{period}'
        ema_values = result[col_name].dropna()
        if len(ema_values) > 0:
            print(f"   {period}日: 均值 {ema_values.mean():.2f}, 范围 [{ema_values.min():.2f}, {ema_values.max():.2f}], 完整度 {len(ema_values)/len(result):.1%}")


def run_all_tests():
    """运行所有测试"""
    print("📊 EMA因子模块化测试")
    print("=" * 50)

    try:
        test_ema_basic()
        test_ema_trend_patterns()
        test_ema_vs_sma()
        test_ema_edge_cases()
        test_ema_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()