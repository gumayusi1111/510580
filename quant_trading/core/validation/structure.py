"""
结构验证器 - 负责数据基本结构检查
"""

import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class StructureValidator:
    """数据结构验证器"""

    @staticmethod
    def validate_basic_structure(df: pd.DataFrame) -> Dict:
        """
        验证数据基本结构

        Args:
            df: 待验证的DataFrame

        Returns:
            验证结果字典
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }

        try:
            # 检查是否为空
            if df.empty:
                validation_result['is_valid'] = False
                validation_result['errors'].append("数据框为空")
                return validation_result

            # 检查必需列
            required_columns = ['ts_code', 'trade_date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"缺少必需列: {missing_columns}")

            # 检查日期列格式
            if 'trade_date' in df.columns:
                try:
                    pd.to_datetime(df['trade_date'])
                except Exception as e:
                    validation_result['errors'].append(f"日期格式错误: {e}")
                    validation_result['is_valid'] = False

            # 检查数据类型
            numeric_columns = df.select_dtypes(include=['number']).columns
            if len(numeric_columns) == 0:
                validation_result['warnings'].append("没有数值型列")

            # 统计信息
            validation_result['statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(numeric_columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"结构验证过程中发生错误: {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"验证过程异常: {str(e)}")

        return validation_result

    @staticmethod
    def check_column_types(df: pd.DataFrame, expected_types: Dict[str, str]) -> Dict:
        """
        检查列数据类型

        Args:
            df: 数据框
            expected_types: 期望的列类型映射

        Returns:
            类型检查结果
        """
        type_errors = []
        for column, expected_type in expected_types.items():
            if column in df.columns:
                actual_type = str(df[column].dtype)
                if expected_type not in actual_type:
                    type_errors.append(f"{column}: 期望{expected_type}，实际{actual_type}")

        return {
            'is_valid': len(type_errors) == 0,
            'type_errors': type_errors
        }