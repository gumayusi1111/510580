"""
WR核心计算模块
专注于威廉指标的算法实现
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

# 导入WrConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("wr_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
WrConfig = config_module.WrConfig


class WR(BaseFactor):
    """威廉指标因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = WrConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算威廉指标
        WR = (N日内最高价 - 收盘价) / (N日内最高价 - N日内最低价) × (-100)

        WR解释：
        - WR值在-100到0之间
        - WR > -20: 超买状态，价格可能回调
        - WR < -80: 超卖状态，价格可能反弹
        - WR在-20到-80之间: 正常震荡区间
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格数据
        high_prices = data['hfq_high']
        low_prices = data['hfq_low']
        close_prices = data['hfq_close']

        period = self.params["period"]

        # 计算N日内最高价和最低价
        highest_high = high_prices.rolling(window=period, min_periods=1).max()
        lowest_low = low_prices.rolling(window=period, min_periods=1).min()

        # 计算威廉指标
        # WR = (最高价 - 收盘价) / (最高价 - 最低价) × (-100)
        numerator = highest_high - close_prices
        denominator = highest_high - lowest_low

        # 避免除零错误
        wr = np.where(denominator != 0, (numerator / denominator) * (-100), -50)
        wr = pd.Series(wr, index=close_prices.index)

        # 处理特殊情况
        wr = wr.replace([float('inf'), -float('inf')], np.nan)
        wr = wr.fillna(-50)  # 默认值设为中位数

        # 应用精度配置
        precision = config.get_precision('indicator')
        column_name = f'WR_{period}'
        result[column_name] = wr.round(precision)

        # 数据验证和清理
        # WR值应该在-100到0之间
        result[column_name] = result[column_name].clip(-100, 0)

        return result

    def get_required_columns(self) -> list:
        return WrConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return WrConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + WrConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查WR值的合理性
            period = self.params['period']
            wr_col = f'WR_{period}'
            wr_values = result[wr_col].dropna()

            if len(wr_values) == 0:
                return False

            # WR值应该在-100到0之间
            if (wr_values < -100).any() or (wr_values > 0).any():
                return False

            # 检查是否有无穷大
            if np.isinf(wr_values).any():
                return False

            return True

        except Exception:
            return False