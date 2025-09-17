"""
CUM_RETURN数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np
# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入CumReturnConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("cum_return_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
CumReturnConfig = config_module.CumReturnConfig


class CumReturnValidator:
    """累计收益率因子数据验证器"""

    def __init__(self, params: dict):
        self.config = CumReturnConfig
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
        if len(data) < max_period + 1:
            import warnings
            warnings.warn(f"数据长度({len(data)})小于最大计算周期({max_period})，部分结果可能为空")

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
            warnings.warn(f"价格数据空值比例过高({null_ratio:.1%})，可能影响计算准确性")

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

            # 检查各周期的累计收益率数据
            for period in self.params['periods']:
                col_name = f'CUM_RETURN_{period}'
                if not self._validate_period_returns(result[col_name], period):
                    return False

            return True

        except Exception:
            return False

    def _validate_period_returns(self, returns: pd.Series, period: int) -> bool:
        """验证特定周期的累计收益率数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(returns):
            return False

        # 获取非空数据
        non_null_returns = returns.dropna()

        # 前period行应该为NaN是正常的
        expected_null_count = min(period, len(returns))
        actual_null_count = returns.isnull().sum()

        # 如果全部为空，只有在数据不足时才正常
        if len(non_null_returns) == 0:
            return len(returns) <= period

        # 检查无穷大值
        if np.isinf(non_null_returns).any():
            return False

        # 累计收益率应在合理范围内
        # 正常情况下很少超过±100%，极端情况可能达到±500%
        if (non_null_returns < -100).any() or (non_null_returns > 1000).any():
            return False

        # 检查数据分布的合理性
        # 累计收益率的标准差不应过大
        if len(non_null_returns) > 10:
            std_dev = non_null_returns.std()
            if std_dev > 200:  # 标准差超过200%可能有问题
                import warnings
                warnings.warn(f"周期{period}的累计收益率标准差过大({std_dev:.1f}%)，请检查数据质量")

        return True