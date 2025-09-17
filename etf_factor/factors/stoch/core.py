"""
STOCH核心计算模块
专注于随机震荡器指标的算法实现
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

# 导入StochConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("stoch_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
StochConfig = config_module.StochConfig


class STOCH(BaseFactor):
    """随机震荡器因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = StochConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算随机震荡器
        %K = (收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) × 100
        %D = %K的M日移动平均
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格数据
        high_prices = data['hfq_high']
        low_prices = data['hfq_low']
        close_prices = data['hfq_close']

        k_period = self.params["k_period"]
        d_period = self.params["d_period"]

        # 计算N日内最高价和最低价
        highest_high = high_prices.rolling(window=k_period, min_periods=1).max()
        lowest_low = low_prices.rolling(window=k_period, min_periods=1).min()

        # 计算%K值
        # %K = (当前收盘价 - N日最低价) / (N日最高价 - N日最低价) × 100
        numerator = close_prices - lowest_low
        denominator = highest_high - lowest_low

        # 避免除零错误
        k_values = np.where(denominator != 0, (numerator / denominator) * 100, 50)
        k_values = pd.Series(k_values, index=close_prices.index)

        # 计算%D值（%K的移动平均）
        d_values = k_values.rolling(window=d_period, min_periods=1).mean()

        # 应用精度配置
        precision = config.get_precision('indicator')
        result[f'STOCH_K_{k_period}'] = k_values.round(precision)
        result[f'STOCH_D_{d_period}'] = d_values.round(precision)

        # 数据验证和清理
        k_col = f'STOCH_K_{k_period}'
        d_col = f'STOCH_D_{d_period}'

        # 确保值在0-100范围内
        result[k_col] = result[k_col].clip(0, 100)
        result[d_col] = result[d_col].clip(0, 100)

        # 处理异常值
        result[k_col] = result[k_col].fillna(50)
        result[d_col] = result[d_col].fillna(50)

        return result

    def get_required_columns(self) -> list:
        return StochConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return StochConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + StochConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查STOCH值的合理性
            k_period = self.params['k_period']
            d_period = self.params['d_period']
            k_col = f'STOCH_K_{k_period}'
            d_col = f'STOCH_D_{d_period}'

            k_values = result[k_col].dropna()
            d_values = result[d_col].dropna()

            if len(k_values) == 0 or len(d_values) == 0:
                return False

            # 值应在0-100范围内
            if (k_values < 0).any() or (k_values > 100).any():
                return False
            if (d_values < 0).any() or (d_values > 100).any():
                return False

            # 检查是否有无穷大
            if np.isinf(k_values).any() or np.isinf(d_values).any():
                return False

            return True

        except Exception:
            return False