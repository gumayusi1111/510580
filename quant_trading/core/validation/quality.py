"""
质量验证器 - 负责数据质量分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class QualityValidator:
    """数据质量验证器"""

    @staticmethod
    def validate_factor_data_quality(df: pd.DataFrame,
                                   factor_columns: List[str],
                                   min_coverage: float = 0.8,
                                   outlier_threshold: float = 3.0) -> Dict:
        """
        验证因子数据质量

        Args:
            df: 因子数据DataFrame
            factor_columns: 因子列名列表
            min_coverage: 最小数据覆盖率
            outlier_threshold: 异常值检测阈值(Z-score)

        Returns:
            质量验证结果
        """
        quality_result = {
            'quality_score': 0.0,
            'factor_analysis': {},
            'overall_statistics': {},
            'recommendations': []
        }

        try:
            factor_scores = []
            factor_analysis = {}

            for factor in factor_columns:
                if factor in df.columns:
                    analysis = QualityValidator._analyze_single_factor_quality(
                        df[factor], outlier_threshold
                    )
                    factor_analysis[factor] = analysis
                    factor_scores.append(analysis['quality_score'])

            # 计算总体质量得分
            if factor_scores:
                quality_result['quality_score'] = np.mean(factor_scores)

            # 总体统计
            quality_result['overall_statistics'] = {
                'total_factors': len(factor_columns),
                'valid_factors': len([f for f in factor_columns if f in df.columns]),
                'average_coverage': np.mean([
                    factor_analysis[f]['coverage'] for f in factor_analysis
                ]) if factor_analysis else 0,
                'high_quality_factors': len([
                    f for f, analysis in factor_analysis.items()
                    if analysis['quality_score'] > 0.7
                ])
            }

            quality_result['factor_analysis'] = factor_analysis

            # 生成建议
            quality_result['recommendations'] = QualityValidator._generate_quality_recommendations(
                factor_analysis
            )

        except Exception as e:
            logger.error(f"质量验证过程中发生错误: {e}")
            quality_result['error'] = str(e)

        return quality_result

    @staticmethod
    def _analyze_single_factor_quality(factor_series: pd.Series,
                                     outlier_threshold: float = 3.0) -> Dict:
        """
        分析单个因子的质量

        Args:
            factor_series: 因子数据序列
            outlier_threshold: 异常值阈值

        Returns:
            因子质量分析结果
        """
        analysis = {
            'quality_score': 0.0,
            'coverage': 0.0,
            'missing_ratio': 0.0,
            'outlier_ratio': 0.0,
            'stability_score': 0.0,
            'distribution_score': 0.0
        }

        try:
            # 基本统计
            total_count = len(factor_series)
            missing_count = factor_series.isnull().sum()
            valid_data = factor_series.dropna()

            analysis['coverage'] = len(valid_data) / total_count if total_count > 0 else 0
            analysis['missing_ratio'] = missing_count / total_count if total_count > 0 else 1

            if len(valid_data) > 0:
                # 确保数据是数值类型
                try:
                    valid_data = pd.to_numeric(valid_data, errors='coerce').dropna()
                except:
                    # 如果转换失败，说明数据包含非数值内容
                    analysis['quality_score'] = 0.0
                    analysis['coverage'] = 0.0
                    return analysis

                if len(valid_data) == 0:
                    return analysis

                # 异常值检测
                if valid_data.std() > 0:  # 避免除零错误
                    z_scores = np.abs((valid_data - valid_data.mean()) / valid_data.std())
                    outliers = z_scores > outlier_threshold
                    analysis['outlier_ratio'] = outliers.sum() / len(valid_data)
                else:
                    analysis['outlier_ratio'] = 0.0

                # 稳定性评分（基于变异系数）
                cv = valid_data.std() / abs(valid_data.mean()) if valid_data.mean() != 0 else float('inf')
                analysis['stability_score'] = max(0, 1 - min(cv / 2, 1))

                # 分布评分（基于偏度和峰度）
                try:
                    skewness = abs(valid_data.skew())
                    kurtosis = abs(valid_data.kurtosis())
                    # 正常分布的偏度为0，峰度为0，给出分布得分
                    analysis['distribution_score'] = max(0, 1 - (skewness + kurtosis) / 10)
                except:
                    analysis['distribution_score'] = 0.5

                # 综合质量得分
                coverage_weight = 0.4
                outlier_weight = 0.2
                stability_weight = 0.2
                distribution_weight = 0.2

                analysis['quality_score'] = (
                    analysis['coverage'] * coverage_weight +
                    (1 - analysis['outlier_ratio']) * outlier_weight +
                    analysis['stability_score'] * stability_weight +
                    analysis['distribution_score'] * distribution_weight
                )

        except Exception as e:
            logger.error(f"因子质量分析失败: {e}")

        return analysis

    @staticmethod
    def _generate_quality_recommendations(factor_analysis: Dict) -> List[str]:
        """
        基于因子分析结果生成改进建议

        Args:
            factor_analysis: 因子分析结果

        Returns:
            改进建议列表
        """
        recommendations = []

        for factor_name, analysis in factor_analysis.items():
            if analysis['missing_ratio'] > 0.2:
                recommendations.append(f"{factor_name}: 缺失数据过多({analysis['missing_ratio']:.1%})，建议检查数据源")

            if analysis['outlier_ratio'] > 0.1:
                recommendations.append(f"{factor_name}: 异常值较多({analysis['outlier_ratio']:.1%})，建议进行异常值处理")

            if analysis['stability_score'] < 0.5:
                recommendations.append(f"{factor_name}: 数据稳定性较差，建议检查计算逻辑")

            if analysis['quality_score'] < 0.6:
                recommendations.append(f"{factor_name}: 整体质量偏低({analysis['quality_score']:.2f})，建议重点关注")

        return recommendations