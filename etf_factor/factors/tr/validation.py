"""
TR数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入TrConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("tr_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
TrConfig = config_module.TrConfig


class TrValidator:
    """真实波幅因子数据验证器"""

    def __init__(self, params: dict):
        self.config = TrConfig
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

        # 检查数据长度
        if len(data) < 2:
            import warnings
            warnings.warn(f"数据长度({len(data)})少于2行，第一行TR结果将为NaN（缺少前一日收盘价）")

        # 检查OHLC数据
        self._validate_ohlc_data(data)

        # 检查日期数据
        self._validate_date_data(data['trade_date'])

    def _validate_ohlc_data(self, data: pd.DataFrame) -> None:
        """验证OHLC数据的合理性"""
        price_columns = ['hfq_high', 'hfq_low', 'hfq_close']

        for col in price_columns:
            prices = data[col]

            # 检查数据类型
            if not pd.api.types.is_numeric_dtype(prices):
                raise ValueError(f"{col}数据必须是数值类型")

            # 检查非空数据
            non_null_prices = prices.dropna()
            if len(non_null_prices) == 0:
                raise ValueError(f"{col}数据不能全部为空")

            # 检查价格合理性（必须为正数）
            if (non_null_prices <= 0).any():
                raise ValueError(f"{col}必须大于0")

            # 检查连续性（不应有过多的空值）
            null_ratio = prices.isnull().sum() / len(prices)
            if null_ratio > 0.3:  # 30%以上为空值
                import warnings
                warnings.warn(f"{col}数据空值比例过高({null_ratio:.1%})，可能影响TR计算准确性")

        # 检查OHLC逻辑关系
        self._validate_ohlc_relationships(data)

    def _validate_ohlc_relationships(self, data: pd.DataFrame) -> None:
        """验证OHLC数据之间的逻辑关系"""
        # 获取有效数据行（所有价格都不为空的行）
        valid_mask = data[['hfq_high', 'hfq_low', 'hfq_close']].notna().all(axis=1)
        valid_data = data[valid_mask]

        if len(valid_data) == 0:
            return

        # 检查 high >= low
        invalid_hl = valid_data['hfq_high'] < valid_data['hfq_low']
        if invalid_hl.any():
            raise ValueError("发现最高价小于最低价的异常数据")

        # 检查 low <= close <= high
        invalid_close_high = valid_data['hfq_close'] > valid_data['hfq_high']
        invalid_close_low = valid_data['hfq_close'] < valid_data['hfq_low']

        if invalid_close_high.any() or invalid_close_low.any():
            import warnings
            warnings.warn("发现收盘价超出当日高低价范围的数据，可能影响TR计算")

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

            # 检查TR数据
            return self._validate_tr_values(result['TR'])

        except Exception:
            return False

    def _validate_tr_values(self, tr: pd.Series) -> bool:
        """验证TR数值的合理性"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(tr):
            return False

        # 获取非空数据
        non_null_tr = tr.dropna()

        # 第一行可能为NaN是正常的（缺少前一日收盘价）
        if len(non_null_tr) == 0:
            # 如果全部为空，检查是否因为数据不足
            return len(tr) <= 1

        # 检查无穷大值
        if np.isinf(non_null_tr).any():
            return False

        # TR值应为非负数
        if (non_null_tr < 0).any():
            return False

        # TR值合理性检查
        # 正常TR值通常在0-100之间，极端情况可能超过但很少超过1000
        if (non_null_tr > 1000).any():
            extreme_ratio = (non_null_tr > 1000).sum() / len(non_null_tr)
            if extreme_ratio > 0.05:  # 5%以上为极端值
                return False

        # 检查数据分布的合理性
        if len(non_null_tr) > 10:
            # 检查零值比例（如果TR经常为0，可能表示价格无波动）
            zero_ratio = (non_null_tr == 0).sum() / len(non_null_tr)
            if zero_ratio > 0.5:  # 50%以上为零值
                import warnings
                warnings.warn(f"TR零值比例过高({zero_ratio:.1%})，可能表示价格缺乏波动")

            # 检查标准差的合理性
            tr_std = non_null_tr.std()
            if tr_std > 100:  # 标准差超过100可能表示数据异常波动
                import warnings
                warnings.warn(f"TR标准差过大({tr_std:.2f})，请检查数据质量")

        return True