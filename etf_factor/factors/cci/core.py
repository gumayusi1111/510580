"""
CCI核心计算模块
专注于CCI顺势指标的算法实现
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

# 导入CciConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("cci_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
CciConfig = config_module.CciConfig


class CCI(BaseFactor):
    """CCI顺势指标因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = CciConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算CCI指标
        TP = (最高价 + 最低价 + 收盘价) / 3 (典型价格)
        MA = TP的N日移动平均
        MD = |TP - MA|的N日移动平均 (平均绝对偏差)
        CCI = (TP - MA) / (0.015 × MD)

        CCI解释：
        - CCI > +100: 超买状态，可能回调
        - CCI < -100: 超卖状态，可能反弹
        - CCI在±100之间: 正常震荡区间
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格数据
        high_prices = data['hfq_high']
        low_prices = data['hfq_low']
        close_prices = data['hfq_close']

        period = self.params["period"]

        # 计算典型价格 (Typical Price)
        tp = (high_prices + low_prices + close_prices) / 3

        # 计算TP的N日移动平均
        ma_tp = tp.rolling(window=period, min_periods=1).mean()

        # 计算平均绝对偏差 (Mean Absolute Deviation)
        # MD = |TP - MA|的N日移动平均
        abs_deviation = np.abs(tp - ma_tp)
        md = abs_deviation.rolling(window=period, min_periods=1).mean()

        # 计算CCI
        # CCI = (TP - MA) / (0.015 × MD)
        # 0.015是标准化常数，使得约2/3的CCI值在±100之间
        cci = (tp - ma_tp) / (0.015 * md)

        # 处理特殊情况
        cci = cci.replace([float('inf'), -float('inf')], np.nan)

        # 当MD为0时（价格完全不变），CCI设为0
        cci = cci.fillna(0)

        # 应用精度配置
        precision = config.get_precision('indicator')
        column_name = f'CCI_{period}'
        result[column_name] = cci.round(precision)

        # 数据验证和清理
        # CCI可以有很大的范围，但超过±1000的值比较极端
        result[column_name] = result[column_name].clip(-1000, 1000)

        return result

    def get_required_columns(self) -> list:
        return CciConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return CciConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + CciConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查CCI值的合理性
            period = self.params['period']
            cci_col = f'CCI_{period}'
            cci_values = result[cci_col].dropna()

            if len(cci_values) == 0:
                return False

            # 检查是否有无穷大
            if np.isinf(cci_values).any():
                return False

            # CCI值应该在合理范围内（虽然理论上无限，但实际很少超过±1000）
            if (cci_values > 2000).any() or (cci_values < -2000).any():
                return False

            return True

        except Exception:
            return False