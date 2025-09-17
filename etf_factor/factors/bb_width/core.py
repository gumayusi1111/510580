"""
BB_WIDTH核心计算模块
专注于布林带宽度指标的算法实现
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

# 导入BbWidthConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("bb_width_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
BbWidthConfig = config_module.BbWidthConfig


class BB_WIDTH(BaseFactor):
    """布林带宽度因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = BbWidthConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算布林带宽度
        BB_WIDTH = (BOLL_UPPER - BOLL_LOWER) / BOLL_MID × 100

        宽度含义：
        - 高值：价格波动大，趋势可能反转
        - 低值：价格波动小，可能酝酿突破
        """
        result = data[['ts_code', 'trade_date']].copy()

        close_prices = data['hfq_close']
        period = self.params["period"]
        std_dev = self.params["std_dev"]

        # 计算布林带组件（重复BOLL计算，避免依赖其他因子）
        # 计算中轨 (移动平均)
        mid = close_prices.rolling(window=period, min_periods=1).mean()

        # 计算标准差
        std = close_prices.rolling(window=period, min_periods=1).std()

        # 计算上下轨
        upper = mid + std_dev * std
        lower = mid - std_dev * std

        # 计算布林带宽度（相对于中轨的百分比）
        bb_width = ((upper - lower) / mid) * 100

        # 处理特殊情况
        bb_width = bb_width.replace([float('inf'), -float('inf')], np.nan)
        bb_width = bb_width.fillna(0)  # 当中轨为0时，宽度设为0

        # 应用精度配置
        precision = config.get_precision('percentage')
        result[f'BB_WIDTH_{period}'] = bb_width.round(precision)

        # 数据验证和清理
        width_col = f'BB_WIDTH_{period}'

        # 宽度应该是正数
        result[width_col] = result[width_col].abs()

        # 过滤异常值（超过1000%的极端情况）
        mask = result[width_col] > 1000
        if mask.any():
            result.loc[mask, width_col] = 100  # 设置为合理上限

        return result

    def get_required_columns(self) -> list:
        return BbWidthConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return BbWidthConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + BbWidthConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查BB_WIDTH值的合理性
            period = self.params['period']
            width_col = f'BB_WIDTH_{period}'
            width_values = result[width_col].dropna()

            if len(width_values) == 0:
                return False

            # 宽度应该是正数
            if (width_values < 0).any():
                return False

            # 宽度应该在合理范围内（0-1000%）
            if (width_values > 1000).any():
                return False

            # 检查是否有无穷大或NaN
            if np.isinf(width_values).any():
                return False

            return True

        except Exception:
            return False