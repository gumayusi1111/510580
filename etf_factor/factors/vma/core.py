"""
VMA核心计算模块
专注于成交量移动均线的算法实现
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入VmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("vma_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
VmaConfig = config_module.VmaConfig

# 导入VmaValidator
validation_path = os.path.join(current_dir, 'validation.py')
spec = importlib.util.spec_from_file_location("vma_validation", validation_path)
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)
VmaValidator = validation_module.VmaValidator


class VMA(BaseFactor):
    """成交量移动均线因子 - 模块化实现"""

    def __init__(self, params=None):
        """
        初始化VMA因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20]}
        """
        validated_params = VmaConfig.validate_params(params)
        super().__init__(validated_params)
        self.validator = VmaValidator(self.params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算成交量移动均线
        VMA = SMA(成交量, period)

        Args:
            data: 包含成交量数据的DataFrame

        Returns:
            包含成交量移动均线的DataFrame

        Raises:
            ValueError: 当输入数据不符合要求时
        """
        # 输入数据验证
        self.validator.validate_input_data(data)

        result = data[['ts_code', 'trade_date']].copy()

        # 获取成交量数据 (使用原始成交量，不复权)
        volume = data['vol']

        # 计算各周期的VMA
        for period in self.params["periods"]:
            column_name = f'VMA_{period}'

            # 核心算法：计算成交量移动均线
            vma_values = self._calculate_period_vma(volume, period)

            result[column_name] = vma_values

        return result

    def _calculate_period_vma(self, volume: pd.Series, period: int) -> pd.Series:
        """计算指定周期的成交量移动均线"""
        # 计算成交量移动平均
        vma_values = volume.rolling(window=period, min_periods=1).mean()

        # 数据处理
        vma_values = self._process_calculation_result(vma_values)

        return vma_values

    def _process_calculation_result(self, vma_values: pd.Series) -> pd.Series:
        """处理计算结果，包括精度控制和异常值处理"""
        # 应用精度配置 - VMA使用默认精度
        precision = config.get_precision('default')
        vma_values = vma_values.round(precision)

        # 处理无穷大值
        vma_values = vma_values.replace([float('inf'), -float('inf')], pd.NA)

        # VMA应为非负数（成交量移动均线不应为负）
        vma_values = vma_values.where(vma_values >= 0)

        # 数据范围验证和修正
        vma_values = config.validate_data_range(vma_values, 'default')

        return vma_values

    def get_required_columns(self) -> list:
        """获取计算所需的数据列"""
        return VmaConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return VmaConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        return self.validator.validate_output_result(result)