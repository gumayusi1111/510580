"""
VMA - 成交量移动均线
Volume Moving Average - 成交量的移动平均，分析量能趋势
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class VMA(BaseFactor):
    """成交量移动均线因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化VMA因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20]}
        """
        if params is None:
            periods = [5, 10, 20]
        elif isinstance(params, dict):
            periods = params.get("periods", [5, 10, 20])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [5, 10, 20]
        
        super().__init__({"periods": periods})
        
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("所有周期必须是正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算成交量移动均线
        VMA = SMA(成交量, period)
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取成交量数据 (使用原始成交量，不复权)
        volume = data['vol']
        
        # 计算各周期的VMA
        for period in self.params["periods"]:
            column_name = f'VMA_{period}'
            
            # 计算成交量移动平均
            vma_values = volume.rolling(window=period, min_periods=1).mean()
            
            # 应用精度配置
            vma_values = vma_values.round(config.get_precision('default'))
            
            result[column_name] = vma_values
        
        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('VMA_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # VMA使用默认数据范围验证
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'vol']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'VMA',
            'description': '成交量移动均线 - 成交量的移动平均',
            'category': 'volume_price',
            'periods': self.params['periods'],
            'data_type': 'volume',
            'calculation_method': 'volume_moving_average',
            'formula': 'VMA = SMA(成交量, period)',
            'output_columns': [f'VMA_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'VMA_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'VMA_{period}'
                values = result[col_name].dropna()
                
                if len(values) == 0:
                    continue
                
                # 成交量应为正数
                if (values < 0).any():
                    return False
            
            return True
        except Exception:
            return False


__all__ = ['VMA']