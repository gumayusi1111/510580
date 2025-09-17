"""
BOLL核心计算模块
专注于布林带指标的算法实现
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

# 导入BollConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("boll_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
BollConfig = config_module.BollConfig


class BOLL(BaseFactor):
    """布林带因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = BollConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算布林带
        MID = SMA(收盘价, period)
        UPPER = MID + std_dev × STD(收盘价, period)
        LOWER = MID - std_dev × STD(收盘价, period)
        """
        result = data[['ts_code', 'trade_date']].copy()

        close = data['hfq_close']
        period = self.params["period"]
        std_dev = self.params["std_dev"]

        # 计算中轨 (移动平均)
        mid = close.rolling(window=period, min_periods=1).mean()

        # 计算标准差
        std = close.rolling(window=period, min_periods=1).std()

        # 计算上下轨
        upper = mid + std_dev * std
        lower = mid - std_dev * std

        # 应用精度配置
        precision = config.get_precision('price')
        result['BOLL_UPPER'] = upper.round(precision)
        result['BOLL_MID'] = mid.round(precision)
        result['BOLL_LOWER'] = lower.round(precision)

        # 数据清理
        for col in ['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)

        return result

    def get_required_columns(self) -> list:
        return BollConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return BollConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + BollConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查上中下轨的逻辑关系
            valid_data = result.dropna(subset=['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER'])
            if len(valid_data) > 0:
                # 上轨应大于等于中轨，中轨应大于等于下轨
                if not ((valid_data['BOLL_UPPER'] >= valid_data['BOLL_MID']).all() and
                        (valid_data['BOLL_MID'] >= valid_data['BOLL_LOWER']).all()):
                    return False

            return True

        except Exception:
            return False