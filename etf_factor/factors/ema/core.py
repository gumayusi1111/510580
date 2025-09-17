"""
EMA核心计算模块
专注于指数移动均线的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入EmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("ema_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
EmaConfig = config_module.EmaConfig

# 导入EmaValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("ema_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
EmaValidator = validation_module.EmaValidator


class EMA(BaseFactor):
    """指数移动均线因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化EMA因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20,60]}
        """
        validated_params = EmaConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = EmaValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算指数移动均线
        EMA = 前一日EMA × (1-α) + 今日收盘价 × α
        其中 α = 2/(N+1), N为周期

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含指数移动均线的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价数据 (按日期升序排列用于EMA计算)
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']

        # 计算各周期的EMA
        for period in self.params["periods"]:
            column_name = f'EMA_{period}'

            # 核心算法：计算指数移动均线
            ema_values = self._calculate_period_ema(close_prices, period)

            result[column_name] = ema_values

        # 恢复原始排序（最新日期在前）
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)

        return result

    def _calculate_period_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """计算指定周期的指数移动均线"""
        # pandas向量化计算EMA - 核心优化点
        ema_values = prices.ewm(
            span=period,           # EMA周期
            adjust=False           # 不调整权重（标准EMA算法）
        ).mean()

        # 数据处理
        ema_values = self._process_calculation_result(ema_values)

        return ema_values

    def _process_calculation_result(self, ema_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('price')
        ema_values = ema_values.round(precision)

        # 处理无穷大值
        ema_values = ema_values.replace([float('inf'), -float('inf')], pd.NA)

        # 数据范围验证和修正
        ema_values = config.validate_data_range(ema_values, 'price')

        return ema_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return EmaConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return EmaConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)