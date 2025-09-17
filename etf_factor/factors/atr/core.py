"""
ATR核心计算模块
专注于ATR平均真实波幅指标的算法实现
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

# 导入AtrConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("atr_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
AtrConfig = config_module.AtrConfig


class ATR(BaseFactor):
    """ATR平均真实波幅因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = AtrConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算ATR平均真实波幅
        ATR = TR的移动平均
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 先计算TR
        high = data['hfq_high']
        low = data['hfq_low']
        close = data['hfq_close']

        # 获取前一日收盘价
        prev_close = close.shift(1)

        # 计算TR
        hl = high - low
        hc = (high - prev_close).abs()
        lc = (low - prev_close).abs()
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)

        # 向量化计算所有周期的ATR
        for period in self.params["periods"]:
            column_name = f'ATR_{period}'

            # 计算TR的移动平均 (使用EMA更平滑)
            atr_values = tr_values.ewm(
                span=period,
                adjust=False
            ).mean()

            # 应用全局精度配置
            atr_values = atr_values.round(config.get_precision('price'))

            result[column_name] = atr_values

        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('ATR_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # ATR应为正数
            result[col] = result[col].where(result[col] >= 0)

        return result

    def get_required_columns(self) -> list:
        return AtrConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return AtrConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + AtrConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查ATR值的合理性
            for period in self.params['periods']:
                col_name = f'ATR_{period}'
                atr_values = result[col_name].dropna()

                if len(atr_values) == 0:
                    continue

                # ATR值应为正数
                if (atr_values < 0).any():
                    return False

                # ATR值应在合理范围内
                if (atr_values > 100).any():
                    return False

            return True

        except Exception:
            return False