"""
ATR_PCT核心计算模块
专注于ATR百分比的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入AtrPctConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("atr_pct_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
AtrPctConfig = config_module.AtrPctConfig

# 导入AtrPctValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("atr_pct_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
AtrPctValidator = validation_module.AtrPctValidator


class ATR_PCT(BaseFactor):
    """ATR百分比因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化ATR_PCT因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [14]}
        """
        validated_params = AtrPctConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = AtrPctValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算ATR百分比
        ATR_PCT = ATR / 收盘价 × 100%

        Args:
            data: 包含OHLC数据的DataFrame

        Returns:
            包含ATR百分比的DataFrame

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

        # 核心算法：先计算TR，再计算ATR和ATR_PCT
        tr_values = self._calculate_tr(high, low, close)

        # 计算各周期的ATR_PCT
        for period in self.params["periods"]:
            column_name = f'ATR_PCT_{period}'

            # 计算ATR百分比
            atr_pct_values = self._calculate_period_atr_pct(tr_values, close, period)

            result[column_name] = atr_pct_values

        return result

    def _calculate_tr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """计算真实波幅TR"""
        # 获取前一日收盘价
        prev_close = close.shift(1)

        # 计算三种波幅
        hl = high - low  # 当日最高价与最低价之差
        hc = (high - prev_close).abs()  # 当日最高价与昨收之差的绝对值
        lc = (low - prev_close).abs()   # 当日最低价与昨收之差的绝对值

        # 取三者中的最大值
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)

        return tr_values

    def _calculate_period_atr_pct(self, tr_values: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """计算指定周期的ATR百分比"""
        # 计算ATR (使用指数加权移动平均)
        atr_values = tr_values.ewm(span=period, adjust=False).mean()

        # 计算ATR百分比
        atr_pct_values = (atr_values / close) * 100

        # 数据处理
        atr_pct_values = self._process_calculation_result(atr_pct_values)

        return atr_pct_values

    def _process_calculation_result(self, atr_pct_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('percentage')
        atr_pct_values = atr_pct_values.round(precision)

        # 处理无穷大值
        atr_pct_values = atr_pct_values.replace([float('inf'), -float('inf')], pd.NA)

        # ATR_PCT应为非负数
        atr_pct_values = atr_pct_values.where(atr_pct_values >= 0)

        # 数据范围验证和修正
        atr_pct_values = config.validate_data_range(atr_pct_values, 'percentage')

        return atr_pct_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return AtrPctConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return AtrPctConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)