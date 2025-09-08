"""
DAILY_RETURN - 日收益率
Daily Return - 单日价格变化百分比
向量化实现
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class DAILY_RETURN(BaseFactor):
    """日收益率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化DAILY_RETURN因子
        Args:
            params: 参数字典 (无参数)
        """
        super().__init__(params or {})
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算日收益率
        DAILY_RETURN = (今日收盘价 - 昨日收盘价) / 昨日收盘价 × 100%
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价
        close = data['hfq_close']
        
        # 计算日收益率
        daily_return = close.pct_change() * 100
        
        # 应用精度配置
        daily_return = daily_return.round(config.get_precision('percentage'))
        
        result['DAILY_RETURN'] = daily_return
        
        # 数据清理
        result['DAILY_RETURN'] = result['DAILY_RETURN'].replace([float('inf'), -float('inf')], pd.NA)
        result['DAILY_RETURN'] = config.validate_data_range(result['DAILY_RETURN'], 'percentage')
        
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'DAILY_RETURN',
            'description': '日收益率 - 单日价格变化百分比',
            'category': 'return_risk',
            'data_type': 'percentage',
            'calculation_method': 'daily_return',
            'formula': 'DAILY_RETURN = (今收 - 昨收) / 昨收 × 100%',
            'output_columns': ['DAILY_RETURN']
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            if 'DAILY_RETURN' not in result.columns:
                return False
            
            if len(result) == 0:
                return False
            
            returns = result['DAILY_RETURN'].dropna()
            if len(returns) == 0:
                return len(result) > 0  # 第一行可能为NA
            
            # 日收益率应在合理范围内 (-100%, 100%)
            if (returns < -100).any() or (returns > 100).any():
                return False
            
            return True
        except Exception:
            return False


__all__ = ['DAILY_RETURN']