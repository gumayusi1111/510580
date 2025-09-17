"""
VMA数据验证模块
处理输入数据验证和输出结果检查
"""

import pandas as pd
import numpy as np

# 使用绝对路径导入避免模块名冲突
import importlib.util
import os

# 导入VmaConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("vma_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
VmaConfig = config_module.VmaConfig


class VmaValidator:
    """成交量移动均线因子数据验证器"""

    def __init__(self, params: dict):
        self.config = VmaConfig
        self.params = params

    def validate_input_data(self, data: pd.DataFrame) -> None:
        """
        验证输入数据的完整性和正确性

        Args:
            data: 输入的成交量数据DataFrame

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
            warnings.warn(f"数据长度({len(data)})小于最大计算周期({max_period})，部分结果可能不准确")

        # 检查成交量数据
        self._validate_volume_data(data['vol'])

        # 检查日期数据
        self._validate_date_data(data['trade_date'])

    def _validate_volume_data(self, volume: pd.Series) -> None:
        """验证成交量数据的合理性"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(volume):
            raise ValueError("成交量数据必须是数值类型")

        # 检查非空数据
        non_null_volume = volume.dropna()
        if len(non_null_volume) == 0:
            raise ValueError("成交量数据不能全部为空")

        # 检查成交量合理性（应为非负数）
        if (non_null_volume < 0).any():
            raise ValueError("成交量必须为非负数")

        # 检查成交量数据连续性
        null_ratio = volume.isnull().sum() / len(volume)
        if null_ratio > 0.3:  # 30%以上为空值
            import warnings
            warnings.warn(f"成交量数据空值比例过高({null_ratio:.1%})，可能影响VMA计算准确性")

        # 检查成交量数据分布合理性
        if len(non_null_volume) > 5:
            # 检查是否有过多零值（可能表示停牌或数据问题）
            zero_ratio = (non_null_volume == 0).sum() / len(non_null_volume)
            if zero_ratio > 0.5:  # 50%以上为零值
                import warnings
                warnings.warn(f"成交量零值比例过高({zero_ratio:.1%})，可能影响分析有效性")

            # 检查成交量波动性
            volume_std = non_null_volume.std()
            volume_mean = non_null_volume.mean()
            if volume_mean > 0:
                cv = volume_std / volume_mean  # 变异系数
                if cv > 10:  # 变异系数过大
                    import warnings
                    warnings.warn(f"成交量变异系数过大({cv:.2f})，数据波动性异常")

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

            # 检查各周期的VMA数据
            for period in self.params['periods']:
                col_name = f'VMA_{period}'
                if not self._validate_period_vma(result[col_name], period):
                    return False

            return True

        except Exception:
            return False

    def _validate_period_vma(self, vma: pd.Series, period: int) -> bool:
        """验证特定周期的VMA数值"""
        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(vma):
            return False

        # 获取非空数据
        non_null_vma = vma.dropna()

        # 如果全部为空，检查是否合理
        if len(non_null_vma) == 0:
            return len(vma) == 0

        # 检查无穷大值
        if np.isinf(non_null_vma).any():
            return False

        # VMA值应为非负数（成交量移动均线不能为负）
        if (non_null_vma < 0).any():
            return False

        # VMA合理性检查
        if len(non_null_vma) > 5:
            # 检查零值比例
            zero_ratio = (non_null_vma == 0).sum() / len(non_null_vma)
            if zero_ratio > 0.8:  # 80%以上为零值
                import warnings
                warnings.warn(f"周期{period}的VMA零值比例过高({zero_ratio:.1%})，可能表示成交量长期为零")

            # 检查VMA的变异系数
            vma_std = non_null_vma.std()
            vma_mean = non_null_vma.mean()
            if vma_mean > 0:
                cv = vma_std / vma_mean
                if cv > 15:  # 变异系数过大
                    import warnings
                    warnings.warn(f"周期{period}的VMA变异系数过大({cv:.2f})，请检查数据质量")

            # 检查VMA数值范围合理性
            # 对于正常ETF，成交量通常在特定范围内
            vma_max = non_null_vma.max()
            vma_min = non_null_vma.min()

            # 如果最大值是最小值的10000倍以上，可能有异常
            if vma_min > 0 and vma_max / vma_min > 10000:
                import warnings
                warnings.warn(f"周期{period}的VMA数值范围过大(最大值/最小值={vma_max/vma_min:.0f})，请检查数据")

        return True