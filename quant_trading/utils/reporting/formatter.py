"""
报告格式化器 - 数据格式化和处理
处理报告生成中的数据格式化需求
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime


class ReportFormatter:
    """报告格式化器"""

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """格式化百分比"""
        if pd.isna(value):
            return 'N/A'
        return f"{value * 100:.{decimals}f}%"

    @staticmethod
    def format_number(value: float, decimals: int = 3) -> str:
        """格式化数字"""
        if pd.isna(value) or np.isinf(value):
            return 'N/A'
        return f"{value:.{decimals}f}"

    @staticmethod
    def format_date(date_obj, format_str: str = '%Y-%m-%d') -> str:
        """格式化日期"""
        if pd.isna(date_obj) or date_obj is None:
            return 'N/A'
        if isinstance(date_obj, str):
            return date_obj
        try:
            if hasattr(date_obj, 'strftime'):
                return date_obj.strftime(format_str)
            else:
                return str(date_obj)
        except (ValueError, AttributeError, TypeError):
            return 'N/A'

    @staticmethod
    def create_ranking_dataframe(evaluation_results: Dict) -> pd.DataFrame:
        """创建因子排序DataFrame"""
        if 'factor_ranking' not in evaluation_results:
            return pd.DataFrame()

        ranking_data = evaluation_results['factor_ranking']
        if isinstance(ranking_data, pd.DataFrame):
            return ranking_data.copy()

        # 如果是字典格式，转换为DataFrame
        if isinstance(ranking_data, dict):
            df_data = []
            for rank, (factor_name, scores) in enumerate(ranking_data.items(), 1):
                row = {
                    'rank': rank,
                    'factor': factor_name,
                    'total_score': scores.get('total_score', 0),
                    'grade': scores.get('grade', 'F'),
                    'ic_score': scores.get('ic_score', 0),
                    'stability_score': scores.get('stability_score', 0),
                    'data_quality_score': scores.get('data_quality_score', 0),
                    'distribution_score': scores.get('distribution_score', 0)
                }
                df_data.append(row)

            return pd.DataFrame(df_data)

        return pd.DataFrame()

    @staticmethod
    def create_summary_table(factor_ranking: pd.DataFrame) -> Dict:
        """创建摘要表格"""
        if factor_ranking.empty:
            return {}

        summary = {
            'total_factors': len(factor_ranking),
            'grade_distribution': factor_ranking['grade'].value_counts().to_dict(),
            'top_factors': factor_ranking.head(5)['factor'].tolist(),
            'average_scores': {
                'total_score': factor_ranking['total_score'].mean(),
                'ic_score': factor_ranking['ic_score'].mean(),
                'stability_score': factor_ranking['stability_score'].mean()
            }
        }
        return summary

    @staticmethod
    def format_correlation_stats(correlation_results: Dict) -> Dict:
        """格式化相关性统计"""
        if not correlation_results:
            return {}

        stats = correlation_results.get('correlation_statistics', {})
        formatted_stats = {}

        for key, value in stats.items():
            if isinstance(value, (int, float)):
                if 'ratio' in key or 'percentage' in key:
                    formatted_stats[key] = ReportFormatter.format_percentage(value)
                else:
                    formatted_stats[key] = ReportFormatter.format_number(value)
            else:
                formatted_stats[key] = value

        return formatted_stats

    @staticmethod
    def format_ic_statistics(ic_analysis: Dict) -> Dict:
        """格式化IC统计信息"""
        if not ic_analysis:
            return {}

        ic_stats = ic_analysis.get('ic_statistics', {})
        formatted_stats = {}

        for key, value in ic_stats.items():
            if isinstance(value, (int, float)):
                if 'ratio' in key or 'rate' in key:
                    formatted_stats[key] = ReportFormatter.format_percentage(value)
                else:
                    formatted_stats[key] = ReportFormatter.format_number(value, 4)
            else:
                formatted_stats[key] = value

        return formatted_stats

    @staticmethod
    def create_csv_export_data(evaluation_results: Dict) -> Dict[str, pd.DataFrame]:
        """创建CSV导出数据"""
        export_data = {}

        # 因子排序数据
        if 'factor_ranking' in evaluation_results:
            ranking_df = ReportFormatter.create_ranking_dataframe(evaluation_results)
            if not ranking_df.empty:
                export_data['factor_ranking'] = ranking_df

        # 因子详细数据
        if 'factor_details' in evaluation_results:
            details = evaluation_results['factor_details']
            if isinstance(details, dict):
                # 转换为适合CSV的格式
                detail_rows = []
                for factor_name, factor_data in details.items():
                    if isinstance(factor_data, dict):
                        row = {'factor_name': factor_name}
                        row.update(ReportFormatter._flatten_dict(factor_data))
                        detail_rows.append(row)

                if detail_rows:
                    export_data['factor_summary'] = pd.DataFrame(detail_rows)

        return export_data

    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ReportFormatter._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)):
                # 对于列表，只保留简单统计
                if v and isinstance(v[0], (int, float)):
                    items.append((f"{new_key}_mean", np.mean(v)))
                    items.append((f"{new_key}_count", len(v)))
                else:
                    items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def generate_timestamp() -> str:
        """生成时间戳"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    @staticmethod
    def clean_filename(filename: str) -> str:
        """清理文件名，移除特殊字符"""
        # 移除或替换不安全的文件名字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename