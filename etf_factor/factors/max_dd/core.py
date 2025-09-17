"""
MAX_DD核心计算模块
专注于最大回撤指标的算法实现
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加正确的项目路径
etf_factor_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, etf_factor_root)

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入MaxDdConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("max_dd_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MaxDdConfig = config_module.MaxDdConfig


class MAX_DD(BaseFactor):
    """最大回撤因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = MaxDdConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算最大回撤
        MAX_DD = (期间最高价 - 期间最低价) / 期间最高价 × 100%
        """
        result = data[['ts_code', 'trade_date']].copy()

        close_prices = data['hfq_close']

        # 计算各周期的最大回撤
        for period in self.params["periods"]:
            column_name = f'MAX_DD_{period}'

            def calculate_max_drawdown(prices):
                """计算单个窗口的最大回撤"""
                if len(prices) == 0:
                    return 0.0

                # 转换为pandas Series以使用expanding
                prices_series = pd.Series(prices)

                # 计算累计最高价
                cumulative_max = prices_series.expanding().max()

                # 计算回撤
                drawdown = (prices_series - cumulative_max) / cumulative_max

                # 返回最大回撤 (绝对值，转换为正数百分比)
                max_dd = abs(drawdown.min()) * 100
                return max_dd

            # 使用滚动窗口计算最大回撤
            max_dd_values = close_prices.rolling(
                window=period,
                min_periods=1
            ).apply(calculate_max_drawdown, raw=True)

            # 应用精度配置
            precision = config.get_precision('percentage')
            max_dd_values = max_dd_values.round(precision)

            result[column_name] = max_dd_values

        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('MAX_DD_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # 最大回撤应为正数
            result[col] = result[col].where(result[col] >= 0)

        return result

    def get_required_columns(self) -> list:
        return MaxDdConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return MaxDdConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + MaxDdConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            for period in self.params['periods']:
                col_name = f'MAX_DD_{period}'
                dd_values = result[col_name].dropna()

                if len(dd_values) == 0:
                    continue

                # 最大回撤应为正数且在合理范围内
                if (dd_values < 0).any() or (dd_values > 100).any():
                    return False

            return True

        except Exception:
            return False