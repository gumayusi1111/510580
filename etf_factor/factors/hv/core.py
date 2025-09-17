"""
HV核心计算模块
专注于历史波动率指标的算法实现
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

# 导入HvConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("hv_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
HvConfig = config_module.HvConfig


class HV(BaseFactor):
    """历史波动率因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = HvConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算历史波动率
        HV = STD(日收益率) × √252 (年化)
        """
        result = data[['ts_code', 'trade_date']].copy()

        close_prices = data['hfq_close']
        # 计算日收益率
        returns = close_prices.pct_change()

        # 计算各周期的历史波动率
        for period in self.params["periods"]:
            column_name = f'HV_{period}'

            # 使用滚动窗口计算历史波动率
            # 标准差 * √252 得到年化波动率
            rolling_std = returns.rolling(window=period, min_periods=period).std()
            hv_values = rolling_std * np.sqrt(252)

            # 应用全局精度配置
            precision = config.get_precision('percentage')
            hv_values = hv_values.round(precision)

            result[column_name] = hv_values

        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('HV_')]
        for col in numeric_columns:
            # 清理无穷大值
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # 验证数据范围
            result[col] = config.validate_data_range(result[col], 'percentage')

        return result

    def get_required_columns(self) -> list:
        return HvConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return HvConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + HvConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查HV值的合理性
            for period in self.params['periods']:
                col_name = f'HV_{period}'
                values = result[col_name].dropna()

                if len(values) == 0:
                    continue

                # 历史波动率应该是非负值且在合理范围内（0-1000%）
                if (values < 0).any():
                    return False

                if (values > 1000).any():  # 极端情况：超过1000%的年化波动率
                    return False

                # 检查是否有异常的无穷大值
                if np.isinf(values).any():
                    return False

            return True

        except Exception:
            return False