"""
MACD数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入MacdConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("macd_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
MacdConfig = config_module.MacdConfig


class MacdValidator:
    """MACD指标因子数据验证器"""

    def __init__(self, params: dict):
        self.config = MacdConfig
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
        max_period = max(self.params['slow_period'], self.params['fast_period'], self.params['signal_period'])
        min_required_length = max_period + self.params['signal_period']  # MACD需要足够数据来计算信号线
        if len(data) < min_required_length:
            import warnings
            warnings.warn(f"数据长度({len(data)})小于建议最小长度({min_required_length})，MACD结果可能不稳定")

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
            warnings.warn(f"价格数据空值比例过高({null_ratio:.1%})，可能影响MACD计算准确性")

        # 检查价格序列的有效性
        if len(non_null_prices) > 5:
            # 检查是否存在异常的价格跳跃
            price_changes = non_null_prices.pct_change().dropna()
            extreme_changes = (price_changes.abs() > 0.5).sum()  # 50%以上变化
            if extreme_changes > len(price_changes) * 0.1:  # 10%以上的点有极端变化
                import warnings
                warnings.warn(f"价格数据存在较多极端变化({extreme_changes}个)，可能影响MACD准确性")

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

            # 检查MACD各组件数据
            return self._validate_macd_components(result)

        except Exception:
            return False

    def _validate_macd_components(self, result: pd.DataFrame) -> bool:
        """验证MACD各组件的数值合理性"""
        macd_columns = ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']

        for col_name in macd_columns:
            if not self._validate_macd_component(result[col_name], col_name):
                return False

        # 验证MACD组件之间的逻辑关系
        return self._validate_macd_relationships(result)

    def _validate_macd_component(self, values: pd.Series, component_name: str) -> bool:
        """验证MACD单个组件的数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(values):
            return False

        # 获取非空数据
        non_null_values = values.dropna()

        # 如果全部为空，检查是否合理
        if len(non_null_values) == 0:
            return len(values) == 0

        # 检查无穷大值
        if np.isinf(non_null_values).any():
            return False

        # MACD值合理性检查
        # 正常MACD值通常在-100到100之间，极端情况可能更大
        if (non_null_values.abs() > 1000).any():
            extreme_ratio = (non_null_values.abs() > 1000).sum() / len(non_null_values)
            if extreme_ratio > 0.05:  # 5%以上为极端值
                return False

        # 检查数据分布的合理性
        if len(non_null_values) > 10:
            # 检查是否有过多的零值（可能表示计算错误）
            zero_ratio = (non_null_values.abs() < 0.001).sum() / len(non_null_values)
            if zero_ratio > 0.9:  # 90%以上接近零值
                import warnings
                warnings.warn(f"{component_name}接近零值比例过高({zero_ratio:.1%})，可能表示计算异常")

            # 检查MACD组件的波动合理性
            values_std = non_null_values.std()
            values_mean = non_null_values.mean()

            # MACD_HIST通常比DIF和DEA波动更大
            if component_name == 'MACD_HIST':
                if values_std > 50:  # HIST标准差过大
                    import warnings
                    warnings.warn(f"{component_name}标准差过大({values_std:.2f})，请检查数据质量")
            else:  # DIF 和 DEA
                if values_std > 20:  # DIF/DEA标准差过大
                    import warnings
                    warnings.warn(f"{component_name}标准差过大({values_std:.2f})，请检查数据质量")

        return True

    def _validate_macd_relationships(self, result: pd.DataFrame) -> bool:
        """验证MACD各组件之间的逻辑关系"""
        try:
            dif = result['MACD_DIF'].dropna()
            dea = result['MACD_DEA'].dropna()
            hist = result['MACD_HIST'].dropna()

            # 如果数据不足，跳过关系验证
            if len(dif) == 0 or len(dea) == 0 or len(hist) == 0:
                return True

            # 获取对齐的有效数据
            common_index = dif.index.intersection(dea.index).intersection(hist.index)
            if len(common_index) == 0:
                return True

            dif_aligned = dif[common_index]
            dea_aligned = dea[common_index]
            hist_aligned = hist[common_index]

            # 验证 HIST = DIF - DEA 关系
            calculated_hist = dif_aligned - dea_aligned
            hist_diff = (hist_aligned - calculated_hist).abs()

            # 允许一定的数值误差（由于精度问题）
            tolerance = 0.01
            invalid_ratio = (hist_diff > tolerance).sum() / len(hist_diff)

            if invalid_ratio > 0.05:  # 5%以上的数据点关系不正确
                import warnings
                warnings.warn(f"MACD组件关系验证失败，{invalid_ratio:.1%}的数据点HIST≠DIF-DEA")
                return False

            # 验证DEA的平滑特性：DEA应该比DIF更平滑
            if len(dif_aligned) > 5:
                dif_volatility = dif_aligned.diff().abs().mean()
                dea_volatility = dea_aligned.diff().abs().mean()

                # DEA作为DIF的EMA，通常应该比DIF更平滑
                if dea_volatility > dif_volatility * 1.5:  # DEA波动显著大于DIF
                    import warnings
                    warnings.warn("DEA波动性异常，可能存在计算问题")

            return True

        except Exception:
            return False