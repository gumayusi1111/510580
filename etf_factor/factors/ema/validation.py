"""
EMA数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入EmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("ema_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
EmaConfig = config_module.EmaConfig


class EmaValidator:
    """指数移动均线因子数据验证器"""

    def __init__(self, params: dict):
        self.config = EmaConfig
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
        if len(data) < max_period:
            import warnings
            warnings.warn(f"数据长度({len(data)})小于最大计算周期({max_period})，EMA结果可能不稳定")

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
            warnings.warn(f"价格数据空值比例过高({null_ratio:.1%})，可能影响EMA计算准确性")

        # 检查价格异常值
        if len(non_null_prices) > 5:
            price_std = non_null_prices.std()
            price_mean = non_null_prices.mean()
            if price_mean > 0:
                cv = price_std / price_mean  # 变异系数
                if cv > 5:  # 变异系数过大，可能存在异常值
                    import warnings
                    warnings.warn(f"价格数据变异系数过大({cv:.2f})，可能存在异常值，影响EMA准确性")

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

            # 检查各周期的EMA数据
            for period in self.params['periods']:
                col_name = f'EMA_{period}'
                if not self._validate_period_ema(result[col_name], period):
                    return False

            return True

        except Exception:
            return False

    def _validate_period_ema(self, ema: pd.Series, period: int) -> bool:
        """验证特定周期的EMA数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(ema):
            return False

        # 获取非空数据
        non_null_ema = ema.dropna()

        # 如果全部为空，检查是否合理
        if len(non_null_ema) == 0:
            return len(ema) == 0

        # 检查无穷大值
        if np.isinf(non_null_ema).any():
            return False

        # EMA值应为正数（股票价格为正）
        if (non_null_ema <= 0).any():
            return False

        # EMA合理性检查
        # 正常股票价格通常在0.1到10000之间
        if (non_null_ema > 10000).any() or (non_null_ema < 0.001).any():
            extreme_ratio = ((non_null_ema > 10000) | (non_null_ema < 0.001)).sum() / len(non_null_ema)
            if extreme_ratio > 0.05:  # 5%以上为极端值
                return False

        # 检查EMA平滑性
        if len(non_null_ema) > 5:
            # EMA应该比原价格更平滑，计算相邻值变化率
            ema_diff = non_null_ema.diff().dropna()
            if len(ema_diff) > 0:
                # 检查是否有异常大的跳跃（可能表示计算错误）
                ema_mean = non_null_ema.mean()
                large_jump_ratio = (ema_diff.abs() > ema_mean * 0.5).sum() / len(ema_diff)
                if large_jump_ratio > 0.1:  # 10%以上的点有大跳跃
                    import warnings
                    warnings.warn(f"周期{period}的EMA存在异常大的跳跃({large_jump_ratio:.1%})，请检查数据质量")

            # 检查EMA的趋势一致性
            # EMA应该体现价格趋势，不应该频繁大幅震荡
            if len(non_null_ema) > 10:
                ema_volatility = ema_diff.std() / non_null_ema.mean() if non_null_ema.mean() > 0 else 0
                if ema_volatility > 0.2:  # 波动率超过20%
                    import warnings
                    warnings.warn(f"周期{period}的EMA波动率过高({ema_volatility:.1%})，可能需要检查数据质量")

        return True