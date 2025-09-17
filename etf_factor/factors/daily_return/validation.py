"""
DAILY_RETURN数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np
from config import DailyReturnConfig


class DailyReturnValidator:
    """日收益率因子数据验证器"""

    def __init__(self):
        self.config = DailyReturnConfig

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

        # 检查异常值（价格变化超过1000倍可能是数据错误）
        if len(non_null_prices) > 1:
            price_changes = non_null_prices.pct_change().abs()
            if (price_changes > 10).any():  # 1000%的变化
                import warnings
                warnings.warn("检测到异常的价格变化，请检查数据质量")

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
            expected_columns = ['ts_code', 'trade_date', 'DAILY_RETURN']
            if not all(col in result.columns for col in expected_columns):
                return False

            # 检查日收益率数据
            returns = result['DAILY_RETURN'].dropna()

            # 允许第一行为NaN（因为没有前一日数据）
            if len(returns) == 0 and len(result) > 0:
                return True  # 只有第一行，且为NaN是正常的

            # 检查数据合理性
            if not self._validate_return_values(returns):
                return False

            return True

        except Exception:
            return False

    def _validate_return_values(self, returns: pd.Series) -> bool:
        """验证收益率数值的合理性"""
        # 检查数值类型
        if not pd.api.types.is_numeric_dtype(returns):
            return False

        # 检查无穷大值
        if np.isinf(returns).any():
            return False

        # 日收益率应在合理范围内
        # 正常情况下，单日收益率很少超过±50%
        # 极端情况下可能达到±100%，但不应超过这个范围
        if (returns < -100).any() or (returns > 100).any():
            return False

        # 检查是否有过多的零值（可能表示数据质量问题）
        zero_ratio = (returns == 0).sum() / len(returns)
        if zero_ratio > 0.9:  # 90%以上为零值可能有问题
            import warnings
            warnings.warn("日收益率数据中零值比例过高，请检查数据质量")

        return True