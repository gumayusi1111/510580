"""
CCI验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class CciValidation:
    """CCI因子验证工具"""

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
        expected_columns = ['ts_code', 'trade_date', f'CCI_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查CCI值
        cci_col = f'CCI_{period}'
        cci_values = result[cci_col].dropna()

        if len(cci_values) == 0:
            return False, "所有CCI值为空"

        # 检查是否有无穷大值
        if np.isinf(cci_values).any():
            return False, "存在无穷大CCI值"

        # CCI值合理性检查（理论上可以无限，但实际应在合理范围）
        if (cci_values > 2000).any() or (cci_values < -2000).any():
            return False, "存在异常大的CCI值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 验证最后一个有效数据点的CCI计算
        period = params['period']

        if len(data) >= period:
            recent_data = data.tail(period)

            # 手工计算典型价格
            manual_tp = (recent_data['hfq_high'] + recent_data['hfq_low'] + recent_data['hfq_close']) / 3
            manual_ma = manual_tp.mean()
            manual_md = np.abs(manual_tp - manual_ma).mean()

            # 避免除零
            if manual_md > 0:
                current_tp = manual_tp.iloc[-1]
                manual_cci = (current_tp - manual_ma) / (0.015 * manual_md)

                cci_col = f'CCI_{period}'
                calculated_cci = result[cci_col].iloc[-1]

                # 允许小的数值误差（1.0）
                if abs(calculated_cci - manual_cci) > 1.0:
                    return False, f"计算不一致: 手工CCI={manual_cci:.4f} vs 计算CCI={calculated_cci:.4f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_cci_signals(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证CCI信号合理性"""
        period = params['period']
        cci_col = f'CCI_{period}'

        if cci_col not in result.columns:
            return False, f"缺少CCI列: {cci_col}"

        cci_values = result[cci_col].dropna()
        if len(cci_values) == 0:
            return False, "无有效CCI值"

        # 检查信号分布合理性
        # 大部分CCI值应该在±100之间（约2/3）
        normal_range = cci_values[(cci_values >= -100) & (cci_values <= 100)]
        ratio = len(normal_range) / len(cci_values)

        # 允许一定的偏差，至少40%在正常范围内
        if ratio < 0.4:
            return False, f"CCI正常范围值比例过低: {ratio:.2%}"

        return True, f"CCI信号合理性验证通过，正常范围比例: {ratio:.2%}"

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

        # CCI信号合理性验证
        if overall_success:
            is_valid, message = cls.validate_cci_signals(result, params)
            validation_results.append(("CCI信号验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results