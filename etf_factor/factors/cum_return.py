"""
CUM_RETURN - 累计收益率
Cumulative Return - 指定周期内的累计收益率
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class CUM_RETURN(BaseFactor):
    """累计收益率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化CUM_RETURN因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,20,60]}
        """
        if params is None:
            periods = [5, 20, 60]
        elif isinstance(params, dict):
            periods = params.get("periods", [5, 20, 60])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [5, 20, 60]
        
        super().__init__({"periods": periods})
        
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("所有周期必须是正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算累计收益率
        CUM_RETURN = (今日价格 - N日前价格) / N日前价格 × 100%
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价
        close = data['hfq_close']
        
        # 计算各周期的累计收益率
        for period in self.params["periods"]:
            column_name = f'CUM_RETURN_{period}'
            
            # 获取N日前的价格
            prev_close = close.shift(period)
            
            # 计算累计收益率
            cum_return = ((close - prev_close) / prev_close) * 100
            
            # 应用精度配置
            cum_return = cum_return.round(config.get_precision('percentage'))
            
            result[column_name] = cum_return
        
        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('CUM_RETURN_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            result[col] = config.validate_data_range(result[col], 'percentage')
            
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'CUM_RETURN',
            'description': '累计收益率 - 指定周期内的累计收益率',
            'category': 'return_risk',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'cumulative_return',
            'formula': 'CUM_RETURN = (今价 - N日前价) / N日前价 × 100%',
            'output_columns': [f'CUM_RETURN_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'CUM_RETURN_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'CUM_RETURN_{period}'
                returns = result[col_name].dropna()
                
                if len(returns) == 0:
                    continue
                
                # 累计收益率应在合理范围内
                if (returns < -100).any() or (returns > 1000).any():
                    return False
            
            return True
        except Exception:
            return False


__all__ = ['CUM_RETURN']