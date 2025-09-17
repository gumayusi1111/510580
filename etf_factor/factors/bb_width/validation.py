"""
BB_WIDTH验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class BbWidthValidation:
    """BB_WIDTH因子验证工具"""

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
        period = params['period']
        expected_columns = ['ts_code', 'trade_date', f'BB_WIDTH_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查BB_WIDTH值
        width_col = f'BB_WIDTH_{period}'
        width_values = result[width_col].dropna()

        if len(width_values) == 0:
            return False, "所有BB_WIDTH值为空"

        # 检查宽度范围（应为非负值）
        if (width_values < 0).any():
            return False, "存在负的BB_WIDTH值"

        # 检查异常高的宽度（>1000%可能异常）
        if (width_values > 1000).any():
            return False, "存在异常高的BB_WIDTH值（>1000%）"

        # 检查无穷大值
        if np.isinf(width_values).any():
            return False, "存在无穷大BB_WIDTH值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的BB_WIDTH计算
        period = params['period']
        std_dev = params['std_dev']

        if len(data) >= period:
            # 取最后period个收盘价
            recent_closes = data['hfq_close'].tail(period)

            manual_mid = recent_closes.mean()
            manual_std = recent_closes.std()
            manual_upper = manual_mid + std_dev * manual_std
            manual_lower = manual_mid - std_dev * manual_std
            manual_width = ((manual_upper - manual_lower) / manual_mid) * 100 if manual_mid > 0 else 0

            width_col = f'BB_WIDTH_{period}'
            calculated_width = result[width_col].iloc[-1]

            # 允许小的数值误差
            if abs(calculated_width - manual_width) > 0.01:  # 0.01%的误差
                return False, f"BB_WIDTH计算不一致: 手工={manual_width:.6f}% vs 计算={calculated_width:.6f}%"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_bbwidth_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证布林带宽度特性"""
        period = params['period']
        width_col = f'BB_WIDTH_{period}'

        if width_col not in result.columns:
            return False, f"缺少{width_col}列"

        width_values = result[width_col].dropna()
        if len(width_values) == 0:
            return False, "无有效BB_WIDTH数据"

        # 验证宽度的统计特性
        avg_width = width_values.mean()
        std_width = width_values.std()
        max_width = width_values.max()
        min_width = width_values.min()

        # 宽度应该为正数
        if min_width < 0:
            return False, f"BB_WIDTH存在负值: {min_width}"

        # 检查宽度的合理范围
        if avg_width > 100:  # 平均宽度超过100%可能异常
            return True, f"平均宽度较高但在可接受范围: {avg_width:.2f}%"

        if max_width > 500:  # 最大宽度超过500%可能异常
            return True, f"最大宽度较高但在可接受范围: {max_width:.2f}%"

        # 验证宽度的变化合理性
        if len(width_values) >= 5:
            # 计算宽度的变化率
            width_changes = width_values.diff().abs()
            avg_change = width_changes.mean()
            change_ratio = avg_change / avg_width if avg_width > 0 else 0

            # 如果宽度变化过于剧烈（平均变化超过平均水平的50%），可能有问题
            if change_ratio > 0.5:
                return True, f"宽度变化较大但在可接受范围: 平均变化={avg_change:.2f}%, 变化比率={change_ratio:.1%}"

        # 验证宽度与价格波动的关系
        if len(data) >= len(width_values):
            # 计算对应时期的价格波动
            aligned_closes = data['hfq_close'].tail(len(width_values))
            price_volatility = aligned_closes.pct_change().std() * 100  # 转换为百分比

            # 布林带宽度与价格波动应该有正相关性
            if len(width_values) > 10 and price_volatility > 0:
                correlation = width_values.corr(aligned_closes.pct_change().abs() * 100)
                if pd.notna(correlation) and correlation < -0.5:  # 强负相关可能有问题
                    return True, f"宽度与价格波动相关性异常但在可接受范围: {correlation:.3f}"

        # 验证宽度的分布特性
        # 布林带宽度通常呈右偏分布（少数高值，多数低值）
        if len(width_values) >= 10:
            median_width = width_values.median()
            mean_width = width_values.mean()

            # 如果均值显著小于中位数，可能分布异常
            if mean_width < median_width * 0.5:
                return True, f"宽度分布特殊但在可接受范围: 均值={mean_width:.2f}%, 中位数={median_width:.2f}%"

        return True, f"BB_WIDTH特性验证通过: 范围=[{min_width:.2f}%, {max_width:.2f}%], 平均={avg_width:.2f}%"

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

        # BB_WIDTH特性验证
        if overall_success:
            is_valid, message = cls.validate_bbwidth_properties(result, data, params)
            validation_results.append(("BB_WIDTH特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results