"""
ANNUAL_VOL核心计算模块
专注于年化波动率的算法实现
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入AnnualVolConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("annual_vol_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
AnnualVolConfig = config_module.AnnualVolConfig

# 导入AnnualVolValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("annual_vol_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
AnnualVolValidator = validation_module.AnnualVolValidator


class ANNUAL_VOL(BaseFactor):
    """年化波动率因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化ANNUAL_VOL因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [20,60]}
        """
        validated_params = AnnualVolConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = AnnualVolValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算年化波动率
        ANNUAL_VOL = STD(日收益率) × √252

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含年化波动率的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 计算日收益率
        close_prices = data['hfq_close']
        daily_returns = close_prices.pct_change()

        # 计算各周期的年化波动率
        for period in self.params["periods"]:
            column_name = f'ANNUAL_VOL_{period}'

            # 核心算法：计算年化波动率
            annual_vol = self._calculate_period_volatility(daily_returns, period)

            result[column_name] = annual_vol

        return result

    def _calculate_period_volatility(self, returns: pd.Series, period: int) -> pd.Series:
        """计算指定周期的年化波动率"""
        # 创建结果序列
        annual_vol = pd.Series(index=returns.index, dtype=float)

        # 从第period行开始计算（有足够历史数据的位置）
        for i in range(period, len(returns)):
            period_returns = returns.iloc[i-period+1:i+1]  # 取period个收益率

            # 确保有足够的非空数据
            valid_returns = period_returns.dropna()
            if len(valid_returns) >= period:
                vol_std = period_returns.std()
                if pd.notna(vol_std) and vol_std >= 0:
                    # 年化波动率 = 标准差 × √(年交易日数)
                    trading_days = AnnualVolConfig.get_trading_days_per_year()
                    annualized_vol = vol_std * np.sqrt(trading_days)
                    annual_vol.iloc[i] = annualized_vol
                else:
                    annual_vol.iloc[i] = pd.NA
            else:
                annual_vol.iloc[i] = pd.NA

        # 数据处理
        annual_vol = self._process_calculation_result(annual_vol)

        return annual_vol

    def _process_calculation_result(self, annual_vol: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('percentage')
        annual_vol = annual_vol.round(precision)

        # 处理无穷大值
        annual_vol = annual_vol.replace([float('inf'), -float('inf')], pd.NA)

        # 数据范围验证和修正
        annual_vol = config.validate_data_range(annual_vol, 'percentage')

        return annual_vol

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return AnnualVolConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return AnnualVolConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)