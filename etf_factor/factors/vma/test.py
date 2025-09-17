"""
VMA测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import VMA


def create_test_data(length=20, volume_pattern="normal") -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2025-01-01', periods=length)
    base_volume = 100000  # 基础成交量10万股

    # 根据成交量模式生成数据
    if volume_pattern == "normal":
        # 正常波动：成交量在基础值附近波动
        volumes = [base_volume + np.random.normal(0, base_volume * 0.2) for _ in range(length)]
        volumes = [max(vol, 0) for vol in volumes]  # 确保非负
    elif volume_pattern == "trending":
        # 趋势性：成交量逐渐增长
        volumes = [base_volume * (1 + i * 0.05) + np.random.normal(0, base_volume * 0.1) for i in range(length)]
        volumes = [max(vol, 0) for vol in volumes]
    elif volume_pattern == "volatile":
        # 高波动：成交量剧烈波动
        volumes = []
        for i in range(length):
            if i % 3 == 0:  # 每3天一个高峰
                vol = base_volume * (2 + np.random.uniform(0, 1))
            else:
                vol = base_volume * (0.3 + np.random.uniform(0, 0.4))
            volumes.append(max(vol, 0))
    elif volume_pattern == "low_activity":
        # 低活跃：成交量很小且变化不大
        volumes = [base_volume * 0.1 + np.random.normal(0, base_volume * 0.02) for _ in range(length)]
        volumes = [max(vol, 0) for vol in volumes]
    else:  # mixed
        # 混合模式：前期高成交量，后期低成交量
        mid_point = length // 2
        volumes = []
        for i in range(length):
            if i < mid_point:
                vol = base_volume * 2 + np.random.normal(0, base_volume * 0.3)
            else:
                vol = base_volume * 0.5 + np.random.normal(0, base_volume * 0.1)
            volumes.append(max(vol, 0))

    return pd.DataFrame({
        'ts_code': ['510580.SH'] * length,
        'trade_date': dates,
        'vol': volumes
    })


def test_vma_basic():
    """基础功能测试"""
    print("🧪 测试VMA基础功能...")

    # 创建简单测试数据，方便手工验证
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'vol': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]  # 递增成交量
    })

    # 创建因子实例
    factor = VMA({"periods": [3, 5]})

    # 计算结果
    result = factor.calculate_vectorized(test_data)

    # 显示结果
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")

    # 手工验证VMA_3第3行（索引2）: (100+200+300)/3 = 200
    # VMA_5第5行（索引4）: (100+200+300+400+500)/5 = 300
    manual_vma3_idx2 = (100 + 200 + 300) / 3
    manual_vma5_idx4 = (100 + 200 + 300 + 400 + 500) / 5

    print(f"   手工验证VMA_3[2]: {manual_vma3_idx2:.1f}, 计算结果: {result['VMA_3'].iloc[2]:.1f}")
    print(f"   手工验证VMA_5[4]: {manual_vma5_idx4:.1f}, 计算结果: {result['VMA_5'].iloc[4]:.1f}")

    # 验证结果
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")

    # 检查VMA值都为正数
    vma3_positive = (result['VMA_3'] >= 0).all()
    vma5_positive = (result['VMA_5'] >= 0).all()
    print(f"   正数检查: VMA_3 {'✅' if vma3_positive else '❌'} VMA_5 {'✅' if vma5_positive else '❌'}")

    return result


def test_vma_volume_patterns():
    """不同成交量模式测试"""
    print("\\n🧪 测试VMA不同成交量模式...")

    factor = VMA({"periods": [5, 10]})

    # 测试正常波动
    normal_data = create_test_data(20, "normal")
    normal_result = factor.calculate_vectorized(normal_data)
    normal_vma = normal_result['VMA_5'].dropna()

    # 测试趋势性增长
    trending_data = create_test_data(20, "trending")
    trending_result = factor.calculate_vectorized(trending_data)
    trending_vma = trending_result['VMA_5'].dropna()

    # 测试高波动
    volatile_data = create_test_data(20, "volatile")
    volatile_result = factor.calculate_vectorized(volatile_data)
    volatile_vma = volatile_result['VMA_5'].dropna()

    # 测试低活跃度
    low_activity_data = create_test_data(20, "low_activity")
    low_activity_result = factor.calculate_vectorized(low_activity_data)
    low_activity_vma = low_activity_result['VMA_5'].dropna()

    print(f"   正常波动: 平均VMA {normal_vma.mean():.0f}, 标准差 {normal_vma.std():.0f}")
    print(f"   趋势增长: 平均VMA {trending_vma.mean():.0f}, 最大值 {trending_vma.max():.0f}")
    print(f"   高波动: 平均VMA {volatile_vma.mean():.0f}, 变异系数 {volatile_vma.std()/volatile_vma.mean():.2f}")
    print(f"   低活跃: 平均VMA {low_activity_vma.mean():.0f}, 最大值 {low_activity_vma.max():.0f}")

    # 验证模式特征
    trending_growth = trending_vma.max() > normal_vma.max()  # 趋势增长应该有更高峰值
    volatile_variation = (volatile_vma.std() / volatile_vma.mean()) > (normal_vma.std() / normal_vma.mean())  # 高波动应该变异系数更大
    low_activity_small = low_activity_vma.mean() < normal_vma.mean()  # 低活跃度应该均值更小

    print(f"   模式验证: 趋势增长{'✅' if trending_growth else '❌'} 高波动{'✅' if volatile_variation else '❌'} 低活跃{'✅' if low_activity_small else '❌'}")


def test_vma_edge_cases():
    """边界情况测试"""
    print("\\n🧪 测试VMA边界情况...")

    factor = VMA({"periods": [5]})

    # 测试1: 零成交量数据
    zero_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'vol': [0.0] * 10
    })

    result1 = factor.calculate_vectorized(zero_data)
    zero_vma = result1['VMA_5'].dropna()
    all_zero = (zero_vma == 0).all() if len(zero_vma) > 0 else True
    print(f"   零成交量测试: {'✅ VMA为0' if all_zero else '❌ 应为0'}")

    # 测试2: 极大成交量差异
    extreme_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'vol': [1, 1, 1, 1, 1000000, 1, 1, 1, 1, 1]  # 第5天成交量异常大
    })

    result2 = factor.calculate_vectorized(extreme_data)
    extreme_vma = result2['VMA_5'].dropna()
    if len(extreme_vma) > 0:
        max_vma = extreme_vma.max()
        min_vma = extreme_vma.min()
        print(f"   极值成交量测试: VMA范围 [{min_vma:.0f}, {max_vma:.0f}]")

    # 测试3: 数据长度不足
    short_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 3,
        'trade_date': pd.date_range('2025-01-01', periods=3),
        'vol': [100, 200, 300]
    })

    result3 = factor.calculate_vectorized(short_data)
    short_vma = result3['VMA_5'].dropna()
    print(f"   短数据测试: 计算出 {len(short_vma)} 个VMA值")

    # 测试4: 包含NaN的成交量数据
    nan_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'vol': [100, 200, np.nan, 400, 500, np.nan, 700, 800, 900, 1000]
    })

    result4 = factor.calculate_vectorized(nan_data)
    nan_vma = result4['VMA_5'].dropna()
    has_results = len(nan_vma) > 0
    print(f"   NaN数据测试: {'✅ 有结果' if has_results else '❌ 无结果'}, 有效值数量: {len(nan_vma)}")


def test_vma_formula_validation():
    """VMA公式验证测试"""
    print("\\n🧪 测试VMA公式验证...")

    # 创建简单数据验证算法
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 8,
        'trade_date': pd.date_range('2025-01-01', periods=8),
        'vol': [100, 200, 300, 400, 500, 600, 700, 800]
    })

    factor = VMA({"periods": [3]})
    result = factor.calculate_vectorized(test_data)

    # 手工验证VMA_3计算
    print("   手工验证VMA_3计算:")
    for i in range(2, len(test_data)):  # 从第3行开始有足够数据
        volumes = test_data['vol'].iloc[max(0, i-2):i+1].tolist()
        expected_vma = sum(volumes) / len(volumes)
        actual_vma = result['VMA_3'].iloc[i]

        print(f"   第{i+1}行: 成交量{volumes} → 期望VMA {expected_vma:.1f}, 实际VMA {actual_vma:.1f}")

        diff = abs(expected_vma - actual_vma)
        if diff > 0.01:
            print(f"   ❌ 差异过大: {diff:.3f}")
            break
    else:
        print("   ✅ VMA公式计算完全正确")


def test_vma_performance():
    """性能测试"""
    print("\\n🧪 测试VMA性能...")

    import time

    # 创建大量数据
    large_data = create_test_data(1000, "normal")
    factor = VMA({"periods": [5, 10, 20, 60]})

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
        col_name = f'VMA_{period}'
        non_null_count = result[col_name].count()
        total_count = len(result)
        completeness = non_null_count / total_count if total_count > 0 else 1
        print(f"   {period}日数据完整度: {completeness:.1%}")

    # 检查VMA值的合理性
    print("   VMA数值合理性检查:")
    for period in [5, 10, 20, 60]:
        col_name = f'VMA_{period}'
        vma_values = result[col_name].dropna()
        if len(vma_values) > 0:
            print(f"   {period}日: 均值 {vma_values.mean():.0f}, 最大值 {vma_values.max():.0f}, 最小值 {vma_values.min():.0f}")


def run_all_tests():
    """运行所有测试"""
    print("📊 VMA因子模块化测试")
    print("=" * 50)

    try:
        test_vma_basic()
        test_vma_volume_patterns()
        test_vma_edge_cases()
        test_vma_formula_validation()
        test_vma_performance()

        print("\\n✅ 所有测试完成")

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()