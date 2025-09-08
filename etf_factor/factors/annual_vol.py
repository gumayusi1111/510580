"""
ANNUAL_VOL - 年化波动率
Annualized Volatility - 基于收益率标准差的年化波动率
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class ANNUAL_VOL(BaseFactor):
    """年化波动率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化ANNUAL_VOL因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [20,60]}
        """
        if params is None:
            periods = [20, 60]
        elif isinstance(params, dict):
            periods = params.get("periods", [20, 60])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [20, 60]
        
        super().__init__({"periods": periods})
        
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 1 for p in periods):
            raise ValueError("所有周期必须是大于1的正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算年化波动率
        ANNUAL_VOL = STD(日收益率) × √252 × 100%
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 计算日收益率
        close = data['hfq_close']
        daily_returns = close.pct_change()
        
        # 计算各周期的年化波动率
        for period in self.params["periods"]:
            column_name = f'ANNUAL_VOL_{period}'
            
            # 计算收益率的滚动标准差
            vol_std = daily_returns.rolling(window=period, min_periods=1).std()
            
            # 年化并转换为百分比
            annual_vol = vol_std * np.sqrt(252) * 100
            
            # 应用精度配置
            annual_vol = annual_vol.round(config.get_precision('percentage'))
            
            result[column_name] = annual_vol
        
        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('ANNUAL_VOL_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            result[col] = config.validate_data_range(result[col], 'percentage')
            
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'ANNUAL_VOL',
            'description': '年化波动率 - 基于收益率标准差的年化波动率',
            'category': 'return_risk',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'annualized_volatility',
            'formula': 'ANNUAL_VOL = STD(日收益率) × √252 × 100%',
            'output_columns': [f'ANNUAL_VOL_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'ANNUAL_VOL_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'ANNUAL_VOL_{period}'
                vol_values = result[col_name].dropna()
                
                if len(vol_values) == 0:
                    continue
                
                # 年化波动率应为正数且在合理范围内
                if (vol_values < 0).any() or (vol_values > 500).any():
                    return False
            
            return True
        except Exception:
            return False


__all__ = ['ANNUAL_VOL']