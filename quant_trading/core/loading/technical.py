"""
技术因子数据加载器
"""

import pandas as pd
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class TechnicalLoader:
    """技术因子数据加载器"""

    def __init__(self, factor_data_path: Path):
        """初始化技术因子加载器"""
        self.factor_data_path = factor_data_path

    def load_complete_factors_file(self, etf_code: str) -> pd.DataFrame:
        """
        从complete目录加载完整因子数据

        Args:
            etf_code: ETF代码

        Returns:
            完整因子数据DataFrame
        """
        complete_path = self.factor_data_path / "technical" / "complete" / f"{etf_code}_complete_factors.csv"

        if complete_path.exists():
            try:
                df = pd.read_csv(complete_path)
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                logger.info(f"从complete目录加载因子数据: {etf_code}, 形状: {df.shape}")
                return df
            except Exception as e:
                logger.error(f"加载complete因子数据失败 {etf_code}: {e}")
                return pd.DataFrame()
        else:
            logger.warning(f"Complete因子文件不存在: {complete_path}")
            return pd.DataFrame()

    def load_technical_factors(self, etf_code: str) -> pd.DataFrame:
        """
        加载技术因子数据

        Args:
            etf_code: ETF代码

        Returns:
            技术因子数据DataFrame
        """
        technical_path = self.factor_data_path / "technical" / etf_code

        if not technical_path.exists():
            logger.warning(f"技术因子目录不存在: {technical_path}")
            return pd.DataFrame()

        all_factors = pd.DataFrame()
        factor_files = list(technical_path.glob("*.csv"))

        if not factor_files:
            logger.warning(f"技术因子目录为空: {technical_path}")
            return pd.DataFrame()

        try:
            for factor_file in factor_files:
                factor_name = factor_file.stem
                factor_df = pd.read_csv(factor_file)

                # 验证数据格式
                if 'trade_date' not in factor_df.columns:
                    logger.warning(f"因子文件缺少trade_date列: {factor_file}")
                    continue

                # 转换日期格式
                factor_df['trade_date'] = pd.to_datetime(factor_df['trade_date'], format='%Y%m%d')

                # 重命名值列
                if 'value' in factor_df.columns:
                    factor_df = factor_df.rename(columns={'value': factor_name})

                # 合并数据
                if all_factors.empty:
                    all_factors = factor_df.copy()
                else:
                    merge_cols = ['ts_code', 'trade_date']
                    all_factors = pd.merge(
                        all_factors,
                        factor_df,
                        on=merge_cols,
                        how='outer'
                    )

            logger.info(f"技术因子加载完成: {etf_code}, 总因子数: {len(factor_files)}, 形状: {all_factors.shape}")

        except Exception as e:
            logger.error(f"技术因子加载失败 {etf_code}: {e}")
            return pd.DataFrame()

        return all_factors

    def get_technical_factor_list(self, etf_code: str) -> List[str]:
        """
        获取技术因子列表

        Args:
            etf_code: ETF代码

        Returns:
            技术因子名称列表
        """
        technical_path = self.factor_data_path / "technical" / etf_code

        if not technical_path.exists():
            return []

        factor_files = list(technical_path.glob("*.csv"))
        factor_names = [f.stem for f in factor_files]

        logger.debug(f"技术因子列表: {etf_code}, 共{len(factor_names)}个因子")
        return factor_names

    def load_single_technical_factor(self, factor_name: str, etf_code: str) -> pd.DataFrame:
        """
        加载单个技术因子

        Args:
            factor_name: 因子名称
            etf_code: ETF代码

        Returns:
            单个因子数据DataFrame
        """
        factor_file = self.factor_data_path / "technical" / etf_code / f"{factor_name}.csv"

        if not factor_file.exists():
            logger.warning(f"技术因子文件不存在: {factor_file}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(factor_file)
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            logger.debug(f"单个技术因子加载完成: {factor_name}")
            return df

        except Exception as e:
            logger.error(f"单个技术因子加载失败 {factor_name}: {e}")
            return pd.DataFrame()