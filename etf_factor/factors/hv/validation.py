"""
HV验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class HvValidation:
    """HV因子验证工具"""

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

        # 检查是否有足够的数据计算收益率
        if len(valid_prices) < 2:
            return False, "数据点不足，无法计算收益率"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        periods = params['periods']
        expected_columns = ['ts_code', 'trade_date'] + [f'HV_{p}' for p in periods]

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查HV值
        for period in periods:
            hv_col = f'HV_{period}'
            hv_values = result[hv_col].dropna()

            if len(hv_values) == 0:
                continue  # 可能因为数据不足而全为NaN

            # 检查HV范围（应为非负值）
            if (hv_values < 0).any():
                return False, f"存在负的HV_{period}值"

            # 检查异常高的波动率（>1000%可能异常）
            if (hv_values > 1000).any():
                return False, f"存在异常高的HV_{period}值（>1000%）"

            # 检查无穷大值
            if np.isinf(hv_values).any():
                return False, f"存在无穷大HV_{period}值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的HV计算
        periods = params['periods']

        # 计算收益率
        close_prices = data['hfq_close']
        returns = close_prices.pct_change()

        for period in periods:
            if len(data) >= period + 1:  # 需要至少period+1个数据点
                # 取最后period个收益率（不包括第一个NaN）
                recent_returns = returns.tail(period + 1).iloc[1:]  # 去掉第一个NaN

                if len(recent_returns.dropna()) >= period:
                    manual_std = recent_returns.std()
                    manual_hv = manual_std * np.sqrt(252) if pd.notna(manual_std) else np.nan

                    hv_col = f'HV_{period}'
                    calculated_hv = result[hv_col].iloc[-1]

                    # 允许小的数值误差
                    if pd.notna(manual_hv) and pd.notna(calculated_hv):
                        relative_error = abs(calculated_hv - manual_hv) / max(manual_hv, 0.001)
                        if relative_error > 0.01:  # 1%的相对误差
                            return False, f"HV_{period}计算不一致: 手工={manual_hv:.6f} vs 计算={calculated_hv:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_hv_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证历史波动率特性"""
        periods = params['periods']

        # 验证波动率的一般特性
        for period in periods:
            hv_col = f'HV_{period}'
            if hv_col not in result.columns:
                return False, f"缺少HV_{period}列"

            hv_values = result[hv_col].dropna()
            if len(hv_values) == 0:
                continue

            # 计算波动率统计特征
            avg_hv = hv_values.mean()
            std_hv = hv_values.std()
            max_hv = hv_values.max()
            min_hv = hv_values.min()

            # 波动率应该为正数
            if min_hv < 0:
                return False, f"HV_{period}存在负值: {min_hv}"

            # 检查波动率的合理范围（年化）
            if avg_hv > 200:  # 平均年化波动率超过200%可能异常
                return False, f"HV_{period}平均值过高: {avg_hv:.2f}%"

            if max_hv > 500:  # 最大年化波动率超过500%可能异常
                return False, f"HV_{period}最大值过高: {max_hv:.2f}%"

        # 验证不同周期间的关系
        if len(periods) > 1:
            # 获取最后一个有效数据点进行比较
            hv_latest = {}
            for period in periods:
                hv_col = f'HV_{period}'
                hv_series = result[hv_col].dropna()
                if len(hv_series) > 0:
                    hv_latest[period] = hv_series.iloc[-1]

            if len(hv_latest) > 1:
                # 一般情况下，短期波动率可能比长期波动率有更大的变化范围
                # 但这不是绝对规律，所以只做温和的检查
                max_period = max(hv_latest.keys())
                min_period = min(hv_latest.keys())

                if max_period != min_period:
                    ratio = hv_latest[max_period] / hv_latest[min_period] if hv_latest[min_period] > 0 else 1
                    # 如果长短期波动率差异过大（超过10倍），可能有问题
                    if ratio > 10 or ratio < 0.1:
                        return True, f"不同周期波动率差异较大但在可接受范围: HV_{min_period}={hv_latest[min_period]:.2f}%, HV_{max_period}={hv_latest[max_period]:.2f}%"

        # 验证波动率的时间序列特性
        if len(periods) > 0:
            period = periods[0]  # 使用第一个周期进行时间序列检查
            hv_col = f'HV_{period}'
            hv_series = result[hv_col].dropna()

            if len(hv_series) >= 5:
                # 检查波动率的变化是否过于剧烈
                hv_changes = hv_series.diff().abs()
                avg_change = hv_changes.mean()
                avg_level = hv_series.mean()

                change_ratio = avg_change / avg_level if avg_level > 0 else 0

                # 如果平均变化幅度超过平均水平的50%，可能数据有问题
                if change_ratio > 0.5:
                    return True, f"波动率变化较大但在可接受范围: 平均变化={avg_change:.2f}%, 平均水平={avg_level:.2f}%, 变化比率={change_ratio:.1%}"

        return True, f"HV特性验证通过: 各周期波动率均在合理范围内"

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

        # HV特性验证
        if overall_success:
            is_valid, message = cls.validate_hv_properties(result, data, params)
            validation_results.append(("HV特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results