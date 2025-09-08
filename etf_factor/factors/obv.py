"""
OBV - 能量潮指标
On-Balance Volume - 累计成交量指标，反映资金流向
向量化实现
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class OBV(BaseFactor):
    """OBV能量潮指标因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化OBV因子
        Args:
            params: 参数字典 (OBV无参数)
        """
        super().__init__(params or {})
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算OBV能量潮
        当日价格 > 昨日价格: OBV = 前日OBV + 今日成交量
        当日价格 < 昨日价格: OBV = 前日OBV - 今日成交量  
        当日价格 = 昨日价格: OBV = 前日OBV
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取价格和成交量数据
        close = data['hfq_close']
        volume = data['vol']
        
        # 计算价格变化方向
        price_change = close.diff()
        
        # 根据价格变化决定成交量的符号
        volume_direction = pd.Series(0, index=volume.index)
        volume_direction[price_change > 0] = 1   # 价格上涨
        volume_direction[price_change < 0] = -1  # 价格下跌
        volume_direction[price_change == 0] = 0  # 价格不变
        
        # 计算有向成交量
        signed_volume = volume * volume_direction
        
        # 累计求和得到OBV
        obv_values = signed_volume.cumsum()
        
        # 应用精度配置
        obv_values = obv_values.round(config.get_precision('default'))
        
        result['OBV'] = obv_values
        
        # 数据清理
        result['OBV'] = result['OBV'].replace([float('inf'), -float('inf')], pd.NA)
        
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close', 'vol']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'OBV',
            'description': '能量潮指标 - 累计成交量指标，反映资金流向',
            'category': 'volume_price',
            'data_type': 'volume',
            'calculation_method': 'on_balance_volume',
            'formula': 'OBV = 累计(价格方向 × 成交量)',
            'output_columns': ['OBV']
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            if 'OBV' not in result.columns:
                return False
            
            if len(result) == 0:
                return False
            
            obv_values = result['OBV'].dropna()
            if len(obv_values) == 0:
                return len(result) > 0  # 允许部分NA值
            
            # OBV是累计值，应该是递增趋势（允许有负值）
            return True
        except Exception:
            return False


__all__ = ['OBV']