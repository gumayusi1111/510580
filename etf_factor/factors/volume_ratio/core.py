"""
VOLUME_RATIO核心计算模块
专注于量比指标的算法实现
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

# 导入VolumeRatioConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("volume_ratio_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
VolumeRatioConfig = config_module.VolumeRatioConfig


class VOLUME_RATIO(BaseFactor):
    """量比因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = VolumeRatioConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算量比
        VOLUME_RATIO = 当日成交量 / 前N日平均成交量

        量比意义：
        - 量比 > 1：成交量高于平均水平，资金关注度高
        - 量比 < 1：成交量低于平均水平，资金关注度低
        - 量比 > 2：异常放量，可能有重要消息
        - 量比 < 0.5：严重缩量，市场冷清
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取成交量数据（使用原始成交量，不需要复权）
        volume = data['vol']
        period = self.params["period"]

        # 计算前N日平均成交量
        # 使用shift(1)排除当日，只计算前N日
        avg_volume = volume.shift(1).rolling(window=period, min_periods=1).mean()

        # 计算量比
        volume_ratio = volume / avg_volume

        # 处理特殊情况
        volume_ratio = volume_ratio.replace([float('inf'), -float('inf')], np.nan)

        # 当平均成交量为0时，如果当日有成交量则设为较大值，否则设为1
        mask_zero_avg = (avg_volume == 0) | avg_volume.isna()
        volume_ratio = np.where(
            mask_zero_avg,
            np.where(volume > 0, 10.0, 1.0),  # 如果当日有量但历史无量，设为10倍
            volume_ratio
        )

        # 应用精度配置
        precision = config.get_precision('indicator')
        result[f'VOLUME_RATIO_{period}'] = pd.Series(volume_ratio).round(precision)

        # 数据验证和清理
        ratio_col = f'VOLUME_RATIO_{period}'

        # 量比应该是正数
        result[ratio_col] = result[ratio_col].abs()

        # 处理异常值（量比通常在0.1-10之间，超过50的为极端异常）
        mask_extreme = result[ratio_col] > 50
        if mask_extreme.any():
            result.loc[mask_extreme, ratio_col] = 50

        # 填充可能的NaN值
        result[ratio_col] = result[ratio_col].fillna(1.0)

        return result

    def get_required_columns(self) -> list:
        return VolumeRatioConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return VolumeRatioConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + VolumeRatioConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查量比值的合理性
            period = self.params['period']
            ratio_col = f'VOLUME_RATIO_{period}'
            ratio_values = result[ratio_col].dropna()

            if len(ratio_values) == 0:
                return False

            # 量比应该是正数
            if (ratio_values <= 0).any():
                return False

            # 检查是否有无穷大
            if np.isinf(ratio_values).any():
                return False

            # 量比通常在合理范围内（0.01-50）
            if (ratio_values > 100).any():
                return False

            return True

        except Exception:
            return False