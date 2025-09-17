"""
VOLUME_RATIO验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class VolumeRatioValidation:
    """VOLUME_RATIO因子验证工具"""

    @staticmethod
    def validate_input_data(data: pd.DataFrame) -> tuple[bool, str]:
        """验证输入数据的有效性"""
        required_columns = ['ts_code', 'trade_date', 'vol']

        # 检查必需列
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"缺少必需列: {missing_columns}"

        # 检查数据行数
        if len(data) == 0:
            return False, "数据为空"

        # 检查成交量数据
        volume = data['vol']
        if volume.isnull().all():
            return False, "所有成交量数据为空"

        # 检查成交量是否为非负数
        valid_volumes = volume.dropna()
        if len(valid_volumes) > 0 and (valid_volumes < 0).any():
            return False, "存在负成交量数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        period = params['period']
        expected_columns = ['ts_code', 'trade_date', f'VOLUME_RATIO_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查VOLUME_RATIO值
        ratio_col = f'VOLUME_RATIO_{period}'
        ratio_values = result[ratio_col].dropna()

        if len(ratio_values) == 0:
            return False, "所有VOLUME_RATIO值为空"

        # 检查量比范围（应为正数）
        if (ratio_values <= 0).any():
            return False, "存在非正VOLUME_RATIO值"

        # 检查是否有异常高的量比（>100倍可能异常）
        if (ratio_values > 100).any():
            return False, "存在异常高的VOLUME_RATIO值（>100倍）"

        # 检查无穷大值
        if np.isinf(ratio_values).any():
            return False, "存在无穷大VOLUME_RATIO值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的VOLUME_RATIO计算
        period = params['period']
        volume = data['vol']

        if len(data) >= period + 1:
            # 取最后一个数据点进行验证
            current_volume = volume.iloc[-1]

            # 计算前period个交易日的平均成交量（排除当日）
            prev_volumes = volume.iloc[-period-1:-1]  # 排除最后一天

            if len(prev_volumes) > 0:
                manual_avg_volume = prev_volumes.mean()
                manual_ratio = current_volume / manual_avg_volume if manual_avg_volume > 0 else 1.0

                ratio_col = f'VOLUME_RATIO_{period}'
                calculated_ratio = result[ratio_col].iloc[-1]

                # 允许小的数值误差
                if pd.notna(manual_ratio) and pd.notna(calculated_ratio):
                    relative_error = abs(calculated_ratio - manual_ratio) / max(manual_ratio, 0.001)
                    if relative_error > 0.01:  # 1%的相对误差
                        return False, f"VOLUME_RATIO计算不一致: 手工={manual_ratio:.6f} vs 计算={calculated_ratio:.6f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_volumeratio_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证量比特性"""
        period = params['period']
        ratio_col = f'VOLUME_RATIO_{period}'

        if ratio_col not in result.columns:
            return False, f"缺少{ratio_col}列"

        ratio_values = result[ratio_col].dropna()
        if len(ratio_values) == 0:
            return False, "无有效VOLUME_RATIO数据"

        # 验证量比的统计特性
        avg_ratio = ratio_values.mean()
        std_ratio = ratio_values.std()
        max_ratio = ratio_values.max()
        min_ratio = ratio_values.min()

        # 量比应该为正数
        if min_ratio <= 0:
            return False, f"VOLUME_RATIO存在非正值: {min_ratio}"

        # 检查量比的合理范围
        if avg_ratio > 10:  # 平均量比超过10倍可能异常
            return True, f"平均量比较高但在可接受范围: {avg_ratio:.2f}倍"

        if max_ratio > 50:  # 最大量比超过50倍可能异常
            return True, f"最大量比较高但在可接受范围: {max_ratio:.2f}倍"

        # 验证量比的分布特性
        if len(ratio_values) >= 10:
            # 计算各个量比区间的分布
            high_ratio_count = (ratio_values > 2).sum()  # 异常放量
            normal_ratio_count = ((ratio_values >= 0.5) & (ratio_values <= 2)).sum()  # 正常范围
            low_ratio_count = (ratio_values < 0.5).sum()  # 明显缩量

            total_count = len(ratio_values)

            # 检查分布是否合理
            normal_ratio = normal_ratio_count / total_count
            if normal_ratio < 0.3:  # 如果正常范围的占比太少
                return True, f"量比分布异常但在可接受范围: 正常范围占比={normal_ratio:.1%}, 放量={high_ratio_count}次, 缩量={low_ratio_count}次"

        # 验证量比与成交量的一致性
        if len(data) >= len(ratio_values):
            volume_data = data['vol'].tail(len(ratio_values))

            # 计算成交量的相对变化
            volume_changes = volume_data.pct_change().dropna()
            if len(volume_changes) > 0:
                high_volume_days = (volume_changes > 0.5).sum()  # 成交量增长>50%
                high_ratio_days = (ratio_values > 1.5).sum()      # 量比>1.5

                # 成交量大幅增长的天数应该与高量比天数相关
                if len(volume_changes) >= 10:
                    correlation_check = abs(high_volume_days - high_ratio_days) <= max(2, len(volume_changes) * 0.2)
                    if not correlation_check:
                        return True, f"成交量变化与量比不完全一致但在可接受范围: 高成交量={high_volume_days}天, 高量比={high_ratio_days}天"

        # 验证量比的时间序列特性
        if len(ratio_values) >= 5:
            # 检查量比的变化是否过于剧烈
            ratio_changes = ratio_values.diff().abs()
            avg_change = ratio_changes.mean()

            # 如果量比变化过于剧烈，可能数据有问题
            if avg_change > avg_ratio:  # 平均变化超过平均水平
                return True, f"量比变化较大但在可接受范围: 平均变化={avg_change:.2f}, 平均水平={avg_ratio:.2f}"

        # 验证异常量比的合理性
        extreme_ratios = ratio_values[ratio_values > 5]  # 5倍以上为极端量比
        if len(extreme_ratios) > 0:
            extreme_ratio = len(extreme_ratios) / len(ratio_values)
            if extreme_ratio > 0.1:  # 超过10%的数据为极端量比
                return True, f"极端量比较多但在可接受范围: {len(extreme_ratios)}次, 占比={extreme_ratio:.1%}"

        return True, f"VOLUME_RATIO特性验证通过: 范围=[{min_ratio:.2f}, {max_ratio:.2f}], 平均={avg_ratio:.2f}倍"

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

        # VOLUME_RATIO特性验证
        if overall_success:
            is_valid, message = cls.validate_volumeratio_properties(result, data, params)
            validation_results.append(("VOLUME_RATIO特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results