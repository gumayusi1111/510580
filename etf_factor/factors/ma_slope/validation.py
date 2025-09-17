"""
MA_SLOPE数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入MaSlopeConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("ma_slope_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MaSlopeConfig = config_module.MaSlopeConfig


class MaSlopeValidator:
    """移动均线斜率因子数据验证器"""

    def __init__(self, params: dict):
        self.config = MaSlopeConfig
        self.params = params

    def validate_input_data(self, data: pd.DataFrame) -> None:
        """
        验证输入数据的完整性和正确性

        Args:
            data: 输入的价格数据DataFrame

        Raises:
            ValueError: 当数据不符合要求时
        """
        # 基础检查
        if not isinstance(data, pd.DataFrame):
            raise ValueError("输入数据必须是pandas DataFrame")

        if len(data) == 0:
            raise ValueError("输入数据不能为空")

        # 检查必需列
        required_columns = self.config.get_required_columns()
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必需的数据列: {missing_columns}")

        # 检查数据长度是否足够
        max_period = max(self.params['periods'])
        min_required_length = max_period * 2  # 需要足够数据来计算斜率
        if len(data) < min_required_length:
            import warnings
            warnings.warn(f"数据长度({len(data)})小于建议最小长度({min_required_length})，部分结果可能为空")

        # 检查收盘价数据
        self._validate_price_data(data['hfq_close'])

        # 检查日期数据
        self._validate_date_data(data['trade_date'])

    def _validate_price_data(self, prices: pd.Series) -> None:
        """验证价格数据的合理性"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(prices):
            raise ValueError("收盘价数据必须是数值类型")

        # 检查非空数据
        non_null_prices = prices.dropna()
        if len(non_null_prices) == 0:
            raise ValueError("收盘价数据不能全部为空")

        # 检查价格合理性（必须为正数）
        if (non_null_prices <= 0).any():
            raise ValueError("收盘价必须大于0")

        # 检查连续性（不应有过多的空值）
        null_ratio = prices.isnull().sum() / len(prices)
        if null_ratio > 0.3:  # 30%以上为空值
            import warnings
            warnings.warn(f"价格数据空值比例过高({null_ratio:.1%})，可能影响MA斜率计算准确性")

    def _validate_date_data(self, dates: pd.Series) -> None:
        """验证日期数据的合理性"""
        # 检查日期数据存在
        if dates.isnull().all():
            raise ValueError("交易日期数据不能全部为空")

        # 尝试转换为日期类型
        try:
            pd.to_datetime(dates.dropna())
        except Exception:
            raise ValueError("交易日期数据格式不正确")

    def validate_output_result(self, result: pd.DataFrame) -> bool:
        """
        验证输出结果的合理性

        Args:
            result: 计算结果DataFrame

        Returns:
            bool: 验证是否通过
        """
        try:
            # 基础检查
            if not isinstance(result, pd.DataFrame):
                return False

            if len(result) == 0:
                return False

            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + self.config.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False

            # 检查各周期的MA斜率数据
            for period in self.params['periods']:
                col_name = f'MA_SLOPE_{period}'
                if not self._validate_period_slope(result[col_name], period):
                    return False

            return True

        except Exception:
            return False

    def _validate_period_slope(self, slope: pd.Series, period: int) -> bool:
        """验证特定周期的MA斜率数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(slope):
            return False

        # 获取非空数据
        non_null_slope = slope.dropna()

        # 前period*2行应该为NaN是正常的（需要足够的历史数据）
        expected_null_count = min(period * 2, len(slope))

        # 如果全部为空，只有在数据不足时才正常
        if len(non_null_slope) == 0:
            return len(slope) <= period * 2

        # 检查无穷大值
        if np.isinf(non_null_slope).any():
            return False

        # MA斜率的合理性检查
        # 斜率值通常在较小的范围内，过大的斜率可能表示数据异常
        if (non_null_slope.abs() > 10).any():
            extreme_ratio = (non_null_slope.abs() > 10).sum() / len(non_null_slope)
            if extreme_ratio > 0.05:  # 5%以上为极端值
                return False

        # 检查数据分布的合理性
        if len(non_null_slope) > 10:
            # 检查零值比例（如果斜率经常为0，可能表示价格趋势平缓）
            zero_ratio = (non_null_slope.abs() < 0.001).sum() / len(non_null_slope)
            if zero_ratio > 0.8:  # 80%以上接近零值
                import warnings
                warnings.warn(f"周期{period}的MA斜率接近零值比例过高({zero_ratio:.1%})，可能表示趋势不明显")

            # 检查标准差的合理性
            slope_std = non_null_slope.std()
            if slope_std > 5:  # 标准差超过5可能表示斜率波动过大
                import warnings
                warnings.warn(f"周期{period}的MA斜率标准差过大({slope_std:.2f})，请检查数据质量")

            # 检查异常高斜率的比例
            high_slope_ratio = (non_null_slope.abs() > 2).sum() / len(non_null_slope)  # 绝对值大于2的斜率
            if high_slope_ratio > 0.2:  # 20%以上的数据点有高斜率
                import warnings
                warnings.warn(f"周期{period}的MA斜率中高斜率数据点较多({high_slope_ratio:.1%})，请检查数据质量")

        return True