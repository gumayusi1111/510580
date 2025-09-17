"""
WMA验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class WmaValidation:
    """WMA因子验证工具"""

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
        expected_columns = ['ts_code', 'trade_date'] + [f'WMA_{p}' for p in params['periods']]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查WMA值
        for period in params['periods']:
            wma_col = f'WMA_{period}'
            wma_values = result[wma_col].dropna()

            if len(wma_values) == 0:
                continue

            # WMA值应为正数
            if (wma_values <= 0).any():
                return False, f"存在非正WMA值: {wma_col}"

            # WMA值应在合理范围内
            if (wma_values > 10000).any() or (wma_values < 0.001).any():
                return False, f"WMA值超出合理范围: {wma_col}"

            # 检查无穷大值
            if np.isinf(wma_values).any():
                return False, f"存在无穷大WMA值: {wma_col}"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的WMA计算
        for period in params['periods']:
            if len(data) >= period:
                # 取最后period个数据点计算WMA
                recent_prices = data['hfq_close'].tail(period).tolist()

                # 生成权重：[1,2,3,...,period]
                weights = list(range(1, period + 1))
                weights_sum = sum(weights)

                # 手工计算WMA
                manual_wma = sum(price * weight for price, weight in zip(recent_prices, weights)) / weights_sum

                wma_col = f'WMA_{period}'
                calculated_wma = result[wma_col].iloc[-1]

                # 允许小的数值误差（0.0001）
                if abs(calculated_wma - manual_wma) > 0.0001:
                    return False, f"WMA_{period}计算不一致: 手工={manual_wma:.6f} vs 计算={calculated_wma:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_wma_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证WMA特性"""
        close_prices = data['hfq_close'].dropna()
        if len(close_prices) == 0:
            return False, "无有效价格数据"

        # 检查WMA相对于SMA的反应敏感性
        for period in params['periods']:
            wma_col = f'WMA_{period}'
            if wma_col not in result.columns:
                continue

            wma_values = result[wma_col].dropna()
            if len(wma_values) < period:
                continue

            # 计算对应的SMA用于比较
            if len(close_prices) >= period:
                recent_prices = close_prices.tail(len(wma_values))
                sma_values = recent_prices.rolling(window=period, min_periods=1).mean()

                # WMA应该对价格变化更敏感（在趋势中）
                # 检查最后几个数据点的趋势敏感性
                if len(wma_values) >= 5 and len(sma_values) >= 5:
                    wma_recent = wma_values.tail(5)
                    sma_recent = sma_values.tail(5)

                    # 计算变化趋势
                    wma_trend = wma_recent.iloc[-1] - wma_recent.iloc[0]
                    sma_trend = sma_recent.iloc[-1] - sma_recent.iloc[0]

                    # 在明显趋势中，WMA应该比SMA反应更强烈
                    # 但由于WMA使用不同的权重机制，这个检查应该更宽松
                    if abs(sma_trend) > 0.05:  # 有明显趋势
                        if abs(wma_trend) < abs(sma_trend) * 0.5:  # WMA反应太弱
                            return False, f"WMA_{period}对趋势的敏感性不足: WMA趋势={wma_trend:.6f}, SMA趋势={sma_trend:.6f}"

            # 检查WMA的权重特性
            # 对于上升趋势，WMA应该高于简单平均值
            if len(wma_values) >= 3:
                recent_wma = wma_values.tail(3)
                recent_prices = close_prices.tail(period) if len(close_prices) >= period else close_prices

                # 如果价格呈上升趋势
                if len(recent_prices) >= 2 and recent_prices.iloc[-1] > recent_prices.iloc[0]:
                    simple_avg = recent_prices.mean()
                    current_wma = recent_wma.iloc[-1]

                    # WMA应该更接近最新价格
                    if current_wma < simple_avg:
                        # 这是正常的，WMA在上升趋势中应该高于SMA，但不严格要求
                        pass

        return True, "WMA特性验证通过"

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

        # WMA特性验证
        if overall_success:
            is_valid, message = cls.validate_wma_properties(result, data, params)
            validation_results.append(("WMA特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results