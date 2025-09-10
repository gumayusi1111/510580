"""
HV - 历史波动率
Historical Volatility - 基于价格收益率的标准差计算波动率
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


class HV(BaseFactor):
    """历史波动率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化HV因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [20, 60]}
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
        向量化计算历史波动率
        HV = STD(日收益率) × √252 (年化)
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        close = data['hfq_close']
        # 计算日收益率
        returns = close.pct_change()
        
        # 计算各周期的历史波动率
        for period in self.params["periods"]:
            column_name = f'HV_{period}'
            
            # 修复逻辑：正确处理历史数据
            # 前period行应该为NaN，因为没有足够的历史数据
            hv_values = pd.Series(index=returns.index, dtype=float)
            
            # 从第period行开始计算（有足够历史数据的位置）
            for i in range(period, len(returns)):
                period_returns = returns.iloc[i-period+1:i+1]  # 取period个收益率
                if len(period_returns.dropna()) >= period:
                    vol_std = period_returns.std()
                    if pd.notna(vol_std):
                        # 年化波动率 (252个交易日)
                        hv_values.iloc[i] = vol_std * np.sqrt(252)
                    else:
                        hv_values.iloc[i] = pd.NA
                else:
                    hv_values.iloc[i] = pd.NA
            
            hv_values = hv_values.round(config.get_precision('percentage'))
            result[column_name] = hv_values
        
        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('HV_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            result[col] = config.validate_data_range(result[col], 'percentage')
            
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'HV',
            'description': '历史波动率 - 年化价格波动率',
            'category': 'volatility',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'historical_volatility',
            'formula': 'HV = STD(日收益率) × √252 × 100%',
            'output_columns': [f'HV_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'HV_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'HV_{period}'
                values = result[col_name].dropna()
                
                if len(values) == 0:
                    continue
                
                if (values < 0).any() or (values > 1000).any():
                    return False
            
            return True
        except Exception:
            return False


__all__ = ['HV']