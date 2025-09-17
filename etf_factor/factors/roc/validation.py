"""
ROC数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入RocConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("roc_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
RocConfig = config_module.RocConfig


class RocValidator:
    """变动率指标因子数据验证器"""

    def __init__(self, params: dict):
        self.config = RocConfig
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
            warnings.warn(f"数据长度({len(data)})小于最大计算周期+1({max_period+1})，部分结果可能为空")

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

        # 检查价格合理性（必须为正数，因为ROC计算涉及除法）
        if (non_null_prices <= 0).any():
            raise ValueError("收盘价必须大于0（ROC计算需要用作除数）")

        # 检查连续性（不应有过多的空值）
        null_ratio = prices.isnull().sum() / len(prices)
        if null_ratio > 0.3:  # 30%以上为空值
            import warnings
            warnings.warn(f"价格数据空值比例过高({null_ratio:.1%})，可能影响ROC计算准确性")

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

            # 检查各周期的变动率指标数据
            for period in self.params['periods']:
                col_name = f'ROC_{period}'
                if not self._validate_period_roc(result[col_name], period):
                    return False

            return True

        except Exception:
            return False

    def _validate_period_roc(self, roc: pd.Series, period: int) -> bool:
        """验证特定周期的变动率指标数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(roc):
            return False

        # 获取非空数据
        non_null_roc = roc.dropna()

        # 前period行应该为NaN是正常的
        expected_null_count = min(period, len(roc))

        # 如果全部为空，只有在数据不足时才正常
        if len(non_null_roc) == 0:
            return len(roc) <= period

        # 检查无穷大值
        if np.isinf(non_null_roc).any():
            return False

        # 变动率指标的合理性检查
        # ROC是百分比变化，正常范围通常在±100%以内
        # 极端情况下可能达到±1000%，但很少超过这个范围
        if (non_null_roc.abs() > 1000).any():
            extreme_ratio = (non_null_roc.abs() > 1000).sum() / len(non_null_roc)
            if extreme_ratio > 0.05:  # 5%以上为极端值
                return False

        # 检查数据分布的合理性
        if len(non_null_roc) > 10:
            # 检查零值比例（如果ROC经常为0，可能表示价格没有变化）
            zero_ratio = (non_null_roc == 0).sum() / len(non_null_roc)
            if zero_ratio > 0.8:  # 80%以上为零值
                import warnings
                warnings.warn(f"周期{period}的ROC零值比例过高({zero_ratio:.1%})，可能表示价格缺乏变化")

            # 检查标准差的合理性
            roc_std = non_null_roc.std()
            if roc_std > 200:  # 标准差超过200%可能表示数据异常
                import warnings
                warnings.warn(f"周期{period}的ROC标准差过大({roc_std:.1f}%)，请检查数据质量")

            # 检查异常高变动率的比例
            high_roc_ratio = (non_null_roc.abs() > 50).sum() / len(non_null_roc)  # 50%以上变动率
            if high_roc_ratio > 0.2:  # 20%以上的数据点有高变动率
                import warnings
                warnings.warn(f"周期{period}的ROC中高变动率数据点较多({high_roc_ratio:.1%})，请检查数据质量")

        return True