"""
CUM_RETURN核心计算模块
专注于累计收益率的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.base_factor import BaseFactor
from src.config import config
# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入CumReturnConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("cum_return_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
CumReturnConfig = config_module.CumReturnConfig

# 导入CumReturnValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("cum_return_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
CumReturnValidator = validation_module.CumReturnValidator


class CUM_RETURN(BaseFactor):
    """累计收益率因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化CUM_RETURN因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,20,60]}
        """
        validated_params = CumReturnConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = CumReturnValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算累计收益率
        CUM_RETURN = (今日价格 - N日前价格) / N日前价格 × 100%

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含累计收益率的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价
        close_prices = data['hfq_close']

        # 计算各周期的累计收益率
        for period in self.params["periods"]:
            column_name = f'CUM_RETURN_{period}'

            # 核心算法：计算累计收益率
            cum_return = self._calculate_period_return(close_prices, period)

            result[column_name] = cum_return

        return result

    def _calculate_period_return(self, prices: pd.Series, period: int) -> pd.Series:
        """计算指定周期的累计收益率"""
        # 创建结果序列
        cum_return = pd.Series(index=prices.index, dtype=float)

        # 从第period行开始计算（有足够历史数据的位置）
        for i in range(period, len(prices)):
            current_price = prices.iloc[i]
            prev_price = prices.iloc[i - period]  # period天前的价格

            if pd.notna(current_price) and pd.notna(prev_price) and prev_price != 0:
                return_value = ((current_price - prev_price) / prev_price) * 100
                cum_return.iloc[i] = return_value
            else:
                cum_return.iloc[i] = pd.NA

        # 数据处理
        cum_return = self._process_calculation_result(cum_return)

        return cum_return

    def _process_calculation_result(self, cum_return: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('percentage')
        cum_return = cum_return.round(precision)

        # 处理无穷大值
        cum_return = cum_return.replace([float('inf'), -float('inf')], pd.NA)

        # 数据范围验证和修正
        cum_return = config.validate_data_range(cum_return, 'percentage')

        return cum_return

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return CumReturnConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return CumReturnConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)