"""
报告模板 - Markdown模板生成器
包含各种报告模板的生成功能
"""

from typing import Dict, List
import pandas as pd
from datetime import datetime


class MarkdownTemplate:
    """Markdown报告模板生成器"""

    @staticmethod
    def generate_header(etf_code: str) -> str:
        """生成报告头部"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""# ETF因子评估报告 - {etf_code}

**生成时间**: {timestamp}

---

"""

    @staticmethod
    def generate_summary_section(evaluation_results: Dict) -> str:
        """生成评估概览部分"""
        if 'evaluation_summary' not in evaluation_results:
            return "## 📊 评估概览\n\n数据概览信息不可用\n\n"

        summary = evaluation_results['evaluation_summary']
        etf_code = evaluation_results.get('etf_code', 'N/A')

        content = ["## 📊 评估概览\n"]
        content.append(f"- **ETF代码**: {etf_code}")
        content.append(f"- **总因子数量**: {summary.get('total_factors', 0)}")
        content.append(f"- **评估因子数量**: {summary.get('evaluated_factors', 0)}")

        if 'data_period' in summary and summary['data_period'] and summary['data_period'][0] is not None:
            start_date, end_date = summary['data_period']
            # 处理各种日期格式
            if hasattr(start_date, 'strftime'):
                start_str = start_date.strftime('%Y-%m-%d')
            else:
                start_str = str(start_date)[:10]  # 取前10个字符作为日期

            if hasattr(end_date, 'strftime'):
                end_str = end_date.strftime('%Y-%m-%d')
            else:
                end_str = str(end_date)[:10]  # 取前10个字符作为日期

            content.append(f"- **数据时间范围**: {start_str} 至 {end_str}")

        content.append("\n")
        return "\n".join(content)

    @staticmethod
    def generate_ranking_section(factor_ranking: pd.DataFrame) -> str:
        """生成因子排序部分"""
        if factor_ranking.empty:
            return "## 🏆 因子质量排序\n\n暂无因子排序数据\n\n"

        content = ["## 🏆 因子质量排序\n"]
        content.append("### Top 10 因子\n")

        # 表头
        content.append("| 排名 | 因子名称 | 评级 | 总分 | IC得分 | 稳定性 | 数据质量 |")
        content.append("|------|----------|------|------|--------|--------|----------|")

        # Top 10 因子数据
        top_10 = factor_ranking.head(10)
        for _, row in top_10.iterrows():
            content.append(
                f"| {row['rank']} | {row['factor']} | {row['grade']} | "
                f"{row['total_score']:.3f} | {row['ic_score']:.3f} | "
                f"{row['stability_score']:.3f} | {row['data_quality_score']:.3f} |"
            )

        content.append("\n")
        return "\n".join(content)

    @staticmethod
    def generate_grade_distribution(factor_ranking: pd.DataFrame) -> str:
        """生成评级分布部分"""
        if factor_ranking.empty:
            return "### 因子评级分布\n\n暂无评级分布数据\n\n"

        grade_counts = factor_ranking['grade'].value_counts()
        total_factors = len(factor_ranking)

        content = ["### 因子评级分布\n"]
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_counts.get(grade, 0)
            percentage = (count / total_factors * 100) if total_factors > 0 else 0
            content.append(f"- **{grade}级**: {count}个因子 ({percentage:.1f}%)")

        content.append("\n")
        return "\n".join(content)

    @staticmethod
    def generate_recommendations_section(recommendations: Dict) -> str:
        """生成因子筛选建议部分"""
        if not recommendations:
            return "## 🎯 因子筛选建议\n\n暂无筛选建议\n\n"

        content = ["## 🎯 因子筛选建议\n"]

        # 推荐使用的因子
        recommended = recommendations.get('recommended_factors', [])
        if recommended:
            content.append("### 推荐使用的因子\n")
            for i, factor in enumerate(recommended, 1):
                content.append(f"{i}. **{factor}**")
            content.append(f"\n**推荐因子总数**: {len(recommended)}\n")

        # 冗余因子
        redundant = recommendations.get('redundant_factors', [])
        if redundant:
            content.append("### 建议剔除的冗余因子\n")
            for factor in redundant:
                content.append(f"- {factor}")
            content.append(f"\n**冗余因子数量**: {len(redundant)}\n")

        # 低质量因子
        low_quality = recommendations.get('low_quality_factors', [])
        if low_quality:
            content.append("### 低质量因子\n")
            for factor in low_quality:
                content.append(f"- {factor}")
            content.append(f"\n**低质量因子数量**: {len(low_quality)}")

        return "\n".join(content)

    @staticmethod
    def generate_correlation_section(correlation_results: Dict) -> str:
        """生成相关性分析部分"""
        if not correlation_results:
            return "## 🔗 相关性分析\n\n暂无相关性分析数据\n\n"

        content = ["## 🔗 相关性分析\n"]
        content.append("### 相关性统计\n")

        stats = correlation_results.get('correlation_statistics', {})
        content.append(f"- **因子对总数**: {stats.get('total_pairs', 0)}")
        content.append(f"- **平均相关性**: {stats.get('mean_correlation', 0):.3f}")
        content.append(f"- **相关性标准差**: {stats.get('std_correlation', 0):.3f}")
        content.append(f"- **最大相关性**: {stats.get('max_correlation', 0):.3f}")

        # 高相关性统计
        high_corr_stats = stats.get('high_correlation_stats', {})
        for threshold, ratio in high_corr_stats.items():
            content.append(f"- **>{threshold}相关性比例**: {ratio:.1f}%")

        content.append("\n")
        return "\n".join(content)

    @staticmethod
    def generate_ic_analysis_section(ic_analysis: Dict, window_config: Dict) -> str:
        """生成IC分析概览部分"""
        if not ic_analysis:
            return "## 📈 IC分析概览\n\n暂无IC分析数据\n\n"

        content = ["## 📈 IC分析概览\n"]

        # 窗口配置信息
        if window_config:
            content.append("### 分析窗口配置\n")
            content.append(f"- **策略类型**: {window_config.get('strategy_type', 'unknown')}")
            content.append(f"- **策略描述**: {window_config.get('description', 'N/A')}")
            content.append(f"- **IC分析窗口**: {window_config.get('ic_windows', [])}日")
            content.append(f"- **主窗口**: {window_config.get('primary_window', 'N/A')}日")
            content.append("\n")

        # IC表现统计
        ic_stats = ic_analysis.get('ic_statistics', {})
        if ic_stats:
            content.append("### IC表现统计（基于主窗口）\n")
            content.append(f"- **平均IC**: {ic_stats.get('mean_ic', 0):.4f}")
            content.append(f"- **IC标准差**: {ic_stats.get('std_ic', 'nan')}")
            content.append(f"- **平均IC_IR**: {ic_stats.get('mean_ic_ir', 0):.4f}")
            content.append(f"- **IC胜率平均**: {ic_stats.get('mean_win_rate', 0)*100:.1f}%")
            content.append("\n")

        return "\n".join(content)

    @staticmethod
    def generate_usage_guidelines() -> str:
        """生成使用建议部分"""
        return """## 💡 使用建议

### 策略开发建议
1. **优先使用A级和B级因子**进行策略构建
2. **避免同时使用高相关性因子**，防止冗余
3. **关注IC_IR较高的因子**，其预测能力更稳定
4. **定期重新评估因子有效性**，及时调整因子池

### 风险提示
1. 历史表现不代表未来收益
2. 因子有效性可能随市场环境变化
3. 建议结合多个因子构建策略，降低单因子风险
4. 注意控制回撤，设置合理的止损机制

### 技术说明
- **IC值**: 信息系数，衡量因子预测能力
- **IC_IR**: IC信息比率，衡量IC的稳定性
- **IC胜率**: IC为正的比例，衡量预测方向准确性
- **相关性阈值**: 0.8，超过此值认为因子高度相关

---

*报告生成时间: {timestamp}*
*ETF代码: {etf_code}*
*本报告仅供研究参考，不构成投资建议*
"""

    @staticmethod
    def format_template_variables(template: str, **kwargs) -> str:
        """格式化模板变量"""
        try:
            return template.format(**kwargs)
        except KeyError:
            # 如果某些变量未提供，返回原模板
            return template