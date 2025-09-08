"""
基础使用示例
演示如何使用因子库进行计算
"""

import sys
import os
sys.path.append('..')

from src import VectorizedEngine

def main():
    """基础使用示例"""
    
    print("🚀 ETF因子库基础使用示例")
    print("=" * 50)
    
    # 1. 创建向量化引擎
    print("1. 初始化引擎...")
    engine = VectorizedEngine(
        data_dir="../data",
        output_dir="factor_data"
    )
    
    # 2. 查看引擎信息
    info = engine.get_engine_info()
    print(f"   - 已注册因子: {info['factor_count']} 个")
    print(f"   - 可用因子: {info['registered_factors'][:3]}...")  # 只显示前3个
    
    # 3. 计算单个因子 (需要先实现SMA因子)
    print("\n2. 计算单个因子...")
    try:
        # 这里会在实现SMA因子后运行
        # sma_result = engine.calculate_single_factor("SMA")
        # print(f"   - SMA计算完成，数据行数: {len(sma_result)}")
        print("   - 待实现因子后测试...")
    except Exception as e:
        print(f"   - 因子计算: {e}")
    
    # 4. 批量计算 (待实现)
    print("\n3. 批量计算...")
    try:
        # factors = ["SMA", "EMA"]
        # results = engine.calculate_batch_factors(factors)
        # print(f"   - 批量计算完成: {len(results)} 个因子")
        print("   - 待实现因子后测试...")
    except Exception as e:
        print(f"   - 批量计算: {e}")
    
    # 5. 保存结果 (待实现)
    print("\n4. 保存结果...")
    print("   - 待实现因子后测试...")
    
    print("\n✅ 基础示例完成")
    print("💡 下一步: 实现具体的因子 (如SMA)")

if __name__ == "__main__":
    main()