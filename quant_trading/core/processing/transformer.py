"""
数据转换器 - 负责数据合并、筛选和重采样
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """数据转换器"""

    @staticmethod
    def merge_factor_data(technical_df: pd.DataFrame,
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
        try:
            if technical_df.empty:
                logger.warning("技术因子数据为空")
                return pd.DataFrame()

            # 从技术因子开始
            merged_df = technical_df.copy()

            # 确保有日期列用于合并
            if 'trade_date' not in merged_df.columns:
                logger.error("技术因子数据缺少trade_date列")
                return pd.DataFrame()

            # 合并基本面数据
            if fundamental_df is not None and not fundamental_df.empty:
                if 'trade_date' in fundamental_df.columns:
                    merged_df = pd.merge(
                        merged_df,
                        fundamental_df,
                        on=['ts_code', 'trade_date'],
                        how='left',
                        suffixes=('', '_fund')
                    )
                    logger.info(f"合并基本面数据: {len(fundamental_df.columns)} 列")
                else:
                    logger.warning("基本面数据缺少trade_date列，跳过合并")

            # 合并宏观数据
            if macro_df is not None and not macro_df.empty:
                if 'trade_date' in macro_df.columns:
                    # 宏观数据通常没有ts_code，只按日期合并
                    macro_columns = [col for col in macro_df.columns if col != 'trade_date']
                    macro_data = macro_df[['trade_date'] + macro_columns].drop_duplicates('trade_date')

                    merged_df = pd.merge(
                        merged_df,
                        macro_data,
                        on='trade_date',
                        how='left',
                        suffixes=('', '_macro')
                    )
                    logger.info(f"合并宏观数据: {len(macro_columns)} 列")
                else:
                    logger.warning("宏观数据缺少trade_date列，跳过合并")

            # 按日期排序
            merged_df = merged_df.sort_values('trade_date')

            logger.info(f"因子数据合并完成: {merged_df.shape}")

        except Exception as e:
            logger.error(f"因子数据合并失败: {e}")
            return technical_df

        return merged_df

    @staticmethod
    def filter_factor_data(df: pd.DataFrame, factors: List[str]) -> pd.DataFrame:
        """
        筛选指定因子数据

        Args:
            df: 完整因子数据
            factors: 要筛选的因子列表

        Returns:
            筛选后的因子数据
        """
        try:
            if df.empty:
                return df

            # 保留必要的标识列
            base_columns = ['ts_code', 'trade_date']
            available_base = [col for col in base_columns if col in df.columns]

            # 检查因子列是否存在
            available_factors = [factor for factor in factors if factor in df.columns]
            missing_factors = [factor for factor in factors if factor not in df.columns]

            if missing_factors:
                logger.warning(f"以下因子不存在: {missing_factors}")

            if not available_factors:
                logger.error("没有可用的因子列")
                return pd.DataFrame()

            # 选择列并去除重复
            selected_columns = available_base + available_factors
            # 去除重复的列名
            selected_columns = list(dict.fromkeys(selected_columns))  # 保持顺序的去重
            filtered_df = df[selected_columns].copy()

            # 检查DataFrame中是否有重复的列
            if filtered_df.columns.duplicated().any():
                # 移除重复列，保留第一个
                filtered_df = filtered_df.loc[:, ~filtered_df.columns.duplicated()]
                logger.warning("检测到并移除了重复列")

            logger.info(f"因子筛选完成: {len(available_factors)}/{len(factors)} 个因子")

        except Exception as e:
            logger.error(f"因子筛选失败: {e}")
            return pd.DataFrame()

        return filtered_df

    @staticmethod
    def resample_data(df: pd.DataFrame,
                     freq: str = 'D',
                     date_column: str = 'trade_date',
                     agg_method: str = 'last') -> pd.DataFrame:
        """
        重采样数据

        Args:
            df: 输入数据框
            freq: 重采样频率 ('D', 'W', 'M', 'Q', 'Y')
            date_column: 日期列名
            agg_method: 聚合方法

        Returns:
            重采样后的数据框
        """
        try:
            if df.empty:
                return df

            if date_column not in df.columns:
                logger.error(f"日期列 {date_column} 不存在")
                return df

            # 确保日期列为datetime类型
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column])

            # 设置日期为索引
            df_copy = df_copy.set_index(date_column)

            # 分离数值列和非数值列
            numeric_columns = df_copy.select_dtypes(include=[np.number]).columns
            non_numeric_columns = df_copy.select_dtypes(exclude=[np.number]).columns

            resampled_data = {}

            # 处理数值列
            if len(numeric_columns) > 0:
                if agg_method == 'last':
                    numeric_resampled = df_copy[numeric_columns].resample(freq).last()
                elif agg_method == 'first':
                    numeric_resampled = df_copy[numeric_columns].resample(freq).first()
                elif agg_method == 'mean':
                    numeric_resampled = df_copy[numeric_columns].resample(freq).mean()
                elif agg_method == 'sum':
                    numeric_resampled = df_copy[numeric_columns].resample(freq).sum()
                else:
                    numeric_resampled = df_copy[numeric_columns].resample(freq).last()

                resampled_data.update(numeric_resampled.to_dict('series'))

            # 处理非数值列（通常使用last）
            if len(non_numeric_columns) > 0:
                non_numeric_resampled = df_copy[non_numeric_columns].resample(freq).last()
                resampled_data.update(non_numeric_resampled.to_dict('series'))

            # 重建DataFrame
            resampled_df = pd.DataFrame(resampled_data)
            resampled_df = resampled_df.reset_index()

            logger.info(f"数据重采样完成: {len(df)} -> {len(resampled_df)} 行")

        except Exception as e:
            logger.error(f"数据重采样失败: {e}")
            return df

        return resampled_df

    @staticmethod
    def pivot_data(df: pd.DataFrame,
                  index_cols: List[str],
                  value_cols: List[str] = None,
                  pivot_col: str = None) -> pd.DataFrame:
        """
        数据透视转换

        Args:
            df: 输入数据框
            index_cols: 索引列
            value_cols: 值列
            pivot_col: 透视列

        Returns:
            透视后的数据框
        """
        try:
            if df.empty:
                return df

            if pivot_col and pivot_col in df.columns:
                # 执行透视
                if value_cols is None:
                    value_cols = df.select_dtypes(include=[np.number]).columns.tolist()

                pivoted_df = df.pivot_table(
                    index=index_cols,
                    columns=pivot_col,
                    values=value_cols,
                    aggfunc='mean'
                )

                # 扁平化列名
                if isinstance(pivoted_df.columns, pd.MultiIndex):
                    pivoted_df.columns = ['_'.join(map(str, col)).strip() for col in pivoted_df.columns]

                pivoted_df = pivoted_df.reset_index()
                logger.info(f"数据透视完成: {pivoted_df.shape}")

            else:
                logger.warning("无法执行透视转换")
                pivoted_df = df

        except Exception as e:
            logger.error(f"数据透视失败: {e}")
            return df

        return pivoted_df