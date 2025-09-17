#!/usr/bin/env python3
"""
验证数据路径配置的脚本
"""

import os
from pathlib import Path

def verify_data_paths():
    print("🔍 验证数据路径...")

    etf_factor_dir = Path(__file__).parent
    project_root = etf_factor_dir.parent
    data_collection_dir = project_root / "data_collection"

    # 检查数据目录
    data_base_dir = data_collection_dir / "data"
    print(f"📂 数据根目录: {data_base_dir}")
    print(f"   存在: {'✅' if data_base_dir.exists() else '❌'}")

    # 检查ETF数据
    etf_codes = []
    if data_base_dir.exists():
        for item in data_base_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                etf_codes.append(item.name)

    print(f"📈 发现ETF数据: {len(etf_codes)} 个")
    for code in etf_codes[:5]:  # 显示前5个
        etf_dir = data_base_dir / code
        files = [f.name for f in etf_dir.iterdir() if f.suffix == '.csv']
        print(f"   {code}: {len(files)} 个数据文件 {files}")

    if len(etf_codes) > 5:
        print(f"   ... 还有 {len(etf_codes) - 5} 个ETF")

    # 检查因子输出目录
    factor_data_dir = etf_factor_dir / "factor_data"
    print(f"\n📊 因子数据目录: {factor_data_dir}")
    print(f"   存在: {'✅' if factor_data_dir.exists() else '❌'}")

    if factor_data_dir.exists():
        factor_etfs = [d.name for d in factor_data_dir.iterdir() if d.is_dir() and d.name != 'cache']
        print(f"   已计算因子的ETF: {len(factor_etfs)} 个")
        for code in factor_etfs:
            etf_factor_dir = factor_data_dir / code
            factor_files = [f.name for f in etf_factor_dir.iterdir() if f.suffix == '.csv']
            print(f"     {code}: {len(factor_files)} 个因子文件")

    print("\n✅ 路径验证完成")

if __name__ == "__main__":
    verify_data_paths()
