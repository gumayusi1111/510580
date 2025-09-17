"""
SMA核心计算模块
专注于简单移动均线的算法实现
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加正确的项目路径
etf_factor_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, etf_factor_root)

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入SmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("sma_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
SmaConfig = config_module.SmaConfig


class SMA(BaseFactor):
    """简单移动均线因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = SmaConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算简单移动均线
        使用pandas.rolling()进行高效计算
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取收盘价数据
        close_prices = data['hfq_close']

        # 向量化计算所有周期的SMA
        for period in self.params["periods"]:
            column_name = f'SMA_{period}'

            # pandas向量化计算 - 核心优化点
            sma_values = close_prices.rolling(
                window=period,
                min_periods=1  # 允许不足周期的计算
            ).mean()

            # 应用全局精度配置
            sma_values = sma_values.round(config.get_precision('price'))

            result[column_name] = sma_values

        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('SMA_')]
        for col in numeric_columns:
            # 处理异常值
            result[col] = config.validate_data_range(result[col], 'price')

        return result

    def get_required_columns(self) -> list:
        return SmaConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return SmaConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + SmaConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查SMA值的合理性
            for period in self.params['periods']:
                col_name = f'SMA_{period}'
                sma_values = result[col_name].dropna()

                if len(sma_values) == 0:
                    continue

                # SMA值应该为正数（价格数据）
                if (sma_values <= 0).any():
                    return False

                # SMA值应在合理范围内
                if (sma_values > 10000).any() or (sma_values < 0.001).any():
                    return False

            return True

        except Exception:
            return False

    def get_performance_stats(self, data: pd.DataFrame, result: pd.DataFrame) -> dict:
        """获取计算性能统计"""
        stats = {
            'input_rows': len(data),
            'output_rows': len(result),
            'periods_calculated': len(self.params['periods']),
            'output_columns': len([col for col in result.columns if col.startswith('SMA_')]),
            'data_completeness': {}
        }

        # 数据完整性统计
        for period in self.params['periods']:
            col_name = f'SMA_{period}'
            if col_name in result.columns:
                non_null_count = result[col_name].notna().sum()
                completeness = non_null_count / len(result) if len(result) > 0 else 0
                stats['data_completeness'][col_name] = {
                    'non_null_count': int(non_null_count),
                    'completeness_ratio': round(completeness, 4)
                }

        return stats