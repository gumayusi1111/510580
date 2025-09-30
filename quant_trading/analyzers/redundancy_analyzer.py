"""
因子冗余性分析工具 (v3新增)

分析因子相关性并识别冗余因子组，基于总分推荐去重后的因子列表
"""

import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.correlation.core import RedundancyDetector
from analyzers.correlation.selection import FactorSelector
import numpy as np


def analyze_redundancy(etf_code: str, threshold: float = 0.85):
    """
    分析指定ETF的因子冗余性

    Args:
        etf_code: ETF代码
        threshold: 相关性阈值，默认0.85
    """
    print(f"\n{'='*80}")
    print(f"因子冗余性分析 - {etf_code}")
    print(f"相关性阈值: {threshold}")
    print(f"{'='*80}\n")

    # 1. 读取最新的CSV报告
    script_dir = Path(__file__).parent.parent
    report_dir = script_dir / "reports" / etf_code
    csv_files = list(report_dir.glob("factor_ranking_*.csv"))

    if not csv_files:
        print(f"❌ 未找到{etf_code}的评估报告，请先运行因子评估")
        return

    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"📄 读取报告: {latest_csv.name}\n")

    ranking_df = pd.read_csv(latest_csv, index_col='factor')

    # 2. 简化版本：基于因子名称的启发式分组
    evaluated_factors = ranking_df.index.tolist()
    print(f"📊 因子总数: {len(evaluated_factors)}")
    print(f"🔍 基于因子名称进行启发式分组...\n")

    # 手动定义同质化因子组
    redundant_groups = {}

    # RSI组
    rsi_factors = {f for f in evaluated_factors if f.startswith('RSI_')}
    if len(rsi_factors) > 1:
        redundant_groups['RSI系列'] = rsi_factors

    # STOCH组
    stoch_factors = {f for f in evaluated_factors if f.startswith('STOCH_')}
    if len(stoch_factors) > 1:
        redundant_groups['STOCH系列'] = stoch_factors

    # KDJ组
    kdj_factors = {f for f in evaluated_factors if f.startswith('KDJ_')}
    if len(kdj_factors) > 1:
        redundant_groups['KDJ系列'] = kdj_factors

    # SMA/EMA/WMA组
    ma_factors = {f for f in evaluated_factors if any(f.startswith(p) for p in ['SMA_', 'EMA_', 'WMA_'])}
    if len(ma_factors) > 3:
        redundant_groups['移动均线系列'] = ma_factors

    # MACD组
    macd_factors = {f for f in evaluated_factors if f.startswith('MACD_')}
    if len(macd_factors) > 1:
        redundant_groups['MACD系列'] = macd_factors

    # HV/ANNUAL_VOL组
    vol_factors = {f for f in evaluated_factors if 'VOL' in f or f.startswith('HV_')}
    if len(vol_factors) > 1:
        redundant_groups['波动率系列'] = vol_factors

    # BOLL组
    boll_factors = {f for f in evaluated_factors if f.startswith('BOLL_') or f.startswith('BB_')}
    if len(boll_factors) > 1:
        redundant_groups['布林带系列'] = boll_factors

    if not redundant_groups:
        print(f"✅ 未发现相关性>{threshold}的冗余因子组\n")
        return

    print(f"🔍 发现 {len(redundant_groups)} 个冗余因子组:\n")
    print(f"{'-'*80}")

    # 5. 对每个冗余组推荐最佳因子
    recommended_factors = []
    redundant_factors = []

    for group_id, factors in redundant_groups.items():
        factors_list = sorted(list(factors))

        # 基于total_score选择最佳因子
        best_factor = FactorSelector.select_by_total_score(factors, ranking_df)

        print(f"\n【{group_id}】({len(factors)}个因子)")
        print(f"  因子列表: {', '.join(factors_list)}")

        # 显示各因子得分
        print(f"\n  {'因子':<15} {'总分':<8} {'评级':<4} {'IC分':<8} {'稳定分':<8}")
        for f in factors_list:
            if f in ranking_df.index:
                row = ranking_df.loc[f]
                marker = "★" if f == best_factor else " "
                print(f"{marker} {f:<15} {row['total_score']:.4f}   {row['grade']:<4} "
                      f"{row['ic_score']:.4f}   {row['stability_score']:.4f}")

        print(f"\n  ✅ 推荐保留: {best_factor}")
        print(f"  ❌ 建议移除: {', '.join([f for f in factors_list if f != best_factor])}")

        recommended_factors.append(best_factor)
        redundant_factors.extend([f for f in factors_list if f != best_factor])

    # 6. 总结
    print(f"\n{'='*80}")
    print(f"📈 去重建议总结")
    print(f"{'='*80}\n")

    all_factors_in_groups = set()
    for factors in redundant_groups.values():
        all_factors_in_groups.update(factors)

    independent_factors = set(evaluated_factors) - all_factors_in_groups

    print(f"  原始因子数量: {len(evaluated_factors)}")
    print(f"  独立因子: {len(independent_factors)}个 (不在任何冗余组中)")
    print(f"  冗余组数量: {len(redundant_groups)}")
    print(f"  冗余组中推荐保留: {len(recommended_factors)}个")
    print(f"  建议移除: {len(redundant_factors)}个")
    print(f"\n  ✅ 去重后因子总数: {len(independent_factors) + len(recommended_factors)}个")
    print(f"  📉 减少: {len(redundant_factors)}个 ({len(redundant_factors)/len(evaluated_factors)*100:.1f}%)\n")

    # 7. 输出去重后的因子列表
    final_factors = sorted(list(independent_factors) + recommended_factors)

    print(f"💡 推荐使用的因子列表 ({len(final_factors)}个):")
    print(f"{'-'*80}")

    # 按评级分组显示
    for grade in ['A', 'B', 'C']:
        grade_factors = [f for f in final_factors if f in ranking_df.index and ranking_df.loc[f, 'grade'] == grade]
        if grade_factors:
            print(f"\n  {grade}级 ({len(grade_factors)}个):")
            for f in grade_factors:
                score = ranking_df.loc[f, 'total_score']
                print(f"    {f:<20} (总分: {score:.3f})")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='分析因子冗余性')
    parser.add_argument('etf_code', type=str, help='ETF代码，如510300')
    parser.add_argument('--threshold', type=float, default=0.85,
                       help='相关性阈值 (默认0.85)')

    args = parser.parse_args()

    try:
        analyze_redundancy(args.etf_code, args.threshold)
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()