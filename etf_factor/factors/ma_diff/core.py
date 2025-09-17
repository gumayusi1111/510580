"""
MA_DIFF核心计算模块
专注于移动均线差值指标的算法实现
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

# 导入MaDiffConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("ma_diff_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MaDiffConfig = config_module.MaDiffConfig


class MA_DIFF(BaseFactor):
    """移动均线差值因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = MaDiffConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算移动均线差值
        MA_DIFF = 短周期MA - 长周期MA
        """
        result = data[['ts_code', 'trade_date']].copy()

        close_prices = data['hfq_close']

        # 预计算所有需要的MA值
        ma_cache = {}
        all_periods = set()
        for short, long in self.params["pairs"]:
            all_periods.add(short)
            all_periods.add(long)

        # 向量化计算所有需要的MA
        for period in all_periods:
            ma_values = close_prices.rolling(window=period, min_periods=1).mean()
            ma_cache[period] = ma_values

        # 计算所有差值对
        for short, long in self.params["pairs"]:
            column_name = f"MA_DIFF_{short}_{long}"

            # 计算差值：短周期MA - 长周期MA
            diff_values = ma_cache[short] - ma_cache[long]

            # 应用全局精度配置
            precision = config.get_precision("price")
            diff_values = diff_values.round(precision)

            result[column_name] = diff_values

        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith("MA_DIFF_")]
        for col in numeric_columns:
            # MA差值可以为负数，使用更宽松的验证
            result[col] = result[col].replace([float("inf"), -float("inf")], pd.NA)

        return result

    def get_required_columns(self) -> list:
        return MaDiffConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return MaDiffConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + MaDiffConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查MA_DIFF值的合理性
            for short, long in self.params["pairs"]:
                col_name = f"MA_DIFF_{short}_{long}"
                diff_values = result[col_name].dropna()

                if len(diff_values) == 0:
                    continue

                # MA差值应在合理范围内（可以为负）
                if (abs(diff_values) > 1000).any():
                    return False

                # 检查是否有无穷大值
                if np.isinf(diff_values).any():
                    return False

            return True

        except Exception:
            return False