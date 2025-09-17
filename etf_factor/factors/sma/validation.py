"""
SMA验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class SmaValidation:
    """SMA因子验证工具"""

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
        expected_columns = ['ts_code', 'trade_date'] + [f'SMA_{p}' for p in params['periods']]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查SMA值
        for period in params['periods']:
            sma_col = f'SMA_{period}'
            sma_values = result[sma_col].dropna()

            if len(sma_values) == 0:
                continue

            # SMA值应为正数
            if (sma_values <= 0).any():
                return False, f"存在非正SMA值: {sma_col}"

            # SMA值应在合理范围内
            if (sma_values > 10000).any() or (sma_values < 0.001).any():
                return False, f"SMA值超出合理范围: {sma_col}"

            # 检查无穷大值
            if np.isinf(sma_values).any():
                return False, f"存在无穷大SMA值: {sma_col}"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的SMA计算
        for period in params['periods']:
            if len(data) >= period:
                # 取最后period个数据点计算SMA
                recent_prices = data['hfq_close'].tail(period)
                manual_sma = recent_prices.mean()

                sma_col = f'SMA_{period}'
                calculated_sma = result[sma_col].iloc[-1]

                # 允许小的数值误差（0.0001）
                if abs(calculated_sma - manual_sma) > 0.0001:
                    return False, f"SMA_{period}计算不一致: 手工={manual_sma:.6f} vs 计算={calculated_sma:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_sma_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证SMA特性"""
        close_prices = data['hfq_close'].dropna()
        if len(close_prices) == 0:
            return False, "无有效价格数据"

        # 检查SMA的平滑特性
        for period in params['periods']:
            sma_col = f'SMA_{period}'
            if sma_col not in result.columns:
                continue

            sma_values = result[sma_col].dropna()
            if len(sma_values) < 5:
                continue

            # SMA应该比原始价格更平滑（波动性更小）
            price_volatility = close_prices.std() / close_prices.mean()
            sma_volatility = sma_values.std() / sma_values.mean()

            # SMA的波动性应该小于等于原始价格的波动性
            if sma_volatility > price_volatility * 1.2:  # 允许20%的误差
                return False, f"SMA_{period}波动性异常: SMA波动性={sma_volatility:.4f} > 价格波动性={price_volatility:.4f}"

            # 检查长期SMA是否比短期SMA更平滑
            if period > 10:  # 只对长期SMA检查
                short_sma_col = None
                for short_period in sorted(params['periods']):
                    if short_period < period:
                        short_sma_col = f'SMA_{short_period}'
                        break

                if short_sma_col and short_sma_col in result.columns:
                    short_sma_values = result[short_sma_col].dropna()
                    if len(short_sma_values) >= len(sma_values):
                        short_volatility = short_sma_values.tail(len(sma_values)).std()
                        long_volatility = sma_values.std()

                        if long_volatility > short_volatility * 1.1:  # 允许10%的误差
                            return False, f"长期SMA_{period}应比短期{short_sma_col}更平滑"

        return True, "SMA特性验证通过"

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

        # SMA特性验证
        if overall_success:
            is_valid, message = cls.validate_sma_properties(result, data, params)
            validation_results.append(("SMA特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results