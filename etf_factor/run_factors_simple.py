#!/usr/bin/env python3
"""
简化版因子计算脚本 - 重用缓存并保存单个因子
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
    print("🚀 运行因子计算 (使用缓存)...")
    print("=" * 50)

    start_time = time.time()

    # 初始化引擎
    data_dir = "../data_collection/data/510580"
    output_dir = "factor_data"

    print(f"📂 数据目录: {data_dir}")
    print(f"📝 输出目录: {output_dir}")

    try:
        # 创建引擎
        engine = VectorizedEngine(data_dir=data_dir, output_dir=output_dir)

        # 获取所有因子
        all_factors = list(engine.factors.keys())
        print(f"🔍 发现 {len(all_factors)} 个因子")

        # 批量计算(会使用缓存)
        print("⚡ 批量计算所有因子(使用缓存)...")
        results = engine.calculate_batch_factors(
            factor_names=all_factors,
            data_type="hfq",
            use_cache=True
        )

        print(f"✅ 获取到 {len(results)} 个因子结果")

        # 只保存单个因子文件
        print("💾 保存单个因子文件...")
        individual_files = engine.save_factor_results(results, output_type="single")

        print(f"   ✅ 成功保存 {len(individual_files)} 个因子文件")

        # 显示文件列表
        print("\n📁 已保存的因子文件:")
        for file_path in individual_files[:10]:  # 显示前10个
            filename = os.path.basename(file_path)
            print(f"   📈 {filename}")

        if len(individual_files) > 10:
            print(f"   ... 还有 {len(individual_files) - 10} 个文件")

        # 执行统计
        end_time = time.time()
        execution_time = end_time - start_time

        print("\n" + "=" * 50)
        print("📊 执行统计:")
        print(f"   ⏱️  执行时间: {execution_time:.2f} 秒")
        print(f"   🔢 处理因子数: {len(results)}")
        print(f"   📁 保存文件数: {len(individual_files)}")

        print(f"\n🎉 完成! 因子数据已保存到: {output_dir}/single/")

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)