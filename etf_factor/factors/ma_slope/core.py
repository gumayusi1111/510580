"""
MA_SLOPE核心计算模块
专注于移动均线斜率的算法实现
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入MaSlopeConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("ma_slope_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MaSlopeConfig = config_module.MaSlopeConfig

# 导入MaSlopeValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("ma_slope_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
MaSlopeValidator = validation_module.MaSlopeValidator


class MA_SLOPE(BaseFactor):
    """移动均线斜率因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化MA_SLOPE因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20]}
        """
        validated_params = MaSlopeConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = MaSlopeValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算移动均线斜率
        斜率 = (当前MA - N日前MA) / N

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含移动均线斜率的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价数据
        close_prices = data['hfq_close']

        # 计算各周期的MA斜率
        for period in self.params["periods"]:
            column_name = f'MA_SLOPE_{period}'

            # 核心算法：计算移动均线斜率
            slope_values = self._calculate_period_slope(close_prices, period)

            result[column_name] = slope_values

        return result

    def _calculate_period_slope(self, prices: pd.Series, period: int) -> pd.Series:
        """计算指定周期的移动均线斜率"""
        # 先计算移动均线
        ma_values = prices.rolling(
            window=period,
            min_periods=1
        ).mean()

        # 创建结果序列
        slope_values = pd.Series(index=ma_values.index, dtype=float)

        # 从第period行开始计算（有足够历史数据的位置）
        for i in range(period, len(ma_values)):
            current_ma = ma_values.iloc[i]
            prev_ma = ma_values.iloc[i - period]  # period天前的MA值

            if pd.notna(current_ma) and pd.notna(prev_ma):
                # 斜率 = (当前MA - N日前MA) / N
                slope_value = (current_ma - prev_ma) / period
                slope_values.iloc[i] = slope_value
            else:
                slope_values.iloc[i] = pd.NA

        # 数据处理
        slope_values = self._process_calculation_result(slope_values)

        return slope_values

    def _process_calculation_result(self, slope_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('indicator')
        slope_values = slope_values.round(precision)

        # 处理无穷大值
        slope_values = slope_values.replace([float('inf'), -float('inf')], pd.NA)

        # 数据范围验证和修正
        slope_values = config.validate_data_range(slope_values, 'indicator')

        return slope_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return MaSlopeConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return MaSlopeConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)