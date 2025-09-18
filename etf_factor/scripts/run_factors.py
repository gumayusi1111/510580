#!/usr/bin/env python3
"""
ETF因子计算脚本
支持完整计算和快速模式（使用缓存）
"""

import os
import sys
import time
import argparse

# 添加父目录到系统路径以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# ruff: noqa: E402 - 导入必须在路径修改后
from src.engine import VectorizedEngine


def main():
    parser = argparse.ArgumentParser(description='ETF因子计算脚本')
    parser.add_argument('--simple', action='store_true',
                       help='简化模式：仅使用缓存和保存单个因子文件')
    parser.add_argument('--data-dir', type=str,
                       default='../../data_collection/data/510580',
                       help='数据目录路径')
    parser.add_argument('--output-dir', type=str,
                       default='../factor_data',
                       help='输出目录路径')

    args = parser.parse_args()

    mode_name = "简化模式" if args.simple else "完整模式"
    print(f"🚀 开始运行ETF因子计算 - {mode_name}...")
    print("=" * 60)

    start_time = time.time()

    print(f"📂 数据目录: {args.data_dir}")
    print(f"📝 输出目录: {args.output_dir}")
    print()

    try:
        # 创建引擎
        engine = VectorizedEngine(data_dir=args.data_dir, output_dir=args.output_dir)

        # 获取所有发现的因子
        all_factors = list(engine.factors.keys())
        if not all_factors:
            print("❌ 未发现任何因子！")
            return False

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

        # 保存结果
        saved_files = []

        if args.simple:
            # 简化模式：只保存单个因子文件
            print("💾 保存单个因子文件...")
            individual_files = engine.save_factor_results(results, output_type="single")
            saved_files.extend(individual_files)
            print(f"   ✅ 成功保存 {len(individual_files)} 个因子文件")

            # 显示部分文件列表
            print("\n📁 已保存的因子文件:")
            for file_path in individual_files[:10]:  # 显示前10个
                filename = os.path.basename(file_path)
                print(f"   📈 {filename}")

            if len(individual_files) > 10:
                print(f"   ... 还有 {len(individual_files) - 10} 个文件")

        else:
            # 完整模式：保存完整数据集和单个因子文件
            print("💾 保存完整数据集...")
            complete_files = engine.save_factor_results(results, output_type="complete")
            saved_files.extend(complete_files)

            for file_path in complete_files:
                print(f"   ✅ 保存: {file_path}")

            print("\n💾 保存单个因子文件...")
            individual_files = engine.save_factor_results(results, output_type="single")
            saved_files.extend(individual_files)
            print(f"   ✅ 保存了 {len(individual_files)} 个单个因子文件")

        # 显示执行统计
        end_time = time.time()
        execution_time = end_time - start_time

        print("\n" + "=" * 60)
        print("📊 执行统计:")
        print(f"   ⏱️  执行时间: {execution_time:.2f} 秒")
        print(f"   🔢 处理因子数: {len(results)}")
        print(f"   📁 保存文件数: {len(saved_files)}")
        print(f"   ⚡ 平均速度: {len(results)/execution_time:.2f} 因子/秒")

        # 显示部分结果预览
        if not args.simple:
            print("\n📋 计算结果预览:")
            for factor_name, data in list(results.items())[:5]:  # 显示前5个
                print(f"   📈 {factor_name}: {len(data)} 行, 列 {list(data.columns)}")

            if len(results) > 5:
                print(f"   ... 还有 {len(results) - 5} 个因子")

        print("\n🎉 所有因子计算完成！")
        if args.simple:
            print(f"🎯 因子数据已保存到: {args.output_dir}/single/")
        else:
            print(f"🎯 完整结果已保存到: {args.output_dir}/")

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)