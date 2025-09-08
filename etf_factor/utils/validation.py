"""
Data Validation Utils - 数据验证工具
基于全局配置的数据验证函数
文件限制: <200行
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import sys
sys.path.append('..')
from src.config import config


def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, List[str]]:
    """
    验证DataFrame基本要求
    Args:
        df: 待验证的DataFrame
        required_columns: 必需的列
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    if df.empty:
        errors.append("DataFrame为空")
        return False, errors
    
    # 检查必需列
    required_columns = required_columns or ['ts_code', 'trade_date']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"缺少必需列: {missing_cols}")
    
    # 检查数据类型
    if 'trade_date' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['trade_date']):
            try:
                pd.to_datetime(df['trade_date'])
            except:
                errors.append("trade_date列格式不正确")
    
    # 检查缺失值比例
    max_missing_ratio = config.get('validation.max_missing_ratio', 0.1)
    for col in df.columns:
        if col in ['ts_code', 'trade_date']:
            continue
        missing_ratio = df[col].isna().mean()
        if missing_ratio > max_missing_ratio:
            errors.append(f"列{col}缺失值比例过高: {missing_ratio:.2%}")
    
    return len(errors) == 0, errors


def validate_price_data(prices: pd.Series, column_name: str = "") -> pd.Series:
    """验证价格数据范围"""
    return config.validate_data_range(prices, 'price')


def validate_volume_data(volumes: pd.Series, column_name: str = "") -> pd.Series:
    """验证成交量数据范围"""
    return config.validate_data_range(volumes, 'volume')


def validate_percentage_data(percentages: pd.Series, column_name: str = "") -> pd.Series:
    """验证百分比数据范围"""
    return config.validate_data_range(percentages, 'percentage')


def check_data_continuity(df: pd.DataFrame, date_column: str = 'trade_date') -> Dict[str, any]:
    """
    检查数据连续性
    Args:
        df: 数据DataFrame
        date_column: 日期列名
    Returns:
        检查结果字典
    """
    if date_column not in df.columns:
        return {"error": f"日期列{date_column}不存在"}
    
    dates = pd.to_datetime(df[date_column]).sort_values()
    
    # 计算日期间隔
    date_diffs = dates.diff().dropna()
    
    # 工作日检查 (跳过周末)
    expected_diff = pd.Timedelta(days=1)
    large_gaps = date_diffs[date_diffs > pd.Timedelta(days=7)]  # 超过一周的间隔
    
    return {
        "total_records": len(df),
        "date_range": {
            "start": str(dates.iloc[0].date()),
            "end": str(dates.iloc[-1].date())
        },
        "large_gaps": len(large_gaps),
        "gap_details": [(str(dates[dates.diff() == gap].iloc[0].date()), gap.days) 
                       for gap in large_gaps] if len(large_gaps) > 0 else []
    }


def detect_outliers(series: pd.Series, method: str = "iqr", threshold: float = 1.5) -> pd.Series:
    """
    检测异常值
    Args:
        series: 数据序列
        method: 检测方法 ('iqr', 'zscore')
        threshold: 阈值
    Returns:
        布尔序列，True表示异常值
    """
    if series.empty or series.isna().all():
        return pd.Series(False, index=series.index)
    
    if method == "iqr":
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    elif method == "zscore":
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold
    
    else:
        raise ValueError(f"不支持的异常值检测方法: {method}")


def clean_factor_data(df: pd.DataFrame, factor_columns: List[str] = None) -> pd.DataFrame:
    """
    清理因子数据
    Args:
        df: 因子数据
        factor_columns: 因子列名列表
    Returns:
        清理后的数据
    """
    cleaned_df = df.copy()
    
    if factor_columns is None:
        factor_columns = [col for col in df.columns 
                         if col not in ['ts_code', 'trade_date']]
    
    for col in factor_columns:
        if col not in cleaned_df.columns:
            continue
        
        # 推断数据类型并验证范围
        data_type = _infer_validation_type(col)
        if data_type in ['price', 'volume', 'percentage']:
            cleaned_df[col] = config.validate_data_range(cleaned_df[col], data_type)
        
        # 处理无穷值
        cleaned_df[col] = cleaned_df[col].replace([np.inf, -np.inf], pd.NA)
        
        # 应用全局精度
        if pd.api.types.is_numeric_dtype(cleaned_df[col]):
            data_type_for_precision = config._infer_data_type(col)
            precision = config.get_precision(data_type_for_precision)
            cleaned_df[col] = cleaned_df[col].round(precision)
    
    return cleaned_df


def _infer_validation_type(column_name: str) -> str:
    """推断验证数据类型"""
    col_lower = column_name.lower()
    
    if any(x in col_lower for x in ['price', 'open', 'high', 'low', 'close', 'sma', 'ema', 'wma']):
        return 'price'
    elif any(x in col_lower for x in ['vol', 'amount']):
        return 'volume'  
    elif any(x in col_lower for x in ['pct', 'return', 'chg']):
        return 'percentage'
    else:
        return 'indicator'


def generate_data_quality_report(df: pd.DataFrame) -> Dict[str, any]:
    """
    生成数据质量报告
    Args:
        df: 数据DataFrame
    Returns:
        质量报告字典
    """
    report = {
        "basic_info": {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024**2)
        },
        "missing_data": {},
        "data_types": {},
        "outliers": {},
        "continuity": {}
    }
    
    # 缺失值统计
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_ratio = missing_count / len(df)
        report["missing_data"][col] = {
            "count": int(missing_count),
            "ratio": round(missing_ratio, 4)
        }
    
    # 数据类型统计
    for col in df.columns:
        report["data_types"][col] = str(df[col].dtype)
    
    # 异常值检测 (仅数值列)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        outliers = detect_outliers(df[col])
        report["outliers"][col] = int(outliers.sum())
    
    # 连续性检查
    if 'trade_date' in df.columns:
        report["continuity"] = check_data_continuity(df)
    
    return report