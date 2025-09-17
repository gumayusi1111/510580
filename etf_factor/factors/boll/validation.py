"""
BOLL验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class BollValidation:
    """BOLL因子验证工具"""

    @staticmethod
    def validate_input_data(data: pd.DataFrame) -> tuple[bool, str]:
        """验证输入数据的有效性"""
        required_columns = ['ts_code', 'trade_date', 'hfq_close']

        # 检查必需列
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"缺少必需列: {missing_columns}"

        # 检查数据行数
        if len(data) == 0:
            return False, "数据为空"

        # 检查收盘价数据
        close_prices = data['hfq_close']
        if close_prices.isnull().all():
            return False, "所有收盘价数据为空"

        # 检查价格是否为正数
        valid_prices = close_prices.dropna()
        if len(valid_prices) > 0 and (valid_prices <= 0).any():
            return False, "存在非正价格数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        expected_columns = ['ts_code', 'trade_date', 'BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查布林带值
        boll_columns = ['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']
        for col in boll_columns:
            values = result[col].dropna()

            if len(values) == 0:
                continue

            # 价格值应为正数
            if (values <= 0).any():
                return False, f"存在非正{col}值"

            # 检查无穷大值
            if np.isinf(values).any():
                return False, f"存在无穷大{col}值"

        # 检查布林带的逻辑关系
        valid_data = result.dropna(subset=boll_columns)
        if len(valid_data) > 0:
            # 上轨 >= 中轨 >= 下轨
            upper_mid_ok = (valid_data['BOLL_UPPER'] >= valid_data['BOLL_MID']).all()
            mid_lower_ok = (valid_data['BOLL_MID'] >= valid_data['BOLL_LOWER']).all()

            if not upper_mid_ok:
                return False, "存在上轨小于中轨的异常情况"
            if not mid_lower_ok:
                return False, "存在中轨小于下轨的异常情况"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后一个有效数据点的计算
        period = params['period']
        std_dev = params['std_dev']

        if len(data) >= period:
            recent_data = data['hfq_close'].tail(period)
            manual_mid = recent_data.mean()
            manual_std = recent_data.std()
            manual_upper = manual_mid + std_dev * manual_std
            manual_lower = manual_mid - std_dev * manual_std

            calculated_mid = result['BOLL_MID'].iloc[-1]
            calculated_upper = result['BOLL_UPPER'].iloc[-1]
            calculated_lower = result['BOLL_LOWER'].iloc[-1]

            # 允许小的数值误差（0.0001）
            if abs(calculated_mid - manual_mid) > 0.0001:
                return False, f"中轨计算不一致: 手工={manual_mid:.6f} vs 计算={calculated_mid:.6f}"
            if abs(calculated_upper - manual_upper) > 0.0001:
                return False, f"上轨计算不一致: 手工={manual_upper:.6f} vs 计算={calculated_upper:.6f}"
            if abs(calculated_lower - manual_lower) > 0.0001:
                return False, f"下轨计算不一致: 手工={manual_lower:.6f} vs 计算={calculated_lower:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_bollinger_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证布林带特性"""
        close_prices = data['hfq_close'].dropna()
        if len(close_prices) == 0:
            return False, "无有效价格数据"

        # 检查价格与布林带的关系
        valid_data = result.dropna(subset=['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER'])
        if len(valid_data) == 0:
            return False, "无有效布林带数据"

        # 对齐价格和布林带数据
        aligned_data = pd.concat([close_prices, valid_data[['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']]], axis=1).dropna()
        if len(aligned_data) == 0:
            return False, "无法对齐价格和布林带数据"

        # 检查价格突破的合理性
        # 价格应该大部分时间在布林带内（通常95%的时间）
        prices = aligned_data['hfq_close']
        upper = aligned_data['BOLL_UPPER']
        lower = aligned_data['BOLL_LOWER']

        within_bands = ((prices >= lower) & (prices <= upper)).sum()
        total_points = len(aligned_data)
        within_ratio = within_bands / total_points if total_points > 0 else 0

        # 允许一定的突破，但不应该太频繁
        if within_ratio < 0.8:  # 80%的时间应该在带内
            return False, f"价格在布林带内的比例过低: {within_ratio:.2%}"

        # 检查布林带宽度的合理性
        band_widths = (upper - lower) / aligned_data['BOLL_MID'] * 100  # 相对宽度
        avg_width = band_widths.mean()

        # 布林带宽度应该在合理范围内（通常1%-50%）
        if avg_width < 0.5 or avg_width > 50:
            return False, f"布林带平均宽度不合理: {avg_width:.2f}%"

        # 检查中轨是否为移动平均
        period = params['period']
        if len(prices) >= period:
            manual_sma = prices.tail(period).mean()
            calculated_mid = aligned_data['BOLL_MID'].iloc[-1]

            if abs(manual_sma - calculated_mid) > 0.01:
                return False, f"中轨不等于移动平均: SMA={manual_sma:.6f}, 中轨={calculated_mid:.6f}"

        return True, f"布林带特性验证通过: 价格在带内比例={within_ratio:.1%}, 平均宽度={avg_width:.1f}%"

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

        # 布林带特性验证
        if overall_success:
            is_valid, message = cls.validate_bollinger_properties(result, data, params)
            validation_results.append(("布林带特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results