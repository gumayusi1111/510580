"""
数据清洗器 - 负责数据清洗和预处理
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_data(df: pd.DataFrame, method: str = "forward_fill") -> pd.DataFrame:
        """
        清洗数据

        Args:
            df: 输入数据框
            method: 清洗方法 ('forward_fill', 'backward_fill', 'interpolate', 'drop')

        Returns:
            清洗后的数据框
        """
        if df.empty:
            return df

        cleaned_df = df.copy()

        try:
            # 移除重复行
            cleaned_df = cleaned_df.drop_duplicates()

            # 处理异常字符串数据（清理重复字符）
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    # 检测并清理重复字符的异常数据
                    mask = cleaned_df[col].astype(str).str.len() > 100  # 异常长的字符串
                    if mask.any():
                        logger.warning(f"发现异常字符串数据在列 {col}，将其设为NaN")
                        cleaned_df.loc[mask, col] = np.nan

            # 处理无穷大值
            cleaned_df = cleaned_df.replace([np.inf, -np.inf], np.nan)

            # 根据方法处理缺失值
            if method == "forward_fill":
                cleaned_df = cleaned_df.ffill()
            elif method == "backward_fill":
                cleaned_df = cleaned_df.bfill()
            elif method == "interpolate":
                # 只对数值列进行插值
                numeric_columns = cleaned_df.select_dtypes(include=[np.number]).columns
                cleaned_df[numeric_columns] = cleaned_df[numeric_columns].interpolate()
            elif method == "drop":
                cleaned_df = cleaned_df.dropna()

            # 确保日期列格式正确
            if 'trade_date' in cleaned_df.columns:
                cleaned_df['trade_date'] = pd.to_datetime(cleaned_df['trade_date'])

            logger.info(f"数据清洗完成: {len(df)} -> {len(cleaned_df)} 行")

        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return df

        return cleaned_df

    @staticmethod
    def remove_outliers(df: pd.DataFrame,
                       columns: List[str] = None,
                       method: str = "iqr",
                       threshold: float = 3.0) -> pd.DataFrame:
        """
        移除异常值

        Args:
            df: 数据框
            columns: 要处理的列名，None表示所有数值列
            method: 异常值检测方法 ('iqr', 'zscore')
            threshold: 阈值

        Returns:
            处理后的数据框
        """
        if df.empty:
            return df

        cleaned_df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        try:
            for col in columns:
                if col not in df.columns:
                    continue

                if method == "iqr":
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR

                    outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)

                elif method == "zscore":
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    outlier_mask = z_scores > threshold

                # 将异常值设为NaN
                cleaned_df.loc[outlier_mask, col] = np.nan

            logger.info(f"异常值处理完成，方法: {method}")

        except Exception as e:
            logger.error(f"异常值处理失败: {e}")
            return df

        return cleaned_df

    @staticmethod
    def standardize_data(df: pd.DataFrame,
                        columns: List[str] = None,
                        method: str = "zscore") -> pd.DataFrame:
        """
        数据标准化

        Args:
            df: 数据框
            columns: 要标准化的列
            method: 标准化方法 ('zscore', 'minmax', 'robust')

        Returns:
            标准化后的数据框
        """
        if df.empty:
            return df

        standardized_df = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        try:
            for col in columns:
                if col not in df.columns:
                    continue

                if method == "zscore":
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    if std_val != 0:
                        standardized_df[col] = (df[col] - mean_val) / std_val

                elif method == "minmax":
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val != min_val:
                        standardized_df[col] = (df[col] - min_val) / (max_val - min_val)

                elif method == "robust":
                    median_val = df[col].median()
                    mad_val = (df[col] - median_val).abs().median()
                    if mad_val != 0:
                        standardized_df[col] = (df[col] - median_val) / mad_val

            logger.info(f"数据标准化完成，方法: {method}")

        except Exception as e:
            logger.error(f"数据标准化失败: {e}")
            return df

        return standardized_df