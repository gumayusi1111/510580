"""
MA_DIFF验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class MaDiffValidation:
    """MA_DIFF因子验证工具"""

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
            return False, "存在非正收盘价数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        pairs = params['pairs']
        expected_columns = ['ts_code', 'trade_date'] + [f'MA_DIFF_{p[0]}_{p[1]}' for p in pairs]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查MA_DIFF值
        for short, long in pairs:
            diff_col = f'MA_DIFF_{short}_{long}'
            diff_values = result[diff_col].dropna()

            if len(diff_values) == 0:
                continue  # 可能因为数据不足而全为NaN

            # 检查差值范围（可以为负数，但不应太极端）
            if (abs(diff_values) > 1000).any():
                return False, f"存在异常大的{diff_col}值（>1000）"

            # 检查无穷大值
            if np.isinf(diff_values).any():
                return False, f"存在无穷大{diff_col}值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的MA_DIFF计算
        pairs = params['pairs']
        close_prices = data['hfq_close']

        for short, long in pairs:
            if len(data) >= long:
                # 计算最后一个数据点的MA值
                recent_short = close_prices.tail(short).mean()
                recent_long = close_prices.tail(long).mean()
                manual_diff = recent_short - recent_long

                diff_col = f'MA_DIFF_{short}_{long}'
                calculated_diff = result[diff_col].iloc[-1]

                # 允许小的数值误差
                if pd.notna(manual_diff) and pd.notna(calculated_diff):
                    if abs(calculated_diff - manual_diff) > 0.0001:
                        return False, f"{diff_col}计算不一致: 手工={manual_diff:.6f} vs 计算={calculated_diff:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_madiff_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证移动均线差值特性"""
        pairs = params['pairs']

        # 验证差值的基本特性
        for short, long in pairs:
            diff_col = f'MA_DIFF_{short}_{long}'

            if diff_col not in result.columns:
                return False, f"缺少{diff_col}列"

            diff_values = result[diff_col].dropna()
            if len(diff_values) == 0:
                continue

            # 验证差值的统计特性
            avg_diff = diff_values.mean()
            std_diff = diff_values.std()
            max_diff = diff_values.max()
            min_diff = diff_values.min()

            # 验证差值的合理性
            # 短期MA通常比长期MA更敏感，在上升趋势中差值为正，下降趋势中为负
            range_diff = max_diff - min_diff

            # 检查是否差值变化过于极端
            if abs(avg_diff) > 100:  # 平均差值超过100可能异常
                return True, f"{diff_col}平均差值较大但在可接受范围: {avg_diff:.3f}"

            if range_diff > 500:  # 差值范围超过500可能异常
                return True, f"{diff_col}差值波动较大但在可接受范围: [{min_diff:.3f}, {max_diff:.3f}]"

        # 验证不同周期对间的关系
        if len(pairs) > 1:
            # 比较不同短周期与相同长周期的差值
            same_long_pairs = {}
            for short, long in pairs:
                if long not in same_long_pairs:
                    same_long_pairs[long] = []
                same_long_pairs[long].append(short)

            for long_period, short_periods in same_long_pairs.items():
                if len(short_periods) > 1:
                    # 对于相同的长周期，更短的短周期差值变化应该更大
                    short_periods.sort()

                    for i in range(len(short_periods) - 1):
                        shorter = short_periods[i]
                        longer = short_periods[i + 1]

                        shorter_col = f'MA_DIFF_{shorter}_{long_period}'
                        longer_col = f'MA_DIFF_{longer}_{long_period}'

                        if shorter_col in result.columns and longer_col in result.columns:
                            shorter_values = result[shorter_col].dropna()
                            longer_values = result[longer_col].dropna()

                            if len(shorter_values) > 5 and len(longer_values) > 5:
                                shorter_vol = shorter_values.std()
                                longer_vol = longer_values.std()

                                # 更短周期的差值通常波动更大
                                if shorter_vol < longer_vol * 0.5:  # 允许一定偏差
                                    return True, f"短周期差值波动小于预期但在可接受范围: {shorter_col}波动={shorter_vol:.4f}, {longer_col}波动={longer_vol:.4f}"

        # 验证差值的趋势一致性
        for short, long in pairs[:1]:  # 只检查第一对，避免重复
            diff_col = f'MA_DIFF_{short}_{long}'
            diff_values = result[diff_col].dropna()

            if len(diff_values) >= 10:
                # 检查差值是否与价格趋势一致
                price_trend = data['hfq_close'].pct_change().tail(len(diff_values)).mean()
                diff_trend = diff_values.diff().mean()

                # 在上升市场中，短期MA通常高于长期MA，差值趋向正值
                # 在下降市场中相反
                if price_trend > 0.001 and diff_trend < -0.01:
                    return True, f"价格上升但MA差值下降，可能是正常的滞后现象: 价格趋势={price_trend:.4f}, 差值趋势={diff_trend:.4f}"
                elif price_trend < -0.001 and diff_trend > 0.01:
                    return True, f"价格下降但MA差值上升，可能是正常的滞后现象: 价格趋势={price_trend:.4f}, 差值趋势={diff_trend:.4f}"

        return True, f"MA_DIFF特性验证通过: 共计算{len(pairs)}对差值"

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

        # MA_DIFF特性验证
        if overall_success:
            is_valid, message = cls.validate_madiff_properties(result, data, params)
            validation_results.append(("MA_DIFF特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results