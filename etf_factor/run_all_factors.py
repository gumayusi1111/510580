#!/usr/bin/env python3
"""
运行所有因子计算的脚本
根据用户要求生成完整的ETF因子数据
"""

import os
import sys
import time
from datetime import datetime

# 添加当前目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.engine import VectorizedEngine


def main():
    print("🚀 开始运行所有ETF因子计算...")
    print("=" * 60)

    start_time = time.time()

    # 初始化引擎，指向510580数据
    data_dir = "../data_collection/data/510580"
    output_dir = "factor_data"

    print(f"📂 数据目录: {data_dir}")
    print(f"📝 输出目录: {output_dir}")
    print()

    try:
        # 创建引擎
        engine = VectorizedEngine(data_dir=data_dir, output_dir=output_dir)

        # 获取所有发现的因子
        all_factors = list(engine.factors.keys())
        if not all_factors:
            print("❌ 未发现任何因子！")
            return

        print(f"🔍 发现因子总数: {len(all_factors)}")
        print(f"📋 因子列表: {', '.join(all_factors)}")
        print()

        # 批量计算所有因子
        print("⚡ 开始批量计算所有因子...")
        results = engine.calculate_batch_factors(
            factor_names=all_factors,
            data_type="hfq",  # 使用后复权数据
            use_cache=True
        )

        print(f"✅ 计算完成! 成功计算 {len(results)} 个因子")
        print()

        # 保存结果 - 使用完整模式保存所有因子到一个文件
        print("💾 保存计算结果...")
        saved_files = engine.save_factor_results(results, output_type="complete")

        for file_path in saved_files:
            print(f"   ✅ 保存: {file_path}")

        # 也保存单个因子文件
        print("\n💾 保存单个因子文件...")
        individual_files = engine.save_factor_results(results, output_type="single")
        print(f"   ✅ 保存了 {len(individual_files)} 个单个因子文件")

        # 显示执行统计
        end_time = time.time()
        execution_time = end_time - start_time

        print("\n" + "=" * 60)
        print("📊 执行统计:")
        print(f"   ⏱️  执行时间: {execution_time:.2f} 秒")
        print(f"   🔢 处理因子数: {len(results)}")
        print(f"   📁 保存文件数: {len(saved_files) + len(individual_files)}")
        print(f"   ⚡ 平均速度: {len(results)/execution_time:.2f} 因子/秒")

        # 显示部分结果预览
        print("\n📋 计算结果预览:")
        for factor_name, data in list(results.items())[:5]:  # 显示前5个
            print(f"   📈 {factor_name}: {len(data)} 行, 列 {list(data.columns)}")

        if len(results) > 5:
            print(f"   ... 还有 {len(results) - 5} 个因子")

        print("\n🎉 所有因子计算完成！")
        print(f"🎯 完整结果已保存到: {output_dir}/")

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)