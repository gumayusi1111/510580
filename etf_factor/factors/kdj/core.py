"""
KDJ核心计算模块
专注于KDJ随机指标的算法实现
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

# 导入KdjConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("kdj_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
KdjConfig = config_module.KdjConfig


class KDJ(BaseFactor):
    """KDJ随机指标因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = KdjConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算KDJ指标
        RSV = (收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) × 100
        K值 = 2/3 × 前一日K值 + 1/3 × 当日RSV
        D值 = 2/3 × 前一日D值 + 1/3 × 当日K值
        J值 = 3 × K值 - 2 × D值
        """
        result = data[['ts_code', 'trade_date']].copy()

        # 获取价格数据
        high_prices = data['hfq_high']
        low_prices = data['hfq_low']
        close_prices = data['hfq_close']

        period = self.params["period"]

        # 计算N日内最高价和最低价
        highest_high = high_prices.rolling(window=period, min_periods=1).max()
        lowest_low = low_prices.rolling(window=period, min_periods=1).min()

        # 计算RSV (Raw Stochastic Value)
        rsv = ((close_prices - lowest_low) / (highest_high - lowest_low)) * 100

        # 处理除零情况
        rsv = rsv.fillna(50)  # 当最高价等于最低价时，RSV设为50
        rsv = np.where(np.isinf(rsv), 50, rsv)

        # 确保rsv是pandas Series，然后转为numpy数组
        if isinstance(rsv, pd.Series):
            rsv_array = rsv.values
        else:
            rsv_array = rsv

        # 初始化K、D值
        k_values = np.zeros(len(data))
        d_values = np.zeros(len(data))

        # KDJ的初始值通常设为50
        k_values[0] = 50
        d_values[0] = 50

        # 逐步计算K、D值（使用指数移动平均的思想）
        for i in range(1, len(data)):
            # K = 2/3 * 前一日K + 1/3 * 当日RSV
            k_values[i] = (2/3) * k_values[i-1] + (1/3) * rsv_array[i]

            # D = 2/3 * 前一日D + 1/3 * 当日K
            d_values[i] = (2/3) * d_values[i-1] + (1/3) * k_values[i]

        # 如果只有一行数据，使用RSV作为K值
        if len(data) == 1:
            k_values[0] = rsv_array[0]
            d_values[0] = rsv_array[0]

        # 计算J值
        j_values = 3 * k_values - 2 * d_values

        # 应用精度配置
        precision = config.get_precision('indicator')
        result[f'KDJ_K_{period}'] = pd.Series(k_values).round(precision)
        result[f'KDJ_D_{period}'] = pd.Series(d_values).round(precision)
        result[f'KDJ_J_{period}'] = pd.Series(j_values).round(precision)

        # 数据验证和清理
        k_col = f'KDJ_K_{period}'
        d_col = f'KDJ_D_{period}'
        j_col = f'KDJ_J_{period}'

        # K和D值通常在0-100之间，但可以适当超出
        result[k_col] = result[k_col].clip(-20, 120)
        result[d_col] = result[d_col].clip(-20, 120)

        # J值可以超出0-100范围更多，这是正常的
        result[j_col] = result[j_col].clip(-50, 150)

        return result

    def get_required_columns(self) -> list:
        return KdjConfig.get_required_columns()

    def get_factor_info(self) -> dict:
        return KdjConfig.get_factor_info(self.params)

    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + KdjConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            if len(result) == 0:
                return False

            # 检查KDJ值的合理性
            period = self.params['period']
            k_col = f'KDJ_K_{period}'
            d_col = f'KDJ_D_{period}'
            j_col = f'KDJ_J_{period}'

            k_values = result[k_col].dropna()
            d_values = result[d_col].dropna()
            j_values = result[j_col].dropna()

            if len(k_values) == 0 or len(d_values) == 0 or len(j_values) == 0:
                return False

            # K、D值通常在合理范围内
            if (k_values < -50).any() or (k_values > 150).any():
                return False
            if (d_values < -50).any() or (d_values > 150).any():
                return False

            # J值可以有更大的范围
            if (j_values < -100).any() or (j_values > 200).any():
                return False

            # 检查是否有无穷大
            if np.isinf(k_values).any() or np.isinf(d_values).any() or np.isinf(j_values).any():
                return False

            return True

        except Exception:
            return False