"""
VOLUME_RATIO测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import VOLUME_RATIO
from validation import VolumeRatioValidation


def test_volumeratio_basic():
    print("🧪 测试VOLUME_RATIO基础功能...")

    # 创建测试数据（模拟成交量变化）
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'vol': [1000, 1200, 800, 1500, 900,   # 前5日：平均1080
                2000, 1100, 1300, 950, 1800,  # 第6-10日：一些放量
                600, 2500, 1000, 1400, 1600]  # 第11-15日：缩量和放量
    })

    factor = VOLUME_RATIO({"period": 5})
    result = factor.calculate_vectorized(test_data)

    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    print(f"   VOLUME_RATIO_5样例: {result['VOLUME_RATIO_5'].iloc[-5:].tolist()}")

    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 手工验证最新数据点
    # 第15日量比 = 1600 / 前5日(600,2500,1000,1400)平均 = 1600 / 1375 ≈ 1.164
    recent_volumes = test_data['vol'].iloc[-6:-1]  # 第10-14日成交量
    manual_avg = recent_volumes.mean()
    current_vol = test_data['vol'].iloc[-1]
    manual_ratio = current_vol / manual_avg

    print(f"   手工验证量比: {manual_ratio:.4f}")
    print(f"   因子结果量比: {result['VOLUME_RATIO_5'].iloc[-1]:.4f}")

    # 展示一些解释
    print(f"   量比解释:")
    latest_ratios = result['VOLUME_RATIO_5'].iloc[-3:].tolist()
    for i, ratio in enumerate(latest_ratios):
        if ratio > 2:
            desc = "异常放量"
        elif ratio > 1.5:
            desc = "明显放量"
        elif ratio > 1:
            desc = "适度放量"
        elif ratio > 0.5:
            desc = "适度缩量"
        else:
            desc = "明显缩量"
        print(f"     倒数第{3-i}日: {ratio:.2f} ({desc})")

    return result


def test_volumeratio_validation():
    print("🧪 测试VOLUME_RATIO验证功能...")

    # 创建更长的随机数据用于统计验证
    np.random.seed(42)
    n_days = 50
    base_volume = 1000

    # 生成带有不同活跃度的成交量序列
    volumes = []
    for i in range(n_days):
        if i < 20:
            # 正常成交量阶段
            daily_vol = base_volume * (0.8 + 0.4 * np.random.random())
        elif i < 35:
            # 活跃成交量阶段
            daily_vol = base_volume * (1.2 + 0.8 * np.random.random())
        else:
            # 低迷成交量阶段
            daily_vol = base_volume * (0.3 + 0.4 * np.random.random())
        volumes.append(max(daily_vol, 100))  # 确保最小成交量

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * n_days,
        'trade_date': pd.date_range('2025-01-01', periods=n_days),
        'vol': volumes
    })

    factor = VOLUME_RATIO()  # 使用默认参数
    result = factor.calculate_vectorized(test_data)

    # 运行完整验证
    is_valid, validation_results = VolumeRatioValidation.run_full_validation(
        test_data, result, factor.params
    )

    print(f"   整体验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    for test_name, passed, message in validation_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {message}")

    return result


def test_volumeratio_edge_cases():
    print("🧪 测试VOLUME_RATIO边界情况...")

    # 测试恒定成交量
    constant_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'vol': [1000] * 15  # 恒定成交量
    })

    factor = VOLUME_RATIO()
    result_constant = factor.calculate_vectorized(constant_data)

    # 恒定成交量时，量比应该接近1
    constant_ratios = result_constant['VOLUME_RATIO_5'].dropna()
    if len(constant_ratios) > 0:
        avg_ratio = constant_ratios.mean()
        constant_check = abs(avg_ratio - 1.0) < 0.1
        print(f"   恒定成交量量比: {avg_ratio:.3f} ({'✅ 接近1' if constant_check else '❌ 异常'})")

    # 测试零成交量情况
    zero_volume_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'vol': [0, 0, 0, 0, 0, 1000, 0, 0, 2000, 0]  # 大部分为零，少数非零
    })

    try:
        result_zero = factor.calculate_vectorized(zero_volume_data)
        zero_ratios = result_zero['VOLUME_RATIO_5'].dropna()
        print(f"   零成交量处理: 生成{len(zero_ratios)}个有效量比值")

        # 测试极端放量
        extreme_data = pd.DataFrame({
            'ts_code': ['510580.SH'] * 12,
            'trade_date': pd.date_range('2025-01-01', periods=12),
            'vol': [100, 100, 100, 100, 100, 100,  # 前6天低量
                    10000, 100, 100, 100, 100, 100]  # 第7天极端放量
        })

        result_extreme = factor.calculate_vectorized(extreme_data)
        extreme_ratio = result_extreme['VOLUME_RATIO_5'].iloc[6]  # 第7天的量比
        print(f"   极端放量量比: {extreme_ratio:.1f}倍 ({'✅ 合理' if 10 <= extreme_ratio <= 100 else '⚠️ 异常'})")

        # 测试不同周期参数
        factor_short = VOLUME_RATIO({"period": 3})
        result_short = factor_short.calculate_vectorized(test_data := pd.DataFrame({
            'ts_code': ['510580.SH'] * 10,
            'trade_date': pd.date_range('2025-01-01', periods=10),
            'vol': [500, 600, 700, 1000, 1200, 800, 1500, 900, 1100, 2000]
        }))

        factor_long = VOLUME_RATIO({"period": 7})
        result_long = factor_long.calculate_vectorized(test_data)

        # 短周期量比通常更敏感
        short_volatility = result_short['VOLUME_RATIO_3'].std()
        long_volatility = result_long['VOLUME_RATIO_7'].std()

        volatility_check = short_volatility >= long_volatility * 0.8  # 允许一定偏差
        print(f"   周期敏感性: 3日波动={short_volatility:.3f}, 7日波动={long_volatility:.3f} ({'✅ 符合预期' if volatility_check else '⚠️ 特殊情况'})")

    except Exception as e:
        print(f"   边界测试失败: {e}")

    return result_constant


def test_volumeratio_different_periods():
    print("🧪 测试VOLUME_RATIO不同周期参数...")

    # 创建具有周期性成交量变化的测试数据
    n_days = 30
    volumes = []
    base_vol = 1000

    for i in range(n_days):
        # 创建周期性变化 + 随机噪声
        cycle_factor = 1 + 0.5 * np.sin(i * 2 * np.pi / 7)  # 7天周期
        noise_factor = 0.8 + 0.4 * np.random.random()
        daily_vol = base_vol * cycle_factor * noise_factor
        volumes.append(daily_vol)

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * n_days,
        'trade_date': pd.date_range('2025-01-01', periods=n_days),
        'vol': volumes
    })

    periods_to_test = [3, 5, 10, 15]
    results = {}

    for period in periods_to_test:
        factor = VOLUME_RATIO({"period": period})
        result = factor.calculate_vectorized(test_data)
        results[period] = result

        ratio_col = f'VOLUME_RATIO_{period}'
        ratio_values = result[ratio_col].dropna()

        if len(ratio_values) > 0:
            avg_ratio = ratio_values.mean()
            max_ratio = ratio_values.max()
            min_ratio = ratio_values.min()
            print(f"   VOLUME_RATIO_{period}: 平均={avg_ratio:.2f}, 范围=[{min_ratio:.2f}, {max_ratio:.2f}]")

    # 验证因子信息
    factor_info = VOLUME_RATIO({"period": 5}).get_factor_info()
    print(f"   因子信息: {factor_info['name']} - {factor_info['description']}")
    print(f"   计算公式: {factor_info['formula']}")

    return results


def test_volumeratio_market_analysis():
    print("🧪 测试VOLUME_RATIO市场分析...")

    # 创建模拟不同市场状态的成交量数据
    market_phases = [
        ('正常交易', 20, 1000, 0.3),     # (阶段名, 天数, 基础量, 波动率)
        ('活跃期', 15, 2000, 0.5),       # 成交量翻倍，波动加大
        ('冷清期', 10, 500, 0.2),        # 成交量减半，波动减小
        ('异动期', 10, 1500, 1.0),       # 成交量不稳定，大幅波动
        ('恢复期', 15, 1200, 0.4)        # 成交量恢复，波动正常
    ]

    all_volumes = []
    phase_info = []
    start_idx = 0

    for phase_name, days, base_vol, volatility in market_phases:
        phase_volumes = []
        for _ in range(days):
            noise = np.random.normal(1, volatility)
            daily_vol = max(base_vol * abs(noise), 50)  # 确保最小成交量
            phase_volumes.append(daily_vol)

        all_volumes.extend(phase_volumes)
        phase_info.append((phase_name, start_idx, start_idx + days, base_vol))
        start_idx += days

    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * len(all_volumes),
        'trade_date': pd.date_range('2025-01-01', periods=len(all_volumes)),
        'vol': all_volumes
    })

    factor = VOLUME_RATIO({"period": 5})
    result = factor.calculate_vectorized(test_data)

    # 分析各阶段的量比特征
    print("   各市场阶段的量比特征:")
    for phase_name, start_idx, end_idx, expected_base in phase_info:
        phase_ratios = result['VOLUME_RATIO_5'].iloc[start_idx:end_idx].dropna()
        if len(phase_ratios) > 0:
            avg_ratio = phase_ratios.mean()
            max_ratio = phase_ratios.max()
            volatility = phase_ratios.std()

            activity_level = "高" if avg_ratio > 1.5 else "中" if avg_ratio > 0.7 else "低"
            print(f"     {phase_name}: 平均量比={avg_ratio:.2f}, 最大={max_ratio:.2f}, 波动={volatility:.2f} (活跃度: {activity_level})")

    # 分析异常量比事件
    all_ratios = result['VOLUME_RATIO_5'].dropna()

    # 定义量比事件
    extreme_high = (all_ratios > 3).sum()    # 极端放量
    high_volume = (all_ratios > 1.5).sum()   # 明显放量
    normal_volume = ((all_ratios >= 0.7) & (all_ratios <= 1.5)).sum()  # 正常交易
    low_volume = (all_ratios < 0.7).sum()    # 明显缩量

    total_days = len(all_ratios)
    print("   量比事件统计:")
    print(f"     极端放量(>3倍): {extreme_high}天 ({extreme_high/total_days:.1%})")
    print(f"     明显放量(>1.5倍): {high_volume}天 ({high_volume/total_days:.1%})")
    print(f"     正常交易(0.7-1.5倍): {normal_volume}天 ({normal_volume/total_days:.1%})")
    print(f"     明显缩量(<0.7倍): {low_volume}天 ({low_volume/total_days:.1%})")

    # 寻找连续放量/缩量模式
    consecutive_high = 0
    consecutive_low = 0
    current_high_streak = 0
    current_low_streak = 0

    for ratio in all_ratios:
        if ratio > 1.5:
            current_high_streak += 1
            current_low_streak = 0
            consecutive_high = max(consecutive_high, current_high_streak)
        elif ratio < 0.7:
            current_low_streak += 1
            current_high_streak = 0
            consecutive_low = max(consecutive_low, current_low_streak)
        else:
            current_high_streak = 0
            current_low_streak = 0

    print(f"   连续模式: 最长连续放量={consecutive_high}天, 最长连续缩量={consecutive_low}天")

    return result


def run_all_tests():
    print("📊 量比因子模块化测试")
    print("=" * 50)

    try:
        test_volumeratio_basic()
        print()
        test_volumeratio_validation()
        print()
        test_volumeratio_edge_cases()
        print()
        test_volumeratio_different_periods()
        print()
        test_volumeratio_market_analysis()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()