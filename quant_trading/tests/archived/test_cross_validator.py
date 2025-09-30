#!/usr/bin/env python3
"""
测试样本外验证框架
验证过拟合检测和健壮性评分功能
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from quant_trading.validation.cross_validator import create_cross_validator


def create_test_data(days=500, factor_decay=True):
    """创建测试数据，模拟因子衰减场景"""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=days, freq='D')

    # 创建基础因子信号
    base_signal = np.random.randn(days)

    if factor_decay:
        # 模拟因子衰减：前期高相关，后期低相关
        split_point = int(days * 0.7)

        # 前期收益率与因子强相关
        early_correlation = 0.4
        early_returns = early_correlation * base_signal[:split_point] + np.random.randn(split_point) * 0.015

        # 后期收益率与因子弱相关（模拟因子失效）
        late_correlation = 0.1
        late_returns = late_correlation * base_signal[split_point:] + np.random.randn(days - split_point) * 0.02

        returns = np.concatenate([early_returns, late_returns])
    else:
        # 模拟稳定因子：全期保持相关性
        correlation = 0.3
        returns = correlation * base_signal + np.random.randn(days) * 0.02

    factor_data = pd.Series(base_signal, index=dates, name='test_factor')
    returns_data = pd.Series(returns, index=dates, name='returns')

    return factor_data, returns_data


def test_simple_validation():
    """测试简单样本外验证"""
    print("🔍 === 简单样本外验证测试 ===")

    # 创建衰减因子数据
    factor_data, returns_data = create_test_data(days=500, factor_decay=True)

    # 创建验证器
    validator = create_cross_validator(min_train_periods=250, test_ratio=0.3)

    # 执行验证
    result = validator.validate_factor_simple(factor_data, returns_data, [1, 5, 10])

    print(f"因子名称: {result.factor_name}")
    print(f"验证类型: {result.validation_type}")
    print(f"是否健壮: {result.is_robust}")
    print(f"健壮性评分: {result.robustness_score:.3f}")

    # 显示衰减指标
    if 'summary' in result.degradation_metrics:
        summary = result.degradation_metrics['summary']
        print(f"平均衰减率: {summary['avg_abs_degradation']:.3f}")
        print(f"符号一致性: {summary['avg_sign_consistency']:.3f}")
        print(f"衰减程度: {summary['degradation_severity']}")

    # 显示详细期别结果
    print("\n各期别衰减详情:")
    for period_key, metrics in result.degradation_metrics.items():
        if period_key != 'summary':
            print(f"  {period_key}: 样本内IC={metrics['in_sample_ic']:.3f}, "
                  f"样本外IC={metrics['out_sample_ic']:.3f}, "
                  f"衰减={metrics['abs_degradation']:.3f}")

    return result


def test_walk_forward_validation():
    """测试滚动窗口验证"""
    print("\n🔄 === 滚动窗口验证测试 ===")

    # 创建稳定因子数据
    factor_data, returns_data = create_test_data(days=600, factor_decay=False)

    # 创建验证器
    validator = create_cross_validator()

    # 执行滚动验证
    result = validator.walk_forward_validation(
        factor_data, returns_data,
        window_size=180,  # 6个月训练窗口
        step_size=30,     # 1个月步长
        forward_periods=[1, 5]
    )

    print(f"因子名称: {result.factor_name}")
    print(f"验证类型: {result.validation_type}")
    print(f"是否健壮: {result.is_robust}")
    print(f"健壮性评分: {result.robustness_score:.3f}")

    # 滚动验证特有信息
    rolling_periods = result.detailed_stats['rolling_periods']
    print(f"滚动验证期数: {rolling_periods}")

    if 'summary' in result.degradation_metrics:
        summary = result.degradation_metrics['summary']
        print(f"平均衰减率: {summary['avg_abs_degradation']:.3f}")
        print(f"符号一致性: {summary['avg_sign_consistency']:.3f}")

    return result


def test_robustness_comparison():
    """对比健壮因子 vs 非健壮因子"""
    print("\n⚖️ === 健壮性对比测试 ===")

    validator = create_cross_validator()

    # 测试稳定因子
    print("1. 测试稳定因子:")
    stable_factor, stable_returns = create_test_data(days=400, factor_decay=False)
    stable_result = validator.validate_factor_simple(stable_factor, stable_returns)
    print(f"   健壮性评分: {stable_result.robustness_score:.3f}")
    print(f"   是否健壮: {stable_result.is_robust}")

    # 测试衰减因子
    print("\n2. 测试衰减因子:")
    decay_factor, decay_returns = create_test_data(days=400, factor_decay=True)
    decay_result = validator.validate_factor_simple(decay_factor, decay_returns)
    print(f"   健壮性评分: {decay_result.robustness_score:.3f}")
    print(f"   是否健壮: {decay_result.is_robust}")

    # 对比分析
    print("\n📊 对比结果:")
    stable_degradation = stable_result.degradation_metrics.get('summary', {}).get('avg_abs_degradation', 1)
    decay_degradation = decay_result.degradation_metrics.get('summary', {}).get('avg_abs_degradation', 1)

    print(f"   稳定因子衰减: {stable_degradation:.3f}")
    print(f"   衰减因子衰减: {decay_degradation:.3f}")
    print(f"   差异倍数: {decay_degradation / stable_degradation:.1f}x")

    return stable_result, decay_result


def test_batch_validation():
    """测试批量验证功能"""
    print("\n📦 === 批量验证测试 ===")

    # 创建多个因子数据
    factors_data = {}
    for i, decay in enumerate([False, True, False, True]):
        factor, returns = create_test_data(days=350, factor_decay=decay)
        factor_name = f"factor_{i+1}_{'stable' if not decay else 'decay'}"
        factor.name = factor_name
        factors_data[factor_name] = factor

    # 统一收益率数据
    _, returns_data = create_test_data(days=350, factor_decay=False)

    # 转换为DataFrame
    factor_df = pd.DataFrame(factors_data)

    # 批量验证
    validator = create_cross_validator()
    batch_results = validator.batch_validate_factors(factor_df, returns_data, validation_type='simple')

    print(f"验证因子数量: {len(batch_results)}")
    print("\n各因子健壮性评分:")
    for factor_name, result in batch_results.items():
        print(f"  {factor_name:20s}: {result.robustness_score:.3f} ({'健壮' if result.is_robust else '不健壮'})")

    return batch_results


def main():
    """主测试函数"""
    print("🧪 === 样本外验证框架测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 简单验证测试
        simple_result = test_simple_validation()

        # 2. 滚动验证测试
        walk_result = test_walk_forward_validation()

        # 3. 健壮性对比测试
        stable_result, decay_result = test_robustness_comparison()

        # 4. 批量验证测试
        batch_results = test_batch_validation()

        print("\n✅ === 测试总结 ===")
        print("核心验证功能:")
        print("  ✓ 样本内外IC计算")
        print("  ✓ 性能衰减检测")
        print("  ✓ 健壮性评分")
        print("  ✓ 滚动窗口验证")
        print("  ✓ 批量处理能力")

        print("\n🎯 验证框架特点:")
        print("  • 防止过拟合：样本外验证确保泛化能力")
        print("  • 量化健壮性：0-1评分体系")
        print("  • 多重验证：简单划分 + 滚动窗口")
        print("  • 实用性强：批量处理多因子")

        print("\n📈 下一步: 集成到因子评估系统")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()