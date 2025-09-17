"""
WR验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class WrValidation:
    """威廉指标因子验证工具"""

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
        period = params['period']
        expected_columns = ['ts_code', 'trade_date', f'WR_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查WR值
        wr_col = f'WR_{period}'
        wr_values = result[wr_col].dropna()

        if len(wr_values) == 0:
            return False, "所有WR值为空"

        # 检查WR范围（-100到0）
        if (wr_values < -100).any() or (wr_values > 0).any():
            return False, f"存在超出范围的WR值: {wr_col}"

        # 检查无穷大值
        if np.isinf(wr_values).any():
            return False, "存在无穷大WR值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 验证最后一个有效数据点的WR计算
        period = params['period']

        if len(data) >= period:
            recent_data = data.tail(period)
            manual_high = recent_data['hfq_high'].max()
            manual_low = recent_data['hfq_low'].min()
            current_close = recent_data['hfq_close'].iloc[-1]

            # 避免除零
            if manual_high != manual_low:
                manual_wr = ((manual_high - current_close) / (manual_high - manual_low)) * (-100)

                wr_col = f'WR_{period}'
                calculated_wr = result[wr_col].iloc[-1]

                # 允许小的数值误差（0.01）
                if abs(calculated_wr - manual_wr) > 0.01:
                    return False, f"计算不一致: 手工WR={manual_wr:.4f} vs 计算WR={calculated_wr:.4f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_wr_signals(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证WR信号合理性"""
        period = params['period']
        wr_col = f'WR_{period}'

        if wr_col not in result.columns:
            return False, f"缺少WR列: {wr_col}"

        wr_values = result[wr_col].dropna()
        if len(wr_values) == 0:
            return False, "无有效WR值"

        # 检查信号分布合理性
        overbought = (wr_values > -20).sum()  # 超买
        oversold = (wr_values < -80).sum()    # 超卖
        normal = len(wr_values) - overbought - oversold

        # 各种情况的比例应该合理
        total = len(wr_values)
        overbought_ratio = overbought / total
        oversold_ratio = oversold / total
        normal_ratio = normal / total

        # 通常情况下，超买和超卖信号不应该占主导地位
        if overbought_ratio > 0.5 or oversold_ratio > 0.5:
            return False, f"WR信号分布异常: 超买{overbought_ratio:.1%}, 超卖{oversold_ratio:.1%}, 正常{normal_ratio:.1%}"

        return True, f"WR信号合理性验证通过: 超买{overbought_ratio:.1%}, 超卖{oversold_ratio:.1%}, 正常{normal_ratio:.1%}"

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

        # WR信号合理性验证
        if overall_success:
            is_valid, message = cls.validate_wr_signals(result, params)
            validation_results.append(("WR信号验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results