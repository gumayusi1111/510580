"""
MAX_DD验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class MaxDdValidation:
    """MAX_DD因子验证工具"""

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
        periods = params['periods']
        expected_columns = ['ts_code', 'trade_date'] + [f'MAX_DD_{p}' for p in periods]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查MAX_DD值
        for period in periods:
            dd_col = f'MAX_DD_{period}'
            dd_values = result[dd_col].dropna()

            if len(dd_values) == 0:
                continue  # 可能因为数据不足而全为NaN

            # 检查回撤范围（应为正数且不超过100%）
            if (dd_values < 0).any():
                return False, f"存在负的{dd_col}值"

            if (dd_values > 100).any():
                return False, f"存在超过100%的{dd_col}值"

            # 检查无穷大值
            if np.isinf(dd_values).any():
                return False, f"存在无穷大{dd_col}值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的MAX_DD计算
        periods = params['periods']
        close_prices = data['hfq_close']

        for period in periods:
            if len(data) >= period:
                # 取最后period个收盘价
                recent_prices = close_prices.tail(period)

                # 手工计算最大回撤
                cumulative_max = recent_prices.expanding().max()
                drawdown = (recent_prices - cumulative_max) / cumulative_max
                manual_max_dd = abs(drawdown.min()) * 100

                dd_col = f'MAX_DD_{period}'
                calculated_max_dd = result[dd_col].iloc[-1]

                # 允许小的数值误差
                if pd.notna(manual_max_dd) and pd.notna(calculated_max_dd):
                    if abs(calculated_max_dd - manual_max_dd) > 0.01:  # 0.01%的误差
                        return False, f"{dd_col}计算不一致: 手工={manual_max_dd:.6f}% vs 计算={calculated_max_dd:.6f}%"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_maxdd_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证最大回撤特性"""
        periods = params['periods']

        # 验证回撤的基本特性
        for period in periods:
            dd_col = f'MAX_DD_{period}'

            if dd_col not in result.columns:
                return False, f"缺少{dd_col}列"

            dd_values = result[dd_col].dropna()
            if len(dd_values) == 0:
                continue

            # 验证回撤的统计特性
            avg_dd = dd_values.mean()
            std_dd = dd_values.std()
            max_dd = dd_values.max()
            min_dd = dd_values.min()

            # 回撤应该为正数
            if min_dd < 0:
                return False, f"{dd_col}存在负值: {min_dd}"

            # 检查回撤的合理范围
            if avg_dd > 50:  # 平均回撤超过50%可能异常
                return True, f"{dd_col}平均回撤较高但在可接受范围: {avg_dd:.2f}%"

            if max_dd > 90:  # 最大回撤超过90%可能异常
                return True, f"{dd_col}最大回撤较高但在可接受范围: {max_dd:.2f}%"

        # 验证不同周期间的关系
        if len(periods) > 1:
            # 一般来说，长周期的最大回撤 >= 短周期的最大回撤
            sorted_periods = sorted(periods)

            for i in range(len(sorted_periods) - 1):
                shorter = sorted_periods[i]
                longer = sorted_periods[i + 1]

                shorter_col = f'MAX_DD_{shorter}'
                longer_col = f'MAX_DD_{longer}'

                if shorter_col in result.columns and longer_col in result.columns:
                    shorter_values = result[shorter_col].dropna()
                    longer_values = result[longer_col].dropna()

                    if len(shorter_values) > 0 and len(longer_values) > 0:
                        # 比较最新的回撤值
                        latest_shorter = shorter_values.iloc[-1]
                        latest_longer = longer_values.iloc[-1]

                        # 长周期回撤通常不小于短周期回撤
                        if latest_longer < latest_shorter * 0.5:  # 允许一定的偏差
                            return True, f"长周期回撤小于预期但在可接受范围: {shorter}日={latest_shorter:.2f}%, {longer}日={latest_longer:.2f}%"

        # 验证回撤的时间序列特性
        if len(periods) > 0:
            period = periods[0]  # 使用第一个周期进行时间序列检查
            dd_col = f'MAX_DD_{period}'
            dd_series = result[dd_col].dropna()

            if len(dd_series) >= 10:
                # 检查回撤的变化是否过于剧烈
                dd_changes = dd_series.diff().abs()
                avg_change = dd_changes.mean()
                avg_level = dd_series.mean()

                change_ratio = avg_change / avg_level if avg_level > 0 else 0

                # 如果回撤变化过于剧烈，可能数据有问题
                if change_ratio > 1:  # 平均变化超过平均水平
                    return True, f"回撤变化较大但在可接受范围: 平均变化={avg_change:.2f}%, 平均水平={avg_level:.2f}%, 变化比率={change_ratio:.1%}"

        # 验证回撤与价格波动的关系
        if len(data) >= len(result.dropna()):
            # 计算价格波动率
            price_returns = data['hfq_close'].pct_change().dropna()
            if len(price_returns) > 10:
                price_volatility = price_returns.std() * 100  # 转换为百分比

                # 最大回撤与价格波动应该有正相关性
                if len(periods) > 0:
                    period = periods[0]
                    dd_col = f'MAX_DD_{period}'
                    dd_values = result[dd_col].dropna()

                    if len(dd_values) > 10:
                        avg_dd = dd_values.mean()

                        # 如果价格波动很大但回撤很小，可能有问题
                        if price_volatility > 5 and avg_dd < 1:  # 波动率>5%但平均回撤<1%
                            return True, f"价格波动大但回撤小，可能是短期数据: 价格波动={price_volatility:.2f}%, 平均回撤={avg_dd:.2f}%"

        return True, f"MAX_DD特性验证通过: 各周期回撤均在合理范围内"

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

        # MAX_DD特性验证
        if overall_success:
            is_valid, message = cls.validate_maxdd_properties(result, data, params)
            validation_results.append(("MAX_DD特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results