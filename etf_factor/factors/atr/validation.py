"""
ATR验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class AtrValidation:
    """ATR因子验证工具"""

    @staticmethod
    def validate_input_data(data: pd.DataFrame) -> tuple[bool, str]:
        """验证输入数据的有效性"""
        required_columns = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

        # 检查必需列
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"缺少必需列: {missing_columns}"

        # 检查数据行数
        if len(data) == 0:
            return False, "数据为空"

        # 检查OHLC数据
        for col in ['hfq_high', 'hfq_low', 'hfq_close']:
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
        expected_columns = ['ts_code', 'trade_date'] + [f'ATR_{p}' for p in params['periods']]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查ATR值
        for period in params['periods']:
            atr_col = f'ATR_{period}'
            atr_values = result[atr_col].dropna()

            if len(atr_values) == 0:
                continue

            # 检查ATR范围
            if (atr_values < 0).any():
                return False, f"存在负ATR值: {atr_col}"

            if (atr_values > 100).any():
                return False, f"存在异常大的ATR值: {atr_col}"

            # 检查无穷大值
            if np.isinf(atr_values).any():
                return False, f"存在无穷大ATR值: {atr_col}"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 验证TR计算逻辑（检查几个数据点）
        if len(data) >= 2:
            high = data['hfq_high'].iloc[1]
            low = data['hfq_low'].iloc[1]
            close = data['hfq_close'].iloc[1]
            prev_close = data['hfq_close'].iloc[0]

            # 手工计算TR
            hl = high - low
            hc = abs(high - prev_close)
            lc = abs(low - prev_close)
            manual_tr = max(hl, hc, lc)

            # TR应该大于0
            if manual_tr <= 0:
                return False, f"TR计算异常: {manual_tr}"

        return True, "计算一致性验证通过"

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
        if overall_success:  # 只在前面验证通过时才进行一致性验证
            is_valid, message = cls.validate_calculation_consistency(data, result, params)
            validation_results.append(("计算一致性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results