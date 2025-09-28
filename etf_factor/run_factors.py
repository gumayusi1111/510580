#!/usr/bin/env python3
"""
独立的因子计算脚本
用于从外部调用etf_factor系统
"""

import sys
import os

# 确保能导入etf_factor模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

from src.engine import VectorizedEngine

def main():
    if len(sys.argv) < 2:
        print("用法: python run_factors.py <data_dir> [output_dir]")
        sys.exit(1)

    data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "factor_data"

    print(f"📂 数据目录: {data_dir}")
    print(f"📈 输出目录: {output_dir}")

    try:
        # 创建引擎
        engine = VectorizedEngine(data_dir=data_dir, output_dir=output_dir)
        print(f"📈 注册因子: {len(engine.factors)} 个")

        # 计算所有因子
        results = engine.calculate_all_factors(use_cache=False)

        if results:
            # 保存因子结果
            saved_files = engine.save_factor_results(results, output_type='single')
            print(f"💾 保存了 {len(saved_files)} 个因子文件")
            print(f"✅ 因子计算完成: {len(results)} 个因子")
            return True
        else:
            print("❌ 因子计算失败: 无结果")
            return False

    except Exception as e:
        print(f"❌ 因子计算出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)