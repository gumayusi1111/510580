"""
WMA核心计算模块
专注于加权移动均线的算法实现
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

# 导入WmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("wma_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
WmaConfig = config_module.WmaConfig


class WMA(BaseFactor):
    """加权移动均线因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = WmaConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算加权移动均线
        WMA = Σ(价格 × 权重) / Σ(权重)
        权重: [1,2,3,...,N] (最近的价格权重最高)
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价数据
        close_prices = data['hfq_close']

        # 向量化计算所有周期的WMA
        for period in self.params["periods"]:
            column_name = f'WMA_{period}'

            # 生成权重：[1,2,3,...,period]
            weights = list(range(1, period + 1))
            weights_sum = sum(weights)

            # 向量化计算WMA - 核心优化点
            def calculate_wma_single(series):
                """计算单个WMA值"""
                if len(series) < period:
                    # 不足周期时使用可用数据
                    available_weights = weights[:len(series)]
                    available_weights_sum = sum(available_weights)
                    return (series * available_weights).sum() / available_weights_sum
                else:
                    return (series * weights).sum() / weights_sum

            # 使用rolling + apply进行向量化计算
            wma_values = close_prices.rolling(
                window=period,
                min_periods=1
            ).apply(calculate_wma_single, raw=True)

            # 应用全局精度配置
            wma_values = wma_values.round(config.get_precision('price'))

            result[column_name] = wma_values

        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('WMA_')]
        for col in numeric_columns:
            result[col] = config.validate_data_range(result[col], 'price')

        return result

    def get_required_columns(self) -> list:
        return WmaConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return WmaConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + WmaConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查WMA值的合理性
            for period in self.params['periods']:
                col_name = f'WMA_{period}'
                wma_values = result[col_name].dropna()

                if len(wma_values) == 0:
                    continue

                # WMA值应该为正数
                if (wma_values <= 0).any():
                    return False

                # WMA值应在合理范围内
                if (wma_values > 10000).any() or (wma_values < 0.001).any():
                    return False

            return True

        except Exception:
            return False