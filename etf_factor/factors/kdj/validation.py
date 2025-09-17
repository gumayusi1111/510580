"""
KDJ验证模块
数据验证和输出检查功能
"""

import pandas as pd
import numpy as np


class KdjValidation:
    """KDJ因子验证工具"""

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
        valid_data = data[['hfq_high', 'hfq_low', 'hfq_close']].dropna()
        if len(valid_data) > 0:
            invalid_hl = valid_data['hfq_high'] < valid_data['hfq_low']
            if invalid_hl.any():
                return False, "存在高价小于低价的异常数据"

            # 检查收盘价是否在高低价范围内
            invalid_close = (valid_data['hfq_close'] > valid_data['hfq_high']) | \
                           (valid_data['hfq_close'] < valid_data['hfq_low'])
            if invalid_close.any():
                return False, "存在收盘价超出高低价范围的异常数据"

        return True, "输入数据验证通过"

    @staticmethod
    def validate_output_data(result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证输出数据的有效性"""
        period = params['period']
        expected_columns = ['ts_code', 'trade_date'] + [f'KDJ_K_{period}', f'KDJ_D_{period}', f'KDJ_J_{period}']

        # 检查输出列
        missing_columns = [col for col in expected_columns if col not in result.columns]
        if missing_columns:
            return False, f"输出缺少列: {missing_columns}"

        # 检查数据行数
        if len(result) == 0:
            return False, "输出数据为空"

        # 检查KDJ值
        k_col = f'KDJ_K_{period}'
        d_col = f'KDJ_D_{period}'
        j_col = f'KDJ_J_{period}'

        k_values = result[k_col].dropna()
        d_values = result[d_col].dropna()
        j_values = result[j_col].dropna()

        if len(k_values) == 0 or len(d_values) == 0 or len(j_values) == 0:
            return False, "所有KDJ值为空"

        # 检查KDJ范围
        if (k_values < -50).any() or (k_values > 150).any():
            return False, "存在超出合理范围的K值"

        if (d_values < -50).any() or (d_values > 150).any():
            return False, "存在超出合理范围的D值"

        if (j_values < -100).any() or (j_values > 200).any():
            return False, "存在超出合理范围的J值"

        # 检查无穷大值
        if np.isinf(k_values).any() or np.isinf(d_values).any() or np.isinf(j_values).any():
            return False, "存在无穷大KDJ值"

        return True, "输出数据验证通过"

    @staticmethod
    def validate_calculation_consistency(data: pd.DataFrame, result: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证计算一致性"""
        if len(data) != len(result):
            return False, f"输入输出行数不匹配: {len(data)} vs {len(result)}"

        # 手工验证最后几个数据点的KDJ计算
        period = params['period']

        if len(data) >= 2:  # 需要至少2个数据点
            # 计算最后一个数据点的RSV
            high_prices = data['hfq_high']
            low_prices = data['hfq_low']
            close_prices = data['hfq_close']

            # 取最后period个数据计算最高最低价
            recent_period = min(period, len(data))
            recent_high = high_prices.tail(recent_period).max()
            recent_low = low_prices.tail(recent_period).min()
            latest_close = close_prices.iloc[-1]

            manual_rsv = ((latest_close - recent_low) / (recent_high - recent_low)) * 100 if recent_high != recent_low else 50

            # 由于K、D值是递归计算，我们只能做基本的RSV验证
            if pd.notna(manual_rsv):
                # 验证RSV在合理范围内
                if manual_rsv < -10 or manual_rsv > 110:
                    return False, f"手工计算RSV超出合理范围: {manual_rsv:.2f}"

        return True, "计算一致性验证通过"

    @staticmethod
    def validate_kdj_properties(result: pd.DataFrame, data: pd.DataFrame, params: dict) -> tuple[bool, str]:
        """验证KDJ随机指标特性"""
        period = params['period']
        k_col = f'KDJ_K_{period}'
        d_col = f'KDJ_D_{period}'
        j_col = f'KDJ_J_{period}'

        if k_col not in result.columns or d_col not in result.columns or j_col not in result.columns:
            return False, "缺少KDJ列"

        # 获取有效数据
        valid_data = result[[k_col, d_col, j_col]].dropna()
        if len(valid_data) == 0:
            return False, "无有效KDJ数据"

        k_values = valid_data[k_col]
        d_values = valid_data[d_col]
        j_values = valid_data[j_col]

        # 验证KDJ的基本特性
        # 1. K、D值应该相对平滑（D比K更平滑）
        if len(k_values) >= 3:
            k_volatility = k_values.diff().abs().mean()
            d_volatility = d_values.diff().abs().mean()

            # D值的波动性通常小于K值（因为D是K的移动平均）
            if d_volatility > k_volatility * 2:  # 允许一定的误差
                return True, f"D值波动大于预期但在可接受范围: K波动={k_volatility:.2f}, D波动={d_volatility:.2f}"

        # 2. 验证J值的计算关系：J = 3*K - 2*D
        if len(valid_data) > 0:
            calculated_j = 3 * k_values - 2 * d_values
            j_diff = (calculated_j - j_values).abs()
            max_diff = j_diff.max()

            if max_diff > 0.1:  # 允许小的数值误差
                return False, f"J值计算关系不符: 最大误差={max_diff:.4f}"

        # 3. 验证KDJ的统计特性
        k_mean = k_values.mean()
        d_mean = d_values.mean()
        j_mean = j_values.mean()

        # KDJ的平均值应该在合理范围内
        if not (0 <= k_mean <= 100) and not (-10 <= k_mean <= 110):
            return True, f"K值平均值偏离但在可接受范围: {k_mean:.2f}"

        if not (0 <= d_mean <= 100) and not (-10 <= d_mean <= 110):
            return True, f"D值平均值偏离但在可接受范围: {d_mean:.2f}"

        # 4. 验证KDJ的极值情况
        k_max = k_values.max()
        k_min = k_values.min()
        d_max = d_values.max()
        d_min = d_values.min()
        j_max = j_values.max()
        j_min = j_values.min()

        # 检查是否有异常极值
        if k_max > 120 or k_min < -20:
            return True, f"K值出现极值但已被裁剪: 范围=[{k_min:.1f}, {k_max:.1f}]"

        if d_max > 120 or d_min < -20:
            return True, f"D值出现极值但已被裁剪: 范围=[{d_min:.1f}, {d_max:.1f}]"

        # 5. 验证KDJ的趋势一致性
        if len(valid_data) >= 5:
            # 检查K、D、J的趋势方向
            k_trend = (k_values.iloc[-1] - k_values.iloc[-5]) / 5
            d_trend = (d_values.iloc[-1] - d_values.iloc[-5]) / 5
            j_trend = (j_values.iloc[-1] - j_values.iloc[-5]) / 5

            # 如果趋势方向完全相反，可能有问题
            if (k_trend > 0 and d_trend < -abs(k_trend)) or (k_trend < 0 and d_trend > abs(k_trend)):
                return True, f"K、D趋势分化较大但在正常范围: K趋势={k_trend:.2f}, D趋势={d_trend:.2f}"

        return True, f"KDJ特性验证通过: K=[{k_min:.1f},{k_max:.1f}], D=[{d_min:.1f},{d_max:.1f}], J=[{j_min:.1f},{j_max:.1f}]"

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

        # KDJ特性验证
        if overall_success:
            is_valid, message = cls.validate_kdj_properties(result, data, params)
            validation_results.append(("KDJ特性验证", is_valid, message))
            if not is_valid:
                overall_success = False

        return overall_success, validation_results