"""
DC验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class DcValidation:
    """DC因子验证工具"""

    @staticmethod
    def validate_input_data(data: pd.DataFrame) -> tuple[bool, str]:
        """验证输入数据的有效性"""
        required_columns = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low']

        # 检查必需列
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"缺少必需列: {missing_columns}"

        # 检查数据行数
        if len(data) == 0:
            return False, "数据为空"

        # 检查OHLC数据
        for col in ['hfq_high', 'hfq_low']:
            prices = data[col]
            if prices.isnull().all():
                return False, f"所有{col}数据为空"

            # 检查价格是否为正数
            valid_prices = prices.dropna()
            if len(valid_prices) > 0 and (valid_prices <= 0).any():
                return False, f"存在非正{col}数据"

        # 检查高低价格逻辑
        valid_data = data[['hfq_high', 'hfq_low']].dropna()
        if len(valid_data) > 0:
            invalid_hl = valid_data['hfq_high'] < valid_data['hfq_low']
            if invalid_hl.any():
                return False, "存在高价小于低价的异常数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        period = params['period']
        expected_columns = ['ts_code', 'trade_date', f'DC_UPPER_{period}', f'DC_LOWER_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查DC值
        upper_col = f'DC_UPPER_{period}'
        lower_col = f'DC_LOWER_{period}'

        upper_values = result[upper_col].dropna()
        lower_values = result[lower_col].dropna()

        if len(upper_values) == 0 or len(lower_values) == 0:
            return False, "所有DC值为空"

        # 检查DC范围（应为正数）
        if (upper_values <= 0).any() or (lower_values <= 0).any():
            return False, "存在非正DC值"

        # 检查无穷大值
        if np.isinf(upper_values).any() or np.isinf(lower_values).any():
            return False, "存在无穷大DC值"

        # 检查上下轨关系
        valid_pairs = result[[upper_col, lower_col]].dropna()
        if len(valid_pairs) > 0:
            upper_lower_ok = (valid_pairs[upper_col] >= valid_pairs[lower_col]).all()
            if not upper_lower_ok:
                return False, "存在上轨小于下轨的异常情况"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的DC计算
        period = params['period']

        if len(data) >= period:
            recent_high = data['hfq_high'].tail(period)
            recent_low = data['hfq_low'].tail(period)

            manual_upper = recent_high.max()
            manual_lower = recent_low.min()

            upper_col = f'DC_UPPER_{period}'
            lower_col = f'DC_LOWER_{period}'
            calculated_upper = result[upper_col].iloc[-1]
            calculated_lower = result[lower_col].iloc[-1]

            # 允许小的数值误差（0.0001）
            if abs(calculated_upper - manual_upper) > 0.0001:
                return False, f"上轨计算不一致: 手工={manual_upper:.6f} vs 计算={calculated_upper:.6f}"
            if abs(calculated_lower - manual_lower) > 0.0001:
                return False, f"下轨计算不一致: 手工={manual_lower:.6f} vs 计算={calculated_lower:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_dc_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证唐奇安通道特性"""
        period = params['period']
        upper_col = f'DC_UPPER_{period}'
        lower_col = f'DC_LOWER_{period}'

        if upper_col not in result.columns or lower_col not in result.columns:
            return False, "缺少DC列"

        # 检查通道宽度的合理性
        valid_data = result[[upper_col, lower_col]].dropna()
        if len(valid_data) == 0:
            return False, "无有效DC数据"

        # 计算通道宽度
        channel_widths = (valid_data[upper_col] - valid_data[lower_col]) / valid_data[upper_col] * 100
        avg_width = channel_widths.mean()

        # 通道宽度应该为正数且在合理范围内
        if avg_width <= 0:
            return False, "通道宽度为负数或零"

        if avg_width > 50:  # 通道宽度超过50%可能异常
            return False, f"通道宽度过大: {avg_width:.2f}%"

        # 检查通道的突破特性
        # 价格应该在大部分时间内在通道内或边界上
        if len(data) >= len(valid_data):
            aligned_data = pd.concat([
                data[['hfq_high', 'hfq_low']].tail(len(valid_data)),
                valid_data
            ], axis=1)

            # 检查高价是否在上轨以下或等于上轨
            high_above_upper = (aligned_data['hfq_high'] > aligned_data[upper_col]).sum()
            # 检查低价是否在下轨以上或等于下轨
            low_below_lower = (aligned_data['hfq_low'] < aligned_data[lower_col]).sum()

            total_points = len(aligned_data)
            breakout_ratio = (high_above_upper + low_below_lower) / total_points if total_points > 0 else 0

            # 允许少量突破（通常不超过10%）
            if breakout_ratio > 0.2:  # 20%的突破率可能太高
                return False, f"通道突破率过高: {breakout_ratio:.2%}"

        # 检查DC的稳定性（通道应该随时间平滑变化）
        if len(valid_data) >= 5:
            upper_changes = valid_data[upper_col].diff().abs()
            lower_changes = valid_data[lower_col].diff().abs()

            # 计算相对变化率
            upper_volatility = upper_changes.mean() / valid_data[upper_col].mean()
            lower_volatility = lower_changes.mean() / valid_data[lower_col].mean()

            # DC通道不应该过度波动（这里只是警告级别的检查）
            if upper_volatility > 0.1 or lower_volatility > 0.1:
                return True, f"DC通道变化较大但在可接受范围: 上轨波动={upper_volatility:.2%}, 下轨波动={lower_volatility:.2%}, 平均宽度={avg_width:.1f}%"

        return True, f"DC特性验证通过: 平均通道宽度={avg_width:.1f}%"

    @classmethod
    def run_full_validation(cls, data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, list]:
        """运行完整验证流程"""
        validation_results = []
        overall_success = True

        # 输入数据验证
        is_valid, message = cls.validate_input_data(data)
        validation_results.append(("输入数据验证", is_valid, message))
        if not is_valid:
            overall_success = False

        # 输出数据验证
        is_valid, message = cls.validate_output_data(result, params)
        validation_results.append(("输出数据验证", is_valid, message))
        if not is_valid:
            overall_success = False

        # 计算一致性验证
        if overall_success:
            is_valid, message = cls.validate_calculation_consistency(data, result, params)
            validation_results.append(("计算一致性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        # DC特性验证
        if overall_success:
            is_valid, message = cls.validate_dc_properties(result, data, params)
            validation_results.append(("DC特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results