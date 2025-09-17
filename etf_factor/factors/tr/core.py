"""
TR核心计算模块
专注于真实波幅的算法实现
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

# 导入TrConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("tr_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
TrConfig = config_module.TrConfig

# 导入TrValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("tr_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
TrValidator = validation_module.TrValidator


class TR(BaseFactor):
    """真实波幅因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化TR因子
        Args:
            params: 参数字典（TR无需参数，保持接口一致性）
        """
        validated_params = TrConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = TrValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算真实波幅
        TR = MAX(高-低, ABS(高-昨收), ABS(低-昨收))

        Args:
            data: 包含OHLC数据的DataFrame

        Returns:
            包含真实波幅的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取OHLC数据
        high = data['hfq_high']
        low = data['hfq_low']
        close = data['hfq_close']

        # 核心算法：计算真实波幅
        tr_values = self._calculate_tr(high, low, close)

        result['TR'] = tr_values

        return result

    def _calculate_tr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """计算真实波幅的核心算法"""
        # 获取前一日收盘价
        prev_close = close.shift(1)

        # 计算三种波幅
        hl = high - low  # 当日最高价与最低价之差
        hc = (high - prev_close).abs()  # 当日最高价与昨收之差的绝对值
        lc = (low - prev_close).abs()   # 当日最低价与昨收之差的绝对值

        # 取三者中的最大值
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)

        # 数据处理
        tr_values = self._process_calculation_result(tr_values)

        return tr_values

    def _process_calculation_result(self, tr_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('price')
        tr_values = tr_values.round(precision)

        # 处理无穷大值
        tr_values = tr_values.replace([float('inf'), -float('inf')], pd.NA)

        # TR应为非负数
        tr_values = tr_values.where(tr_values >= 0)

        # 数据范围验证和修正
        tr_values = config.validate_data_range(tr_values, 'price')

        return tr_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return TrConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return TrConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)