"""
DAILY_RETURN核心计算模块
专注于日收益率的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.base_factor import BaseFactor
from src.config import config
from config import DailyReturnConfig
from validation import DailyReturnValidator


class DAILY_RETURN(BaseFactor):
    """日收益率因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化DAILY_RETURN因子
        Args:
            params: 参数字典 (无参数)
        """
        validated_params = DailyReturnConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = DailyReturnValidator()

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算日收益率
        DAILY_RETURN = (今日收盘价 - 昨日收盘价) / 昨日收盘价 × 100%

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含日收益率的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价
        close_prices = data['hfq_close']

        # 核心算法：计算日收益率
        daily_return = close_prices.pct_change() * 100

        # 数据处理和清理
        daily_return = self._process_calculation_result(daily_return)

        result['DAILY_RETURN'] = daily_return

        return result

    def _process_calculation_result(self, daily_return: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('percentage')
        daily_return = daily_return.round(precision)

        # 处理无穷大值
        daily_return = daily_return.replace([float('inf'), -float('inf')], pd.NA)

        # 数据范围验证和修正
        daily_return = config.validate_data_range(daily_return, 'percentage')

        return daily_return

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return DailyReturnConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return DailyReturnConfig.get_factor_info()

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)