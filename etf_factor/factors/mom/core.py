"""
MOM核心计算模块
专注于动量指标的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入MomConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("mom_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MomConfig = config_module.MomConfig

# 导入MomValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("mom_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
MomValidator = validation_module.MomValidator


class MOM(BaseFactor):
    """动量指标因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化MOM因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20]}
        """
        validated_params = MomConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = MomValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算动量指标
        MOM = 当前价格 - N日前价格

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含动量指标的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价
        close_prices = data['hfq_close']

        # 计算各周期的动量指标
        for period in self.params["periods"]:
            column_name = f'MOM_{period}'

            # 核心算法：计算动量指标
            mom_values = self._calculate_period_momentum(close_prices, period)

            result[column_name] = mom_values

        return result

    def _calculate_period_momentum(self, prices: pd.Series, period: int) -> pd.Series:
        """计算指定周期的动量指标"""
        # 创建结果序列
        mom_values = pd.Series(index=prices.index, dtype=float)

        # 从第period行开始计算（有足够历史数据的位置）
        for i in range(period, len(prices)):
            current_price = prices.iloc[i]
            prev_price = prices.iloc[i - period]  # period天前的价格

            if pd.notna(current_price) and pd.notna(prev_price):
                momentum = current_price - prev_price
                mom_values.iloc[i] = momentum
            else:
                mom_values.iloc[i] = pd.NA

        # 数据处理
        mom_values = self._process_calculation_result(mom_values)

        return mom_values

    def _process_calculation_result(self, mom_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('price')
        mom_values = mom_values.round(precision)

        # 处理无穷大值
        mom_values = mom_values.replace([float('inf'), -float('inf')], pd.NA)

        return mom_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return MomConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return MomConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)