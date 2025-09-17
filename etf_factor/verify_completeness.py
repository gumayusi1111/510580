#!/usr/bin/env python3
"""
验证因子数据质量和完整性的脚本
"""

import os
import pandas as pd
from datetime import datetime

def main():
    print("🔍 验证因子数据质量和完整性...")
    print("=" * 60)

    factor_dir = "factor_data/510580"

    if not os.path.exists(factor_dir):
        print(f"❌ 因子数据目录不存在: {factor_dir}")
        return False

    # 获取所有因子文件
    factor_files = [f for f in os.listdir(factor_dir) if f.endswith('.csv')]
    factor_files.sort()

    print(f"📁 发现因子文件数: {len(factor_files)}")
    print()

    total_issues = 0
    all_factor_info = []

    for factor_file in factor_files:
        file_path = os.path.join(factor_dir, factor_file)
        factor_name = factor_file.replace('.csv', '')

        try:
            # 读取因子数据
            df = pd.read_csv(file_path)

            # 基本信息
            rows = len(df)
            cols = len(df.columns)

            # 检查必要列
            required_cols = ['ts_code', 'trade_date']
            missing_cols = [col for col in required_cols if col not in df.columns]

            # 检查数据质量
            null_count = df.isnull().sum().sum()

            # 日期范围
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                date_range = f"{df['trade_date'].min().date()} 到 {df['trade_date'].max().date()}"
            else:
                date_range = "无日期信息"

            # 因子列(排除基本列)
            factor_cols = [col for col in df.columns if col not in ['ts_code', 'trade_date']]

            factor_info = {
                'name': factor_name,
                'rows': rows,
                'cols': cols,
                'factor_cols': len(factor_cols),
                'null_count': null_count,
                'date_range': date_range,
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

            all_factor_info.append(factor_info)

        except Exception as e:
            print(f"❌ 读取因子文件失败 {factor_name}: {e}")
            total_issues += 1

    # 显示详细报告
    print("📊 因子数据质量报告:")
    print("-" * 80)
    print(f"{'因子名称':<15} {'行数':<6} {'列数':<4} {'因子列':<6} {'空值':<6} {'状态'}")
    print("-" * 80)

    healthy_factors = 0
    for info in all_factor_info:
        status = "✅ 正常" if not info['issues'] else f"⚠️  {len(info['issues'])}个问题"

        if not info['issues']:
            healthy_factors += 1

        print(f"{info['name']:<15} {info['rows']:<6} {info['cols']:<4} {info['factor_cols']:<6} {info['null_count']:<6} {status}")

        # 显示问题详情
        for issue in info['issues']:
            print(f"    💭 {issue}")

    print("-" * 80)

    # 汇总统计
    total_factors = len(all_factor_info)
    total_rows = sum(info['rows'] for info in all_factor_info)
    total_null_values = sum(info['null_count'] for info in all_factor_info)

    print("\n📈 汇总统计:")
    print(f"   🔢 因子总数: {total_factors}")
    print(f"   ✅ 健康因子: {healthy_factors}/{total_factors} ({healthy_factors/total_factors:.1%})")
    print(f"   📊 总数据行数: {total_rows:,}")
    print(f"   ❓ 总空值数: {total_null_values:,}")
    print(f"   ⚠️  总问题数: {total_issues}")

    # 显示日期范围统计
    if all_factor_info:
        sample_info = all_factor_info[0]
        print(f"   📅 数据时间范围: {sample_info['date_range']}")
        print(f"   📆 数据天数: {sample_info['rows']:,} 天")

    print("\n" + "=" * 60)

    if total_issues == 0:
        print("🎉 所有因子数据质量验证通过!")
        print("✅ 数据完整性和质量良好，可以用于后续分析")
        return True
    else:
        print(f"⚠️  发现 {total_issues} 个问题，请检查上述详情")
        print("💡 大部分问题可能是正常的（如早期数据的空值）")
        return False

if __name__ == "__main__":
    main()