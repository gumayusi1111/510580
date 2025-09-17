"""
OBV验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class ObvValidation:
    """OBV因子验证工具"""

    @staticmethod
    def validate_input_data(data: pd.DataFrame) -> tuple[bool, str]:
        """验证输入数据的有效性"""
        required_columns = ['ts_code', 'trade_date', 'hfq_close', 'vol']

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

        # 检查成交量数据
        volumes = data['vol']
        if volumes.isnull().all():
            return False, "所有成交量数据为空"

        # 检查成交量是否为非负数
        valid_volumes = volumes.dropna()
        if len(valid_volumes) > 0 and (valid_volumes < 0).any():
            return False, "存在负成交量数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        expected_columns = ['ts_code', 'trade_date', 'OBV']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查OBV值
        obv_values = result['OBV'].dropna()

        if len(obv_values) == 0:
            return False, "所有OBV值为空"

        # 检查无穷大值
        if np.isinf(obv_values).any():
            return False, "存在无穷大OBV值"

        # OBV是累计值，检查连续性
        if len(obv_values) > 1:
            # OBV应该是连续变化的，不应该有突然的巨大跳跃
            obv_diff = obv_values.diff().abs()
            obv_median = obv_values.abs().median()

            # 如果有差异超过中位数的100倍，可能有异常
            if obv_median > 0 and (obv_diff > obv_median * 100).any():
                return False, "OBV值存在异常跳跃"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证前几个数据点的OBV计算
        if len(data) >= 3:
            close = data['hfq_close'].iloc[:3]
            volume = data['vol'].iloc[:3]

            # 手工计算前3个点的OBV
            manual_obv = [0]  # 第一个点OBV为0（没有前一日价格）

            for i in range(1, len(close)):
                price_change = close.iloc[i] - close.iloc[i-1]
                if price_change > 0:
                    direction = 1
                elif price_change < 0:
                    direction = -1
                else:
                    direction = 0

                manual_obv.append(manual_obv[-1] + direction * volume.iloc[i])

            # 比较计算结果
            calculated_obv = result['OBV'].iloc[:3].tolist()

            for i, (manual, calculated) in enumerate(zip(manual_obv, calculated_obv)):
                if pd.isna(calculated):
                    continue
                if abs(manual - calculated) > 1e-6:  # 允许小的数值误差
                    return False, f"第{i}个点计算不一致: 手工={manual} vs 计算={calculated}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_obv_signals(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证OBV信号合理性"""
        if 'OBV' not in result.columns:
            return False, "缺少OBV列"

        obv_values = result['OBV'].dropna()
        if len(obv_values) == 0:
            return False, "无有效OBV值"

        close_prices = data['hfq_close'].dropna()
        if len(close_prices) == 0:
            return False, "无有效价格数据"

        # 检查OBV与价格趋势的一致性（简单检查）
        if len(obv_values) > 10 and len(close_prices) > 10:
            # 取最后10个数据点
            recent_obv = obv_values.tail(10)
            recent_price = close_prices.tail(10)

            # 计算趋势（简单的起止点比较）
            obv_trend = recent_obv.iloc[-1] - recent_obv.iloc[0]
            price_trend = recent_price.iloc[-1] - recent_price.iloc[0]

            # OBV与价格应该大致同向（这不是绝对的，但作为基本检查）
            # 如果两者方向完全相反且幅度都很大，可能有问题
            if obv_trend * price_trend < 0:  # 方向相反
                obv_ratio = abs(obv_trend) / abs(recent_obv.mean()) if abs(recent_obv.mean()) > 0 else 0
                price_ratio = abs(price_trend) / abs(recent_price.mean()) if abs(recent_price.mean()) > 0 else 0

                # 如果两者都有显著变化但方向相反，给出警告但不失败
                if obv_ratio > 0.1 and price_ratio > 0.1:
                    return True, f"OBV与价格趋势方向相反，需要进一步分析: OBV趋势={obv_trend:.0f}, 价格趋势={price_trend:.4f}"

        return True, "OBV信号合理性验证通过"

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

        # OBV信号合理性验证
        if overall_success:
            is_valid, message = cls.validate_obv_signals(result, data, params)
            validation_results.append(("OBV信号验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results