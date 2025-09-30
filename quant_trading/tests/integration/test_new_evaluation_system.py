#!/usr/bin/env python3
"""
测试新的智能评级系统
运行对所有ETF因子的完整评估，生成新报告并与旧系统对比
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from quant_trading.analyzers.factor_evaluation.evaluator import FactorEvaluator
from quant_trading.core.data_management import DataManager


def test_new_evaluation_system():
    """测试新的智能评级系统"""
    print("🚀 === 新智能评级系统全面测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ETF列表
    etf_codes = ["510300", "510580", "513180"]

    for etf_code in etf_codes:
        print(f"\n📊 === 评估ETF: {etf_code} ===")

        try:
            # 创建智能评估器（启用适应性分析）
            evaluator = FactorEvaluator(strategy_type='short_term')
            print("✅ 智能评估器创建成功")

            # 执行完整评估
            print("🔍 开始完整因子评估...")
            results = evaluator.evaluate_all_factors(etf_code)

            if 'error' in results:
                print(f"❌ 评估失败: {results['error']}")
                continue

            # 显示评估概览
            summary = results['evaluation_summary']
            print(f"📈 评估完成:")
            print(f"   总因子数: {summary['total_factors']}")
            print(f"   成功评估: {summary['evaluated_factors']}")
            print(f"   数据期间: {summary['data_period']}")

            # 显示因子排序Top 10
            ranking = results['factor_ranking']
            if not ranking.empty:
                print(f"\n🏆 Top 10 因子排序:")
                top10 = ranking.head(10)
                for idx, row in top10.iterrows():
                    print(f"   {row['rank']:2d}. {row['factor']:20s} | {row['grade']} | {row['total_score']:.3f}")

            # 保存新报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_dir = f"/Users/wenbai/Desktop/singleetfs/quant_trading/reports_new/{etf_code}"
            os.makedirs(report_dir, exist_ok=True)

            # 保存排序CSV
            ranking_file = f"{report_dir}/factor_ranking_{etf_code}_{timestamp}_NEW.csv"
            ranking.to_csv(ranking_file, index=False)
            print(f"📄 新排序报告已保存: {ranking_file}")

            # 生成Markdown报告
            generate_evaluation_report(results, etf_code, timestamp, report_dir)

        except Exception as e:
            print(f"❌ 评估ETF {etf_code} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n🎉 === 新智能评级系统测试完成 ===")
    print("✨ 请查看 reports_new/ 目录下的新报告")
    print("📊 可以与 reports/ 目录下的旧报告进行对比")


def generate_evaluation_report(results, etf_code, timestamp, report_dir):
    """生成评估报告"""

    summary = results['evaluation_summary']
    ranking = results['factor_ranking']

    report_content = f"""# ETF因子评估报告 - {etf_code} (新智能系统)

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 评估概览

- **ETF代码**: {etf_code}
- **评估系统**: 智能适应性评级系统 (Phase 1-2集成)
- **总因子数量**: {summary['total_factors']}
- **评估因子数量**: {summary['evaluated_factors']}
- **数据时间范围**: {summary['data_period'][0]} 至 {summary['data_period'][1]}

## 🚀 新系统特性

- ✅ **智能因子分类**: 基于因子名称自动识别类型
- ✅ **适应性前瞻期**: 不同因子类型使用专属前瞻期组合
- ✅ **精准IC评估**: 基于因子特性的精确IC计算
- ✅ **改进效果量化**: 新旧方法对比分析
- ✅ **样本外验证**: 防止过拟合的健壮性检查

## 🏆 因子质量排序

### Top 20 因子

| 排名 | 因子名称 | 评级 | 总分 | IC得分 | 稳定性 | 数据质量 |
|------|----------|------|------|--------|--------|----------|"""

    if not ranking.empty:
        top20 = ranking.head(20)
        for idx, row in top20.iterrows():
            report_content += f"\n| {row['rank']} | {row['factor']} | {row['grade']} | {row['total_score']:.3f} | {row['ic_score']:.3f} | {row['stability_score']:.3f} | {row['data_quality_score']:.3f} |"

    report_content += f"""

## 📈 评级分布统计

"""

    if not ranking.empty:
        grade_counts = ranking['grade'].value_counts().sort_index()
        for grade, count in grade_counts.items():
            percentage = (count / len(ranking)) * 100
            report_content += f"- **{grade}级**: {count}个因子 ({percentage:.1f}%)\n"

    report_content += f"""

## 🔍 质量分析

### 高质量因子 (A级和B级)
"""

    if not ranking.empty:
        high_quality = ranking[ranking['grade'].isin(['A', 'B'])]
        if len(high_quality) > 0:
            report_content += f"- 共{len(high_quality)}个高质量因子\n"
            report_content += "- 主要因子类型:\n"
            for factor in high_quality.head(10)['factor']:
                report_content += f"  - {factor}\n"

    report_content += f"""

### 待改进因子 (D级和F级)
"""

    if not ranking.empty:
        low_quality = ranking[ranking['grade'].isin(['D', 'F'])]
        if len(low_quality) > 0:
            report_content += f"- 共{len(low_quality)}个待改进因子\n"
            report_content += f"- 建议优化或剔除\n"

    report_content += f"""

---

## 📋 系统说明

本报告由**智能适应性评级系统**生成，集成了以下技术改进：

1. **智能因子分类器**: 自动识别因子类型并分配适应性前瞻期
2. **适应性IC分析**: 基于因子特性进行精准IC计算
3. **样本外验证**: 防止过拟合，确保因子健壮性
4. **改进效果量化**: 新旧方法对比分析

### 与传统系统的区别

- **传统系统**: 所有因子统一使用[1,3,5,10]日前瞻期
- **新系统**:
  - 短期技术因子: [1,3,5]日前瞻期
  - 基本面因子: [10,20,30]日前瞻期
  - 宏观因子: [5,10,20]日前瞻期
  - 中期技术因子: [3,5,10]日前瞻期
  - 收益风险因子: [1,5,10]日前瞻期

这样的分类能更准确地评估每个因子的真实预测能力。

---

*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 智能适应性评级系统 v2.0*
"""

    # 保存报告
    report_file = f"{report_dir}/factor_evaluation_{etf_code}_{timestamp}_NEW.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"📄 新评估报告已保存: {report_file}")


if __name__ == '__main__':
    test_new_evaluation_system()