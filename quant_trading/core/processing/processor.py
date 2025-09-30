"""
数据处理器主接口 - 整合所有处理功能
"""

import pandas as pd
from typing import Dict, List, Optional
import logging

from .cleaner import DataCleaner
from .calculator import DataCalculator
from .transformer import DataTransformer

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器 - 重构版本主接口"""

    def __init__(self):
        """初始化处理器"""
        self.cleaner = DataCleaner()
        self.calculator = DataCalculator()
        self.transformer = DataTransformer()

    def clean_data(self, df: pd.DataFrame, method: str = "forward_fill") -> pd.DataFrame:
        """
        清洗数据

        Args:
            df: 输入数据框
            method: 清洗方法

        Returns:
            清洗后的数据框
        """
        return self.cleaner.clean_data(df, method)

    def merge_factor_data(self, technical_df: pd.DataFrame,
                         fundamental_df: pd.DataFrame = None,
                         macro_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        合并因子数据

        Args:
            technical_df: 技术因子数据
            fundamental_df: 基本面因子数据
            macro_df: 宏观因子数据

        Returns:
            合并后的因子数据
        """
        return self.transformer.merge_factor_data(technical_df, fundamental_df, macro_df)

    def calculate_returns(self, df: pd.DataFrame, price_column: str = 'close') -> pd.Series:
        """
        计算收益率

        Args:
            df: 价格数据框
            price_column: 价格列名

        Returns:
            收益率序列
        """
        return self.calculator.calculate_returns(df, price_column)

    def get_data_statistics(self, df: pd.DataFrame) -> Dict:
        """
        获取数据统计信息

        Args:
            df: 数据框

        Returns:
            统计信息字典
        """
        return self.calculator.get_data_statistics(df)

    def filter_factor_data(self, df: pd.DataFrame, factors: List[str]) -> pd.DataFrame:
        """
        筛选指定因子数据

        Args:
            df: 完整因子数据
            factors: 要筛选的因子列表

        Returns:
            筛选后的因子数据
        """
        return self.transformer.filter_factor_data(df, factors)

    def resample_data(self, df: pd.DataFrame,
                     freq: str = 'D',
                     date_column: str = 'trade_date',
                     agg_method: str = 'last') -> pd.DataFrame:
        """
        重采样数据

        Args:
            df: 输入数据框
            freq: 重采样频率
            date_column: 日期列名
            agg_method: 聚合方法

        Returns:
            重采样后的数据框
        """
        return self.transformer.resample_data(df, freq, date_column, agg_method)

    # 添加更多组合方法
    def standardize_and_clean(self, df: pd.DataFrame,
                            clean_method: str = "forward_fill",
                            std_method: str = "zscore") -> pd.DataFrame:
        """
        数据清洗和标准化组合

        Args:
            df: 输入数据框
            clean_method: 清洗方法
            std_method: 标准化方法

        Returns:
            处理后的数据框
        """
        # 先清洗
        cleaned_df = self.cleaner.clean_data(df, clean_method)

        # 再标准化
        standardized_df = self.cleaner.standardize_data(cleaned_df, method=std_method)

        return standardized_df

    def comprehensive_processing(self, df: pd.DataFrame, **kwargs) -> Dict:
        """
        综合数据处理

        Args:
            df: 输入数据框
            **kwargs: 处理参数

        Returns:
            处理结果字典
        """
        result = {
            'processed_data': pd.DataFrame(),
            'statistics': {},
            'processing_log': [],
            'success': False
        }

        try:
            # 数据清洗
            clean_method = kwargs.get('clean_method', 'forward_fill')
            processed_df = self.clean_data(df, clean_method)
            result['processing_log'].append(f"数据清洗完成: {clean_method}")

            # 异常值处理
            if kwargs.get('remove_outliers', False):
                outlier_method = kwargs.get('outlier_method', 'iqr')
                processed_df = self.cleaner.remove_outliers(processed_df, method=outlier_method)
                result['processing_log'].append(f"异常值处理完成: {outlier_method}")

            # 数据标准化
            if kwargs.get('standardize', False):
                std_method = kwargs.get('std_method', 'zscore')
                processed_df = self.cleaner.standardize_data(processed_df, method=std_method)
                result['processing_log'].append(f"数据标准化完成: {std_method}")

            # 数据重采样
            if kwargs.get('resample', False):
                freq = kwargs.get('freq', 'D')
                processed_df = self.resample_data(processed_df, freq=freq)
                result['processing_log'].append(f"数据重采样完成: {freq}")

            result['processed_data'] = processed_df
            result['statistics'] = self.get_data_statistics(processed_df)
            result['success'] = True

        except Exception as e:
            logger.error(f"综合数据处理失败: {e}")
            result['error'] = str(e)

        return result