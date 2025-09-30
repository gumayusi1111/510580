"""
数据验证器主接口 - 整合所有验证功能
"""

import pandas as pd
from typing import Dict, List, Optional
import logging

from .structure import StructureValidator
from .quality import QualityValidator
from .continuity import ContinuityValidator

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器 - 重构版本主接口"""

    def __init__(self):
        """初始化验证器"""
        self.structure_validator = StructureValidator()
        self.quality_validator = QualityValidator()
        self.continuity_validator = ContinuityValidator()

    def validate_basic_structure(self, df: pd.DataFrame) -> Dict:
        """
        验证数据基本结构

        Args:
            df: 待验证的DataFrame

        Returns:
            验证结果字典
        """
        return self.structure_validator.validate_basic_structure(df)

    def validate_factor_data_quality(self, df: pd.DataFrame,
                                   factor_columns: List[str],
                                   min_coverage: float = 0.8,
                                   outlier_threshold: float = 3.0) -> Dict:
        """
        验证因子数据质量

        Args:
            df: 因子数据DataFrame
            factor_columns: 因子列名列表
            min_coverage: 最小数据覆盖率
            outlier_threshold: 异常值检测阈值

        Returns:
            质量验证结果
        """
        return self.quality_validator.validate_factor_data_quality(
            df, factor_columns, min_coverage, outlier_threshold
        )

    def validate_time_series_continuity(self, df: pd.DataFrame,
                                       date_column: str = 'trade_date',
                                       max_gap_days: int = 7) -> Dict:
        """
        验证时间序列连续性

        Args:
            df: 数据框
            date_column: 日期列名
            max_gap_days: 允许的最大间隔天数

        Returns:
            连续性验证结果
        """
        return self.continuity_validator.validate_time_series_continuity(
            df, date_column, max_gap_days
        )

    def comprehensive_validation(self, df: pd.DataFrame,
                               factor_columns: List[str] = None,
                               **kwargs) -> Dict:
        """
        全面数据验证

        Args:
            df: 待验证的数据框
            factor_columns: 因子列名列表
            **kwargs: 其他验证参数

        Returns:
            综合验证结果
        """
        validation_result = {
            'overall_status': 'passed',
            'structure_validation': {},
            'quality_validation': {},
            'continuity_validation': {},
            'summary': {},
            'recommendations': []
        }

        try:
            # 结构验证
            structure_result = self.validate_basic_structure(df)
            validation_result['structure_validation'] = structure_result

            if not structure_result['is_valid']:
                validation_result['overall_status'] = 'failed'

            # 质量验证
            if factor_columns:
                quality_result = self.validate_factor_data_quality(df, factor_columns)
                validation_result['quality_validation'] = quality_result

                if quality_result.get('quality_score', 0) < 0.6:
                    validation_result['overall_status'] = 'warning'

            # 连续性验证
            continuity_result = self.validate_time_series_continuity(df)
            validation_result['continuity_validation'] = continuity_result

            if not continuity_result['is_continuous']:
                if validation_result['overall_status'] == 'passed':
                    validation_result['overall_status'] = 'warning'

            # 汇总信息
            validation_result['summary'] = self._generate_summary(
                structure_result,
                validation_result.get('quality_validation', {}),
                continuity_result
            )

            # 综合建议
            validation_result['recommendations'] = self._generate_comprehensive_recommendations(
                validation_result
            )

        except Exception as e:
            logger.error(f"综合验证过程中发生错误: {e}")
            validation_result['overall_status'] = 'error'
            validation_result['error'] = str(e)

        return validation_result

    def _generate_summary(self, structure_result: Dict,
                         quality_result: Dict,
                         continuity_result: Dict) -> Dict:
        """生成验证摘要"""
        summary = {
            'total_rows': structure_result.get('statistics', {}).get('total_rows', 0),
            'total_columns': structure_result.get('statistics', {}).get('total_columns', 0),
            'structure_valid': structure_result.get('is_valid', False),
            'quality_score': quality_result.get('quality_score', 0),
            'time_continuity': continuity_result.get('is_continuous', False),
            'coverage_ratio': continuity_result.get('coverage_ratio', 0)
        }
        return summary

    def _generate_comprehensive_recommendations(self, validation_result: Dict) -> List[str]:
        """生成综合建议"""
        recommendations = []

        # 从各个验证模块收集建议
        structure_errors = validation_result.get('structure_validation', {}).get('errors', [])
        for error in structure_errors:
            recommendations.append(f"[结构] {error}")

        quality_recs = validation_result.get('quality_validation', {}).get('recommendations', [])
        for rec in quality_recs:
            recommendations.append(f"[质量] {rec}")

        continuity_recs = validation_result.get('continuity_validation', {}).get('recommendations', [])
        for rec in continuity_recs:
            recommendations.append(f"[连续性] {rec}")

        # 根据总体状态添加建议
        if validation_result['overall_status'] == 'failed':
            recommendations.append("[总体] 数据存在严重问题，建议先解决结构性错误")
        elif validation_result['overall_status'] == 'warning':
            recommendations.append("[总体] 数据质量有待改善，建议优先处理质量问题")

        return recommendations