"""
基本面因子数据加载器
"""

import pandas as pd
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class FundamentalLoader:
    """基本面因子数据加载器"""

    def __init__(self, factor_data_path: Path):
        """初始化基本面因子加载器"""
        self.factor_data_path = factor_data_path

    def load_fundamental_factors(self, etf_code: str) -> pd.DataFrame:
        """
        加载基本面因子数据

        Args:
            etf_code: ETF代码

        Returns:
            基本面因子数据DataFrame
        """
        fundamental_path = self.factor_data_path / "fundamental" / etf_code

        if not fundamental_path.exists():
            logger.warning(f"基本面因子目录不存在: {fundamental_path}")
            return pd.DataFrame()

        all_factors = pd.DataFrame()
        factor_files = list(fundamental_path.glob("*.csv"))

        if not factor_files:
            logger.warning(f"基本面因子目录为空: {fundamental_path}")
            return pd.DataFrame()

        try:
            for factor_file in factor_files:
                factor_name = factor_file.stem
                factor_df = pd.read_csv(factor_file)

                # 验证数据格式
                if 'trade_date' not in factor_df.columns:
                    logger.warning(f"基本面因子文件缺少trade_date列: {factor_file}")
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

            logger.info(f"基本面因子加载完成: {etf_code}, 总因子数: {len(factor_files)}, 形状: {all_factors.shape}")

        except Exception as e:
            logger.error(f"基本面因子加载失败 {etf_code}: {e}")
            return pd.DataFrame()

        return all_factors

    def get_fundamental_factor_list(self, etf_code: str) -> List[str]:
        """
        获取基本面因子列表

        Args:
            etf_code: ETF代码

        Returns:
            基本面因子名称列表
        """
        fundamental_path = self.factor_data_path / "fundamental" / etf_code

        if not fundamental_path.exists():
            return []

        factor_files = list(fundamental_path.glob("*.csv"))
        factor_names = [f.stem for f in factor_files]

        logger.debug(f"基本面因子列表: {etf_code}, 共{len(factor_names)}个因子")
        return factor_names

    def load_single_fundamental_factor(self, factor_name: str, etf_code: str) -> pd.DataFrame:
        """
        加载单个基本面因子

        Args:
            factor_name: 因子名称
            etf_code: ETF代码

        Returns:
            单个因子数据DataFrame
        """
        factor_file = self.factor_data_path / "fundamental" / etf_code / f"{factor_name}.csv"

        if not factor_file.exists():
            logger.warning(f"基本面因子文件不存在: {factor_file}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(factor_file)
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            logger.debug(f"单个基本面因子加载完成: {factor_name}")
            return df

        except Exception as e:
            logger.error(f"单个基本面因子加载失败 {factor_name}: {e}")
            return pd.DataFrame()

    def load_financial_statements(self, etf_code: str, statement_type: str = "income") -> pd.DataFrame:
        """
        加载财务报表数据

        Args:
            etf_code: ETF代码
            statement_type: 报表类型 (income, balance, cashflow)

        Returns:
            财务报表数据DataFrame
        """
        statement_path = self.factor_data_path / "fundamental" / etf_code / f"{statement_type}_statement.csv"

        if not statement_path.exists():
            logger.warning(f"财务报表文件不存在: {statement_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(statement_path)
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'])
            logger.info(f"财务报表加载完成: {etf_code} - {statement_type}")
            return df

        except Exception as e:
            logger.error(f"财务报表加载失败 {etf_code} - {statement_type}: {e}")
            return pd.DataFrame()

    def get_available_statements(self, etf_code: str) -> List[str]:
        """
        获取可用的财务报表类型

        Args:
            etf_code: ETF代码

        Returns:
            可用报表类型列表
        """
        fundamental_path = self.factor_data_path / "fundamental" / etf_code

        if not fundamental_path.exists():
            return []

        statement_files = list(fundamental_path.glob("*_statement.csv"))
        statement_types = [f.stem.replace('_statement', '') for f in statement_files]

        return statement_types