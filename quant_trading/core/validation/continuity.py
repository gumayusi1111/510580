"""
连续性验证器 - 负责时间序列连续性检查
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ContinuityValidator:
    """时间序列连续性验证器"""

    @staticmethod
    def validate_time_series_continuity(df: pd.DataFrame,
                                      date_column: str = 'trade_date',
                                      max_gap_days: int = 7) -> Dict:
        """
        验证时间序列的连续性

        Args:
            df: 数据框
            date_column: 日期列名
            max_gap_days: 允许的最大间隔天数

        Returns:
            连续性验证结果
        """
        result = {
            'is_continuous': True,
            'total_gaps': 0,
            'max_gap_days': 0,
            'gap_details': [],
            'coverage_ratio': 0.0,
            'recommendations': []
        }

        try:
            if date_column not in df.columns:
                result['is_continuous'] = False
                result['recommendations'].append(f"缺少日期列: {date_column}")
                return result

            # 转换日期并排序
            df_sorted = df.copy()
            df_sorted[date_column] = pd.to_datetime(df_sorted[date_column])
            df_sorted = df_sorted.sort_values(date_column)

            dates = df_sorted[date_column]
            if len(dates) < 2:
                result['recommendations'].append("数据点太少，无法检查连续性")
                return result

            # 计算日期间隔
            date_diffs = dates.diff().dt.days.dropna()

            # 识别gap（周末和假期除外）
            business_day_gaps = []
            gap_details = []

            for i, gap in enumerate(date_diffs):
                if gap > max_gap_days:
                    start_date = dates.iloc[i]
                    end_date = dates.iloc[i + 1]
                    business_days = len(pd.bdate_range(start_date, end_date)) - 1

                    if business_days > max_gap_days:
                        business_day_gaps.append(business_days)
                        gap_details.append({
                            'start_date': start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'gap_days': int(gap),
                            'business_days': business_days
                        })

            # 更新结果
            result['total_gaps'] = len(gap_details)
            result['max_gap_days'] = max(business_day_gaps) if business_day_gaps else 0
            result['gap_details'] = gap_details
            result['is_continuous'] = len(gap_details) == 0

            # 计算覆盖率
            date_range = dates.max() - dates.min()
            expected_business_days = len(pd.bdate_range(dates.min(), dates.max()))
            actual_days = len(dates)
            result['coverage_ratio'] = actual_days / expected_business_days if expected_business_days > 0 else 0

            # 生成建议
            if not result['is_continuous']:
                result['recommendations'].append(f"发现{result['total_gaps']}个数据缺口")
                result['recommendations'].append(f"最大缺口: {result['max_gap_days']}个工作日")

            if result['coverage_ratio'] < 0.9:
                result['recommendations'].append(f"数据覆盖率较低: {result['coverage_ratio']:.1%}")

        except Exception as e:
            logger.error(f"连续性验证过程中发生错误: {e}")
            result['is_continuous'] = False
            result['recommendations'].append(f"验证过程异常: {str(e)}")

        return result

    @staticmethod
    def check_trading_calendar_alignment(df: pd.DataFrame,
                                       date_column: str = 'trade_date',
                                       market: str = 'SSE') -> Dict:
        """
        检查数据与交易日历的对齐情况

        Args:
            df: 数据框
            date_column: 日期列名
            market: 市场代码

        Returns:
            对齐检查结果
        """
        result = {
            'is_aligned': True,
            'missing_trading_days': [],
            'non_trading_days': [],
            'alignment_ratio': 0.0
        }

        try:
            dates = pd.to_datetime(df[date_column]).sort_values()
            if len(dates) == 0:
                return result

            # 生成期间的所有交易日（这里简化为工作日）
            expected_trading_days = pd.bdate_range(dates.min(), dates.max())
            actual_dates = set(dates.dt.date)
            expected_dates = set(expected_trading_days.date)

            # 找出缺失的交易日
            missing_days = expected_dates - actual_dates
            result['missing_trading_days'] = sorted(list(missing_days))

            # 找出非交易日数据
            non_trading = actual_dates - expected_dates
            result['non_trading_days'] = sorted(list(non_trading))

            # 计算对齐比例
            result['alignment_ratio'] = len(actual_dates & expected_dates) / len(expected_dates)
            result['is_aligned'] = len(missing_days) == 0 and len(non_trading) == 0

        except Exception as e:
            logger.error(f"交易日历对齐检查失败: {e}")
            result['is_aligned'] = False

        return result