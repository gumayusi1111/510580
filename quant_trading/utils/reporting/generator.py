"""
报告生成器 - 重构版本
生成因子分析和策略评估报告的主要接口
"""

import pandas as pd
from typing import Dict, List
from pathlib import Path
import logging
from datetime import datetime

from .templates import MarkdownTemplate
from .formatter import ReportFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """分析报告生成器"""

    def __init__(self, output_dir: str = None):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录路径
        """
        if output_dir is None:
            # 默认输出到quant_trading/reports目录
            current_dir = Path(__file__).parent
            quant_trading_root = current_dir.parent.parent
            self.output_dir = quant_trading_root / "reports"
        else:
            self.output_dir = Path(output_dir)

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"报告输出目录: {self.output_dir}")

        self.template = MarkdownTemplate()
        self.formatter = ReportFormatter()

    def _cleanup_old_reports(self, etf_output_dir: Path, report_type: str, keep_count: int = 1):
        """
        清理旧的报告文件，只保留最新的几个

        Args:
            etf_output_dir: ETF输出目录
            report_type: 报告类型前缀 (如 'factor_evaluation', 'factor_ranking')
            keep_count: 保留文件数量
        """
        try:
            # 查找所有该类型的文件
            pattern = f"{report_type}_{etf_output_dir.name}_*.{{'md','csv'}}"
            files = []

            # 查找markdown文件
            md_files = list(etf_output_dir.glob(f"{report_type}_{etf_output_dir.name}_*.md"))
            csv_files = list(etf_output_dir.glob(f"{report_type}_{etf_output_dir.name}_*.csv"))

            # 按修改时间排序，最新的在前
            all_files = md_files + csv_files
            all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除多余的文件
            files_to_delete = all_files[keep_count:]
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    logger.info(f"已删除旧报告文件: {file_path.name}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")

        except Exception as e:
            logger.error(f"清理旧报告失败: {e}")

    def generate_factor_evaluation_report(self, evaluation_results: Dict,
                                        etf_code: str = "510580") -> str:
        """
        生成因子评估报告

        Args:
            evaluation_results: 因子评估结果
            etf_code: ETF代码

        Returns:
            报告文件路径
        """
        try:
            # 创建ETF特定的输出目录
            etf_output_dir = self.output_dir / etf_code
            etf_output_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = self.formatter.generate_timestamp()
            report_filename = f"factor_evaluation_{etf_code}_{timestamp}.md"
            report_path = etf_output_dir / report_filename

            # 构建报告内容
            content_parts = []

            # 报告头部
            content_parts.append(self.template.generate_header(etf_code))

            # 评估概览
            content_parts.append(self.template.generate_summary_section(evaluation_results))

            # 因子排序
            factor_ranking = self.formatter.create_ranking_dataframe(evaluation_results)
            content_parts.append(self.template.generate_ranking_section(factor_ranking))

            # 评级分布
            content_parts.append(self.template.generate_grade_distribution(factor_ranking))

            # 因子筛选建议
            recommendations = evaluation_results.get('selection_recommendations', {})
            content_parts.append(self.template.generate_recommendations_section(recommendations))

            # 相关性分析
            correlation_results = evaluation_results.get('correlation_analysis', {})
            content_parts.append(self.template.generate_correlation_section(correlation_results))

            # IC分析概览
            ic_analysis = evaluation_results.get('ic_analysis', {})
            window_config = evaluation_results.get('window_config', {})
            content_parts.append(self.template.generate_ic_analysis_section(ic_analysis, window_config))

            # 使用建议
            usage_guidelines = self.template.generate_usage_guidelines()
            # 格式化模板变量
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            usage_guidelines = self.template.format_template_variables(
                usage_guidelines,
                timestamp=current_time,
                etf_code=etf_code
            )
            content_parts.append(usage_guidelines)

            # 写入文件
            report_content = "".join(content_parts)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            logger.info(f"因子评估报告已生成: {report_path}")

            # 清理旧的报告文件
            self._cleanup_old_reports(etf_output_dir, "factor_evaluation", keep_count=1)

            return str(report_path)

        except Exception as e:
            logger.error(f"生成因子评估报告失败: {e}")
            return ""

    def generate_csv_summary(self, evaluation_results: Dict,
                           etf_code: str = "510580") -> List[str]:
        """
        生成CSV汇总文件

        Args:
            evaluation_results: 评估结果
            etf_code: ETF代码

        Returns:
            生成的CSV文件路径列表
        """
        try:
            # 创建ETF特定的输出目录
            etf_output_dir = self.output_dir / etf_code
            etf_output_dir.mkdir(exist_ok=True)

            timestamp = self.formatter.generate_timestamp()
            file_paths = []

            # 导出数据
            export_data = self.formatter.create_csv_export_data(evaluation_results)

            for data_name, df in export_data.items():
                if not df.empty:
                    filename = f"{data_name}_{etf_code}_{timestamp}.csv"
                    file_path = etf_output_dir / filename
                    df.to_csv(file_path, index=False, encoding='utf-8')
                    file_paths.append(str(file_path))
                    logger.info(f"CSV文件已生成: {file_path}")

            # 如果没有通过formatter导出，使用备用方法
            if not file_paths:
                file_paths.extend(self._generate_fallback_csv(evaluation_results, etf_code, timestamp))

            # 清理旧的CSV文件
            self._cleanup_old_reports(etf_output_dir, "factor_ranking", keep_count=1)
            self._cleanup_old_reports(etf_output_dir, "factor_summary", keep_count=1)

            return file_paths

        except Exception as e:
            logger.error(f"生成CSV汇总失败: {e}")
            return []

    def _generate_fallback_csv(self, evaluation_results: Dict,
                             etf_code: str, timestamp: str) -> List[str]:
        """生成备用CSV文件"""
        file_paths = []
        etf_output_dir = self.output_dir / etf_code

        try:
            # 因子排序数据
            if 'factor_ranking' in evaluation_results:
                ranking_df = self.formatter.create_ranking_dataframe(evaluation_results)
                if not ranking_df.empty:
                    ranking_path = etf_output_dir / f"factor_ranking_{etf_code}_{timestamp}.csv"
                    ranking_df.to_csv(ranking_path, index=False, encoding='utf-8')
                    file_paths.append(str(ranking_path))

            # 因子详细信息汇总
            if 'factor_details' in evaluation_results:
                details = evaluation_results['factor_details']
                if isinstance(details, dict):
                    summary_data = []
                    for factor_name, factor_data in details.items():
                        if isinstance(factor_data, dict):
                            row = {'factor_name': factor_name}
                            # 扁平化数据
                            flattened = self.formatter._flatten_dict(factor_data)
                            row.update(flattened)
                            summary_data.append(row)

                    if summary_data:
                        summary_df = pd.DataFrame(summary_data)
                        summary_path = etf_output_dir / f"factor_summary_{etf_code}_{timestamp}.csv"
                        summary_df.to_csv(summary_path, index=False, encoding='utf-8')
                        file_paths.append(str(summary_path))

        except Exception as e:
            logger.error(f"生成备用CSV失败: {e}")

        return file_paths

    def generate_comparison_report(self, evaluation_results_list: List[Dict],
                                 etf_codes: List[str]) -> str:
        """
        生成多ETF对比报告

        Args:
            evaluation_results_list: 多个ETF的评估结果列表
            etf_codes: ETF代码列表

        Returns:
            对比报告文件路径
        """
        try:
            if len(evaluation_results_list) != len(etf_codes):
                raise ValueError("评估结果数量与ETF代码数量不匹配")

            timestamp = self.formatter.generate_timestamp()
            etf_codes_str = "_".join(etf_codes)
            report_filename = f"etf_comparison_{etf_codes_str}_{timestamp}.md"
            report_path = self.output_dir / report_filename

            content_parts = []

            # 报告头部
            content_parts.append(f"# ETF因子评估对比报告\n\n")
            content_parts.append(f"**对比ETF**: {', '.join(etf_codes)}\n")
            content_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            content_parts.append("---\n\n")

            # 为每个ETF生成简化报告
            for i, (evaluation_results, etf_code) in enumerate(zip(evaluation_results_list, etf_codes)):
                content_parts.append(f"## {etf_code} 因子分析\n\n")

                # 添加简化的分析内容
                factor_ranking = self.formatter.create_ranking_dataframe(evaluation_results)
                if not factor_ranking.empty:
                    content_parts.append(f"### Top 5 因子\n\n")
                    top_5 = factor_ranking.head(5)
                    content_parts.append("| 排名 | 因子名称 | 评级 | 总分 |\n")
                    content_parts.append("|------|----------|------|------|\n")
                    for _, row in top_5.iterrows():
                        content_parts.append(f"| {row['rank']} | {row['factor']} | {row['grade']} | {row['total_score']:.3f} |\n")
                    content_parts.append("\n")

            # 写入文件
            report_content = "".join(content_parts)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            logger.info(f"ETF对比报告已生成: {report_path}")
            return str(report_path)

        except Exception as e:
            logger.error(f"生成ETF对比报告失败: {e}")
            return ""