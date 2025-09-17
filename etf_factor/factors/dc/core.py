"""
DC核心计算模块
专注于唐奇安通道指标的算法实现
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

# 导入DcConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("dc_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
DcConfig = config_module.DcConfig


class DC(BaseFactor):
    """唐奇安通道因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = DcConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算唐奇安通道
        DC_UPPER = MAX(最高价, period)  - 上轨：N日内最高价
        DC_LOWER = MIN(最低价, period)  - 下轨：N日内最低价
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格数据
        high_prices = data['hfq_high']
        low_prices = data['hfq_low']

        period = self.params["period"]

        # 向量化计算唐奇安通道
        # 上轨：N日内最高价
        dc_upper = high_prices.rolling(window=period, min_periods=1).max()

        # 下轨：N日内最低价
        dc_lower = low_prices.rolling(window=period, min_periods=1).min()

        # 应用全局精度配置
        precision = config.get_precision('indicator')
        dc_upper = dc_upper.round(precision)
        dc_lower = dc_lower.round(precision)

        # 添加到结果
        result[f'DC_UPPER_{period}'] = dc_upper
        result[f'DC_LOWER_{period}'] = dc_lower

        # 数据验证和清理
        # 确保上轨 >= 下轨
        mask = result[f'DC_UPPER_{period}'] < result[f'DC_LOWER_{period}']
        if mask.any():
            # 交换异常值
            temp = result.loc[mask, f'DC_UPPER_{period}'].copy()
            result.loc[mask, f'DC_UPPER_{period}'] = result.loc[mask, f'DC_LOWER_{period}']
            result.loc[mask, f'DC_LOWER_{period}'] = temp

        return result

    def get_required_columns(self) -> list:
        return DcConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return DcConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + DcConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查DC值的合理性
            period = self.params['period']
            upper_col = f'DC_UPPER_{period}'
            lower_col = f'DC_LOWER_{period}'

            upper_values = result[upper_col].dropna()
            lower_values = result[lower_col].dropna()

            if len(upper_values) == 0 or len(lower_values) == 0:
                return False

            # 上轨应该 >= 下轨
            comparison = result[upper_col] >= result[lower_col]
            if not comparison.dropna().all():
                return False

            # 检查是否有异常的负值或无穷大
            if (upper_values <= 0).any() or (lower_values <= 0).any():
                return False

            if np.isinf(upper_values).any() or np.isinf(lower_values).any():
                return False

            return True

        except Exception:
            return False