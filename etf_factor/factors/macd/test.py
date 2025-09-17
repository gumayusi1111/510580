"""
MACD测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import MACD


def create_test_data(length=50, price_pattern="uptrend") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_price = 100

    # 根据价格模式生成数据
    if price_pattern == "uptrend":
        # 上升趋势：价格持续上涨
        prices = [base_price * (1.015 ** i) + np.random.normal(0, base_price * 0.005) for i in range(length)]
    elif price_pattern == "downtrend":
        # 下降趋势：价格持续下跌
        prices = [base_price * (0.985 ** i) + np.random.normal(0, base_price * 0.005) for i in range(length)]
    elif price_pattern == "sideways":
        # 横盘整理：价格围绕基准波动
        prices = [base_price + 5 * np.sin(i * 0.3) + np.random.normal(0, base_price * 0.01) for i in range(length)]
    elif price_pattern == "volatile":
        # 高波动：价格剧烈波动
        prices = []
        current_price = base_price
        for i in range(length):
            change = np.random.normal(0, 0.03)  # 3%标准差的随机变化
            current_price *= (1 + change)
            prices.append(max(current_price, 0.1))
    elif price_pattern == "reversal":
        # 趋势反转：前半段上涨，后半段下跌
        mid_point = length // 2
        prices = []
        for i in range(length):
            if i < mid_point:
                price = base_price * (1.02 ** i)  # 上涨阶段
            else:
                peak_price = base_price * (1.02 ** mid_point)
                price = peak_price * (0.98 ** (i - mid_point))  # 下跌阶段
            prices.append(price + np.random.normal(0, base_price * 0.005))
    else:  # oscillating
        # 振荡模式：价格在两个水平间振荡
        prices = [base_price + 20 * np.sin(i * 0.4) + 10 * np.sin(i * 0.15) + np.random.normal(0, 2) for i in range(length)]

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'hfq_close': prices
    })


def test_macd_basic():
    """基础功能测试"""
    print("🧪 测试MACD基础功能...")

    # 创建足够长的测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 40,
        'trade_date': pd.date_range('2025-01-01', periods=40),
        'hfq_close': [100 + i * 0.5 + np.sin(i * 0.3) * 2 for i in range(40)]  # 带波动的上升趋势
    })

    # 创建因子实例
    factor = MACD()  # 使用默认参数 12, 26, 9

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 检查MACD各组件
    dif_values = result['MACD_DIF'].dropna()
    dea_values = result['MACD_DEA'].dropna()
    hist_values = result['MACD_HIST'].dropna()

    print(f"   MACD_DIF样例: {dif_values.iloc[:3].round(3).tolist()}")
    print(f"   MACD_DEA样例: {dea_values.iloc[:3].round(3).tolist()}")
    print(f"   MACD_HIST样例: {hist_values.iloc[:3].round(3).tolist()}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 验证MACD组件关系: HIST = DIF - DEA
    if len(dif_values) > 0 and len(dea_values) > 0 and len(hist_values) > 0:
        # 取前几个有效值进行验证
        for i in range(min(3, len(dif_values), len(dea_values), len(hist_values))):
            expected_hist = dif_values.iloc[i] - dea_values.iloc[i]
            actual_hist = hist_values.iloc[i]
            diff = abs(expected_hist - actual_hist)
            if diff < 0.01:  # 精度容差
                continue
            else:
                print(f"   ❌ HIST计算错误: 期望{expected_hist:.3f}, 实际{actual_hist:.3f}")
                break
        else:
            print("   ✅ MACD组件关系验证正确: HIST = DIF - DEA")

    return result


def test_macd_trend_patterns():
    """不同趋势模式测试"""
    print("\\n🧪 测试MACD不同趋势模式...")

    factor = MACD({"fast_period": 12, "slow_period": 26, "signal_period": 9})

    # 测试上升趋势
    uptrend_data = create_test_data(60, "uptrend")
    uptrend_result = factor.calculate_vectorized(uptrend_data)
    uptrend_dif = uptrend_result['MACD_DIF'].dropna()
    uptrend_hist = uptrend_result['MACD_HIST'].dropna()

    # 测试下降趋势
    downtrend_data = create_test_data(60, "downtrend")
    downtrend_result = factor.calculate_vectorized(downtrend_data)
    downtrend_dif = downtrend_result['MACD_DIF'].dropna()
    downtrend_hist = downtrend_result['MACD_HIST'].dropna()

    # 测试横盘震荡
    sideways_data = create_test_data(60, "sideways")
    sideways_result = factor.calculate_vectorized(sideways_data)
    sideways_dif = sideways_result['MACD_DIF'].dropna()
    sideways_hist = sideways_result['MACD_HIST'].dropna()

    # 测试趋势反转
    reversal_data = create_test_data(60, "reversal")
    reversal_result = factor.calculate_vectorized(reversal_data)
    reversal_dif = reversal_result['MACD_DIF'].dropna()
    reversal_hist = reversal_result['MACD_HIST'].dropna()

    print(f"   上升趋势: DIF均值 {uptrend_dif.mean():.3f}, HIST均值 {uptrend_hist.mean():.3f}")
    print(f"   下降趋势: DIF均值 {downtrend_dif.mean():.3f}, HIST均值 {downtrend_hist.mean():.3f}")
    print(f"   横盘震荡: DIF标准差 {sideways_dif.std():.3f}, HIST标准差 {sideways_hist.std():.3f}")
    print(f"   趋势反转: DIF范围 [{reversal_dif.min():.3f}, {reversal_dif.max():.3f}]")

    # 验证趋势特征
    uptrend_positive = uptrend_dif.mean() > 0  # 上升趋势DIF通常为正
    downtrend_negative = downtrend_dif.mean() < 0  # 下降趋势DIF通常为负
    sideways_oscillation = abs(sideways_dif.mean()) < sideways_dif.std()  # 震荡时均值接近0但有波动
    reversal_crossing = (reversal_dif > 0).any() and (reversal_dif < 0).any()  # 反转时DIF会穿越0轴

    print(f"   趋势验证: 上升{'✅' if uptrend_positive else '❌'} 下降{'✅' if downtrend_negative else '❌'} 震荡{'✅' if sideways_oscillation else '❌'} 反转{'✅' if reversal_crossing else '❌'}")


def test_macd_signals():
    """MACD信号测试"""
    print("\\n🧪 测试MACD交易信号...")

    # 创建明显趋势变化的数据
    test_data = create_test_data(80, "reversal")
    factor = MACD()
    result = factor.calculate_vectorized(test_data)

    dif = result['MACD_DIF'].dropna()
    dea = result['MACD_DEA'].dropna()
    hist = result['MACD_HIST'].dropna()

    # 检测金叉死叉信号 (DIF穿越DEA)
    # 金叉：DIF从下方穿越DEA向上
    # 死叉：DIF从上方穿越DEA向下

    golden_crosses = 0  # 金叉次数
    death_crosses = 0   # 死叉次数

    # 找出对齐的数据点
    common_idx = dif.index.intersection(dea.index)
    if len(common_idx) > 1:
        dif_aligned = dif[common_idx]
        dea_aligned = dea[common_idx]

        for i in range(1, len(dif_aligned)):
            prev_dif, curr_dif = dif_aligned.iloc[i-1], dif_aligned.iloc[i]
            prev_dea, curr_dea = dea_aligned.iloc[i-1], dea_aligned.iloc[i]

            # 金叉：前一期DIF<DEA, 当期DIF>=DEA
            if prev_dif < prev_dea and curr_dif >= curr_dea:
                golden_crosses += 1

            # 死叉：前一期DIF>DEA, 当期DIF<=DEA
            elif prev_dif > prev_dea and curr_dif <= curr_dea:
                death_crosses += 1

    # 检测柱状图信号 (HIST穿越0轴)
    zero_crosses = 0
    if len(hist) > 1:
        for i in range(1, len(hist)):
            if hist.iloc[i-1] * hist.iloc[i] < 0:  # 异号表示穿越0轴
                zero_crosses += 1

    print(f"   交易信号统计:")
    print(f"   金叉次数: {golden_crosses}")
    print(f"   死叉次数: {death_crosses}")
    print(f"   HIST零轴穿越次数: {zero_crosses}")

    # 验证信号合理性
    total_crosses = golden_crosses + death_crosses
    signal_reasonable = 2 <= total_crosses <= 10  # 在合理的信号频率范围内
    hist_active = zero_crosses >= total_crosses  # HIST通常比DIF/DEA交叉更频繁

    print(f"   信号验证: 频率合理{'✅' if signal_reasonable else '❌'} HIST活跃{'✅' if hist_active else '❌'}")


def test_macd_parameters():
    """不同参数配置测试"""
    print("\\n🧪 测试MACD不同参数配置...")

    test_data = create_test_data(80, "oscillating")

    # 测试不同的参数组合
    configs = [
        {"fast_period": 12, "slow_period": 26, "signal_period": 9},  # 标准配置
        {"fast_period": 5, "slow_period": 10, "signal_period": 5},   # 快速配置
        {"fast_period": 20, "slow_period": 50, "signal_period": 15}  # 慢速配置
    ]

    config_names = ["标准", "快速", "慢速"]

    for config, name in zip(configs, config_names):
        factor = MACD(config)
        result = factor.calculate_vectorized(test_data)

        dif = result['MACD_DIF'].dropna()
        hist = result['MACD_HIST'].dropna()

        print(f"   {name}配置({config['fast_period']},{config['slow_period']},{config['signal_period']}): DIF标准差 {dif.std():.3f}, HIST标准差 {hist.std():.3f}")

    # 验证参数效果：快速配置应该更敏感（标准差更大）
    standard_factor = MACD(configs[0])
    fast_factor = MACD(configs[1])

    standard_result = standard_factor.calculate_vectorized(test_data)
    fast_result = fast_factor.calculate_vectorized(test_data)

    standard_hist_std = standard_result['MACD_HIST'].dropna().std()
    fast_hist_std = fast_result['MACD_HIST'].dropna().std()

    faster_more_sensitive = fast_hist_std > standard_hist_std
    print(f"   参数验证: 快速配置更敏感 {'✅' if faster_more_sensitive else '❌'}")


def test_macd_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试MACD边界情况...")

    factor = MACD()

    # 测试1: 数据长度刚好够计算
    min_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 35,
        'trade_date': pd.date_range('2025-01-01', periods=35),
        'hfq_close': [100 + i * 0.1 for i in range(35)]
    })

    result1 = factor.calculate_vectorized(min_data)
    min_dif = result1['MACD_DIF'].dropna()
    print(f"   最小数据测试: 计算出 {len(min_dif)} 个DIF值")

    # 测试2: 价格完全平坦
    flat_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 50,
        'trade_date': pd.date_range('2025-01-01', periods=50),
        'hfq_close': [100.0] * 50
    })

    result2 = factor.calculate_vectorized(flat_data)
    flat_dif = result2['MACD_DIF'].dropna()
    flat_hist = result2['MACD_HIST'].dropna()

    all_zero_dif = (flat_dif.abs() < 0.001).all() if len(flat_dif) > 0 else True
    all_zero_hist = (flat_hist.abs() < 0.001).all() if len(flat_hist) > 0 else True

    print(f"   平坦价格测试: DIF接近0 {'✅' if all_zero_dif else '❌'} HIST接近0 {'✅' if all_zero_hist else '❌'}")

    # 测试3: 包含NaN价格数据
    nan_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 50,
        'trade_date': pd.date_range('2025-01-01', periods=50),
        'hfq_close': [100 + i * 0.2 if i % 5 != 0 else np.nan for i in range(50)]
    })

    result3 = factor.calculate_vectorized(nan_data)
    nan_dif = result3['MACD_DIF'].dropna()
    print(f"   NaN数据测试: 有效DIF值 {len(nan_dif)} 个")

    # 测试4: 极端价格变化
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 50,
        'trade_date': pd.date_range('2025-01-01', periods=50),
        'hfq_close': [100 if i < 25 else 200 for i in range(50)]  # 中途价格翻倍
    })

    result4 = factor.calculate_vectorized(extreme_data)
    extreme_hist = result4['MACD_HIST'].dropna()
    if len(extreme_hist) > 0:
        print(f"   极端变化测试: HIST范围 [{extreme_hist.min():.2f}, {extreme_hist.max():.2f}]")


def test_macd_performance():
    """性能测试"""
    print("\\n🧪 测试MACD性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000, "oscillating")
    factor = MACD()

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
    dif_count = result['MACD_DIF'].count()
    dea_count = result['MACD_DEA'].count()
    hist_count = result['MACD_HIST'].count()

    print(f"   数据完整度: DIF {dif_count/len(result):.1%}, DEA {dea_count/len(result):.1%}, HIST {hist_count/len(result):.1%}")

    # 检查MACD数值分布
    dif_values = result['MACD_DIF'].dropna()
    dea_values = result['MACD_DEA'].dropna()
    hist_values = result['MACD_HIST'].dropna()

    print(f"   数值分布: DIF标准差 {dif_values.std():.3f}, DEA标准差 {dea_values.std():.3f}, HIST标准差 {hist_values.std():.3f}")


def run_all_tests():
    """运行所有测试"""
    print("📊 MACD因子模块化测试")
    print("=" * 50)

    try:
        test_macd_basic()
        test_macd_trend_patterns()
        test_macd_signals()
        test_macd_parameters()
        test_macd_edge_cases()
        test_macd_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()