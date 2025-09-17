"""
MACD核心计算模块
专注于MACD指标的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入MacdConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("macd_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MacdConfig = config_module.MacdConfig

# 导入MacdValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("macd_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
MacdValidator = validation_module.MacdValidator


class MACD(BaseFactor):
    """MACD指标因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化MACD因子
        Args:
            params: 参数字典，包含fast_period, slow_period, signal_period
                   默认{"fast_period": 12, "slow_period": 26, "signal_period": 9}
        """
        validated_params = MacdConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = MacdValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算MACD指标
        DIF = EMA_fast - EMA_slow
        DEA = EMA(DIF, signal_period)
        HIST = DIF - DEA

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            包含MACD指标的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价数据 (按日期升序排列用于EMA计算)
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']

        # 核心算法：计算MACD各组件
        dif, dea, hist = self._calculate_macd_components(close_prices)

        # 添加到结果 (恢复原始排序)
        result['MACD_DIF'] = dif
        result['MACD_DEA'] = dea
        result['MACD_HIST'] = hist

        # 恢复原始排序（最新日期在前）
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)

        return result

    def _calculate_macd_components(self, prices: pd.Series) -> tuple:
        """计算MACD的三个组件：DIF, DEA, HIST"""
        # 计算快线和慢线EMA
        ema_fast = prices.ewm(
            span=self.params["fast_period"],
            adjust=False
        ).mean()

        ema_slow = prices.ewm(
            span=self.params["slow_period"],
            adjust=False
        ).mean()

        # 计算DIF (差离值)
        dif = ema_fast - ema_slow

        # 计算DEA (信号线) - DIF的EMA
        dea = dif.ewm(
            span=self.params["signal_period"],
            adjust=False
        ).mean()

        # 计算HIST (柱状图) - DIF与DEA的差值
        hist = dif - dea

        # 数据处理
        dif = self._process_calculation_result(dif)
        dea = self._process_calculation_result(dea)
        hist = self._process_calculation_result(hist)

        return dif, dea, hist

    def _process_calculation_result(self, values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置
        precision = config.get_precision('indicator')
        values = values.round(precision)

        # 处理无穷大值
        values = values.replace([float('inf'), -float('inf')], pd.NA)

        # MACD值可以为正数或负数，不需要额外的范围限制
        # 但仍然应用全局数据范围验证
        values = config.validate_data_range(values, 'indicator')

        return values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return MacdConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return MacdConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)