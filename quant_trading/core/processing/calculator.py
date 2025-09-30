"""
数据计算器 - 负责数据计算和统计
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataCalculator:
    """数据计算器"""

    @staticmethod
    def calculate_returns(df: pd.DataFrame, price_column: str = 'close') -> pd.Series:
        """
        计算收益率

        Args:
            df: 价格数据框
            price_column: 价格列名

        Returns:
            收益率序列
        """
        try:
            if price_column not in df.columns:
                logger.error(f"价格列 {price_column} 不存在")
                return pd.Series()

            prices = df[price_column].dropna()
            if len(prices) < 2:
                logger.warning("价格数据不足，无法计算收益率")
                return pd.Series()

            # 计算简单收益率
            returns = prices.pct_change().dropna()

            logger.info(f"收益率计算完成，共 {len(returns)} 个数据点")
            return returns

        except Exception as e:
            logger.error(f"收益率计算失败: {e}")
            return pd.Series()

    @staticmethod
    def calculate_log_returns(df: pd.DataFrame, price_column: str = 'close') -> pd.Series:
        """
        计算对数收益率

        Args:
            df: 价格数据框
            price_column: 价格列名

        Returns:
            对数收益率序列
        """
        try:
            if price_column not in df.columns:
                logger.error(f"价格列 {price_column} 不存在")
                return pd.Series()

            prices = df[price_column].dropna()
            if len(prices) < 2:
                logger.warning("价格数据不足，无法计算对数收益率")
                return pd.Series()

            # 计算对数收益率
            log_returns = np.log(prices / prices.shift(1)).dropna()

            logger.info(f"对数收益率计算完成，共 {len(log_returns)} 个数据点")
            return log_returns

        except Exception as e:
            logger.error(f"对数收益率计算失败: {e}")
            return pd.Series()

    @staticmethod
    def calculate_rolling_statistics(series: pd.Series,
                                   window: int = 20,
                                   statistics: list = None) -> pd.DataFrame:
        """
        计算滚动统计指标

        Args:
            series: 数据序列
            window: 滚动窗口大小
            statistics: 要计算的统计指标列表

        Returns:
            滚动统计结果DataFrame
        """
        if statistics is None:
            statistics = ['mean', 'std', 'min', 'max']

        result_dict = {}

        try:
            for stat in statistics:
                if stat == 'mean':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).mean()
                elif stat == 'std':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).std()
                elif stat == 'min':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).min()
                elif stat == 'max':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).max()
                elif stat == 'median':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).median()
                elif stat == 'skew':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).skew()
                elif stat == 'kurt':
                    result_dict[f'rolling_{stat}_{window}'] = series.rolling(window).kurt()

            result_df = pd.DataFrame(result_dict, index=series.index)
            logger.info(f"滚动统计计算完成，窗口: {window}")

        except Exception as e:
            logger.error(f"滚动统计计算失败: {e}")
            result_df = pd.DataFrame()

        return result_df

    @staticmethod
    def get_data_statistics(df: pd.DataFrame) -> Dict:
        """
        获取数据基本统计信息

        Args:
            df: 数据框

        Returns:
            统计信息字典
        """
        try:
            if df.empty:
                return {}

            stats = {
                'shape': df.shape,
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'missing_data_ratio': df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
            }

            # 日期范围
            if 'trade_date' in df.columns:
                try:
                    dates = pd.to_datetime(df['trade_date'])
                    stats['date_range'] = [
                        dates.min().strftime('%Y-%m-%d'),
                        dates.max().strftime('%Y-%m-%d')
                    ]
                    stats['trading_days'] = len(dates.unique())
                except:
                    stats['date_range'] = [None, None]
                    stats['trading_days'] = 0
            else:
                stats['date_range'] = [None, None]
                stats['trading_days'] = 0

            # 数值列统计
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                numeric_stats = df[numeric_columns].describe()
                stats['numeric_summary'] = {
                    'columns': len(numeric_columns),
                    'mean_values': numeric_stats.loc['mean'].to_dict(),
                    'std_values': numeric_stats.loc['std'].to_dict(),
                    'missing_by_column': df[numeric_columns].isnull().sum().to_dict()
                }

            logger.debug("数据统计信息计算完成")

        except Exception as e:
            logger.error(f"统计信息计算失败: {e}")
            stats = {'error': str(e)}

        return stats

    @staticmethod
    def calculate_correlation_matrix(df: pd.DataFrame,
                                   columns: list = None,
                                   method: str = 'pearson') -> pd.DataFrame:
        """
        计算相关性矩阵

        Args:
            df: 数据框
            columns: 要计算相关性的列名列表
            method: 相关性计算方法

        Returns:
            相关性矩阵
        """
        try:
            if columns is None:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()

            # 移除非数值列
            valid_columns = [col for col in columns if col in df.columns]
            if not valid_columns:
                return pd.DataFrame()

            # 计算相关性矩阵（抑制RuntimeWarning）
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                correlation_matrix = df[valid_columns].corr(method=method)
            logger.info(f"相关性矩阵计算完成，方法: {method}")

            return correlation_matrix

        except Exception as e:
            logger.error(f"相关性矩阵计算失败: {e}")
            return pd.DataFrame()