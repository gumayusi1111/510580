#!/usr/bin/env python3
"""
系统验证脚本
验证数据路径配置和因子数据质量完整性
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd


def verify_data_paths(data_collection_dir):
    """验证数据路径配置"""
    print("🔍 验证数据路径...")

    # 检查数据目录
    data_base_dir = Path(data_collection_dir) / "data"
    print(f"📂 数据根目录: {data_base_dir}")
    print(f"   存在: {'✅' if data_base_dir.exists() else '❌'}")

    if not data_base_dir.exists():
        return False, []

    # 检查ETF数据
    etf_codes = []
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

    return True, etf_codes


def verify_factor_data(factor_data_dir):
    """验证因子数据质量和完整性"""
    print("\n🔍 验证因子数据质量和完整性...")

    # 检查因子输出目录
    factor_data_path = Path(factor_data_dir)
    print(f"📊 因子数据目录: {factor_data_path}")
    print(f"   存在: {'✅' if factor_data_path.exists() else '❌'}")

    if not factor_data_path.exists():
        print("❌ 因子数据目录不存在，请先运行因子计算")
        return False

    # 查找因子文件
    factor_files = []
    factor_etfs = []

    for etf_dir in factor_data_path.iterdir():
        if etf_dir.is_dir() and etf_dir.name != 'cache':
            factor_etfs.append(etf_dir.name)
            for factor_file in etf_dir.iterdir():
                if factor_file.suffix == '.csv':
                    factor_files.append(factor_file)

    if not factor_files:
        print("❌ 未发现任何因子文件")
        return False

    print(f"   已计算因子的ETF: {len(factor_etfs)} 个")
    for code in factor_etfs:
        etf_factor_dir = factor_data_path / code
        etf_factor_files = [f.name for f in etf_factor_dir.iterdir() if f.suffix == '.csv']
        print(f"     {code}: {len(etf_factor_files)} 个因子文件")

    # 详细验证第一个ETF的因子质量
    if factor_etfs:
        target_etf = factor_etfs[0]
        target_dir = factor_data_path / target_etf
        etf_factor_files = [f for f in target_dir.iterdir() if f.suffix == '.csv']

        print(f"\n📊 详细验证 {target_etf} 的因子数据质量:")
        print("-" * 80)
        print(f"{'因子名称':<15} {'行数':<6} {'列数':<4} {'因子列':<6} {'空值':<6} {'状态'}")
        print("-" * 80)

        total_issues = 0
        healthy_factors = 0
        all_factor_info = []

        for factor_file in etf_factor_files:
            factor_name = factor_file.stem.replace(f'_{target_etf}', '')

            try:
                # 读取因子数据
                df = pd.read_csv(factor_file)

                # 基本信息
                rows = len(df)
                cols = len(df.columns)

                # 检查必要列
                required_cols = ['ts_code', 'trade_date']
                missing_cols = [col for col in required_cols if col not in df.columns]

                # 检查数据质量
                null_count = df.isnull().sum().sum()

                # 因子列(排除基本列)
                factor_cols = [col for col in df.columns if col not in ['ts_code', 'trade_date']]

                factor_info = {
                    'name': factor_name,
                    'rows': rows,
                    'cols': cols,
                    'factor_cols': len(factor_cols),
                    'null_count': null_count,
                    'issues': []
                }

                # 验证规则
                if rows < 1000:
                    factor_info['issues'].append(f"数据量过少({rows}行)")
                    total_issues += 1

                if missing_cols:
                    factor_info['issues'].append(f"缺少必要列: {missing_cols}")
                    total_issues += 1

                if null_count > rows * 0.1:  # 超过10%的空值
                    factor_info['issues'].append(f"空值过多({null_count}个)")
                    total_issues += 1

                if len(factor_cols) == 0:
                    factor_info['issues'].append("无因子数据列")
                    total_issues += 1

                if not factor_info['issues']:
                    healthy_factors += 1

                status = "✅ 正常" if not factor_info['issues'] else f"⚠️  {len(factor_info['issues'])}个问题"

                print(f"{factor_info['name']:<15} {factor_info['rows']:<6} {factor_info['cols']:<4} {factor_info['factor_cols']:<6} {factor_info['null_count']:<6} {status}")

                # 显示问题详情
                for issue in factor_info['issues']:
                    print(f"    💭 {issue}")

                all_factor_info.append(factor_info)

            except Exception as e:
                print(f"❌ 读取因子文件失败 {factor_name}: {e}")
                total_issues += 1

        print("-" * 80)

        # 汇总统计
        total_factors = len(all_factor_info)
        total_rows = sum(info['rows'] for info in all_factor_info)
        total_null_values = sum(info['null_count'] for info in all_factor_info)

        print(f"\n📈 {target_etf} 汇总统计:")
        print(f"   🔢 因子总数: {total_factors}")
        print(f"   ✅ 健康因子: {healthy_factors}/{total_factors} ({healthy_factors/total_factors:.1%})")
        print(f"   📊 总数据行数: {total_rows:,}")
        print(f"   ❓ 总空值数: {total_null_values:,}")
        print(f"   ⚠️  总问题数: {total_issues}")

        # 显示日期范围统计
        if all_factor_info:
            try:
                sample_file = etf_factor_files[0]
                sample_df = pd.read_csv(sample_file)
                if 'trade_date' in sample_df.columns:
                    sample_df['trade_date'] = pd.to_datetime(sample_df['trade_date'], format='%Y%m%d')
                    date_range = f"{sample_df['trade_date'].min().date()} 到 {sample_df['trade_date'].max().date()}"
                    print(f"   📅 数据时间范围: {date_range}")
                    print(f"   📆 数据天数: {len(sample_df):,} 天")
            except Exception:
                pass

        return total_issues == 0

    return True


def main():
    parser = argparse.ArgumentParser(description='系统验证脚本')
    parser.add_argument('--data-collection', type=str,
                       default='../../data_collection',
                       help='数据采集目录路径')
    parser.add_argument('--factor-data', type=str,
                       default='../factor_data',
                       help='因子数据目录路径')
    parser.add_argument('--skip-paths', action='store_true',
                       help='跳过数据路径验证')
    parser.add_argument('--skip-quality', action='store_true',
                       help='跳过因子质量验证')

    args = parser.parse_args()

    print("🔍 系统验证开始...")
    print("=" * 60)

    success = True

    # 验证数据路径
    if not args.skip_paths:
        path_success, etf_codes = verify_data_paths(args.data_collection)
        if not path_success:
            print("❌ 数据路径验证失败")
            success = False
        else:
            print("✅ 数据路径验证通过")

    # 验证因子数据质量
    if not args.skip_quality:
        quality_success = verify_factor_data(args.factor_data)
        if not quality_success:
            print("\n⚠️  因子数据质量验证发现问题")
            success = False
        else:
            print("\n✅ 因子数据质量验证通过")

    print("\n" + "=" * 60)

    if success:
        print("🎉 系统验证全部通过!")
        print("✅ 数据完整性和质量良好，可以用于后续分析")
    else:
        print("⚠️  系统验证发现问题，请检查上述详情")
        print("💡 大部分问题可能是正常的（如早期数据的空值）")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)