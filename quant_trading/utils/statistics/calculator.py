"""
统计计算器 - FactorStatistics类
基本统计量计算和分布分析
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class FactorStatistics:
    """因子统计分析器"""

    @staticmethod
    def calculate_basic_statistics(factor_series: pd.Series) -> Dict:
        """
        计算因子基本统计量

        Args:
            factor_series: 因子数据序列

        Returns:
            基本统计量字典
        """
        clean_data = factor_series.dropna()

        if clean_data.empty:
            return {'error': 'no_valid_data'}

        try:
            return {
                'count': len(clean_data),
                'missing_ratio': factor_series.isnull().mean(),
                'mean': float(clean_data.mean()),
                'std': float(clean_data.std()),
                'min': float(clean_data.min()),
                'max': float(clean_data.max()),
                'median': float(clean_data.median()),
                'skewness': float(clean_data.skew()),
                'kurtosis': float(clean_data.kurtosis()),
                'q25': float(clean_data.quantile(0.25)),
                'q75': float(clean_data.quantile(0.75)),
                'iqr': float(clean_data.quantile(0.75) - clean_data.quantile(0.25))
            }

        except Exception as e:
            logger.error(f"基本统计计算失败: {e}")
            return {'error': 'calculation_failed'}

    @staticmethod
    def analyze_distribution(factor_series: pd.Series) -> Dict:
        """
        分析因子数据分布

        Args:
            factor_series: 因子数据序列

        Returns:
            分布分析结果
        """
        clean_data = factor_series.dropna()

        if clean_data.empty:
            return {'error': 'no_valid_data'}

        try:
            # 基本分布特征
            mean_val = clean_data.mean()
            std_val = clean_data.std()

            # 异常值检测 (IQR方法)
            q25 = clean_data.quantile(0.25)
            q75 = clean_data.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]

            # 变异系数
            cv = std_val / abs(mean_val) if mean_val != 0 else np.inf

            return {
                'distribution': {
                    'skewness': float(clean_data.skew()),
                    'kurtosis': float(clean_data.kurtosis()),
                    'is_normal': abs(clean_data.skew()) < 0.5 and abs(clean_data.kurtosis()) < 3,
                    'jarque_bera_p': None  # 可以后续添加正态性测试
                },
                'outlier_analysis': {
                    'outlier_count': len(outliers),
                    'outlier_ratio': len(outliers) / len(clean_data),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound)
                },
                'variability': {
                    'range': float(clean_data.max() - clean_data.min()),
                    'coefficient_of_variation': float(cv) if not np.isinf(cv) else None,
                    'interquartile_range': float(iqr)
                }
            }

        except Exception as e:
            logger.error(f"分布分析失败: {e}")
            return {'error': 'analysis_failed'}

    @staticmethod
    def analyze_factor_stability(factor_series: pd.Series, window: int = 60) -> Dict:
        """
        分析因子稳定性

        Args:
            factor_series: 因子数据序列
            window: 滚动窗口大小（默认60日）

        Returns:
            稳定性分析结果
        """
        clean_data = factor_series.dropna()

        if len(clean_data) < window:
            return {
                'stability_score': 0.0,
                'reason': 'insufficient_data',
                'required_length': window,
                'actual_length': len(clean_data)
            }

        try:
            # 滚动统计
            rolling_mean = clean_data.rolling(window).mean()
            rolling_std = clean_data.rolling(window).std()

            # 稳定性指标
            mean_stability = 1 - (rolling_mean.std() / rolling_mean.mean()) if rolling_mean.mean() != 0 else 0
            std_stability = 1 - (rolling_std.std() / rolling_std.mean()) if rolling_std.mean() != 0 else 0

            # 时间趋势分析
            time_index = np.arange(len(clean_data))
            correlation_with_time = np.corrcoef(time_index, clean_data)[0, 1]

            # 自相关分析
            autocorr_lags = [5, 10, 20, 60]  # 周、双周、月、季度
            autocorrelations = {}

            for lag in autocorr_lags:
                if len(clean_data) > lag:
                    try:
                        autocorr = clean_data.autocorr(lag)
                        autocorrelations[f'lag_{lag}'] = float(autocorr) if not pd.isna(autocorr) else 0.0
                    except:
                        autocorrelations[f'lag_{lag}'] = 0.0

            # 综合稳定性评分
            stability_score = max(0, min(1, (mean_stability + std_stability) / 2))

            return {
                'stability_score': float(stability_score),
                'mean_stability': float(mean_stability),
                'std_stability': float(std_stability),
                'trend_analysis': {
                    'time_correlation': float(correlation_with_time),
                    'has_significant_trend': abs(correlation_with_time) > 0.3
                },
                'autocorrelation': autocorrelations,
                'evaluation_window': window
            }

        except Exception as e:
            logger.error(f"稳定性分析失败: {e}")
            return {'error': 'stability_analysis_failed'}