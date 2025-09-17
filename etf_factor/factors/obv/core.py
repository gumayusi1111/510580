"""
OBV核心计算模块
专注于OBV能量潮指标的算法实现
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

# 导入ObvConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("obv_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
ObvConfig = config_module.ObvConfig


class OBV(BaseFactor):
    """OBV能量潮指标因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = ObvConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算OBV能量潮
        当日价格 > 昨日价格: OBV = 前日OBV + 今日成交量
        当日价格 < 昨日价格: OBV = 前日OBV - 今日成交量
        当日价格 = 昨日价格: OBV = 前日OBV
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格和成交量数据
        close = data['hfq_close']
        volume = data['vol']

        # 计算价格变化方向
        price_change = close.diff()

        # 根据价格变化决定成交量的符号
        volume_direction = pd.Series(0, index=volume.index)
        volume_direction[price_change > 0] = 1   # 价格上涨
        volume_direction[price_change < 0] = -1  # 价格下跌
        volume_direction[price_change == 0] = 0  # 价格不变

        # 计算有向成交量
        signed_volume = volume * volume_direction

        # 累计求和得到OBV
        obv_values = signed_volume.cumsum()

        # 应用精度配置
        obv_values = obv_values.round(config.get_precision('default'))

        result['OBV'] = obv_values

        # 数据清理
        result['OBV'] = result['OBV'].replace([float('inf'), -float('inf')], pd.NA)

        return result

    def get_required_columns(self) -> list:
        return ObvConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return ObvConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + ObvConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            obv_values = result['OBV'].dropna()
            if len(obv_values) == 0:
                return len(result) > 0  # 允许部分NA值

            # 检查是否有无穷大值
            if np.isinf(obv_values).any():
                return False

            # OBV是累计值，应该是连续的数值序列
            return True

        except Exception:
            return False