"""
MAX_DD - 最大回撤
Maximum Drawdown - 指定周期内的最大回撤率
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class MAX_DD(BaseFactor):
    """最大回撤因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化MAX_DD因子
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
        向量化计算最大回撤
        MAX_DD = (期间最高价 - 期间最低价) / 期间最高价 × 100%
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价
        close = data['hfq_close']
        
        # 计算各周期的最大回撤
        for period in self.params["periods"]:
            column_name = f'MAX_DD_{period}'
            
            def calculate_max_drawdown(prices):
                """计算单个窗口的最大回撤"""
                if len(prices) == 0:
                    return 0.0
                
                # 转换为pandas Series以使用expanding
                prices_series = pd.Series(prices)
                
                # 计算累计最高价
                cumulative_max = prices_series.expanding().max()
                
                # 计算回撤
                drawdown = (prices_series - cumulative_max) / cumulative_max
                
                # 返回最大回撤 (绝对值，转换为正数百分比)
                max_dd = abs(drawdown.min()) * 100
                return max_dd
            
            # 使用滚动窗口计算最大回撤
            max_dd_values = close.rolling(
                window=period, 
                min_periods=1
            ).apply(calculate_max_drawdown, raw=True)
            
            # 应用精度配置
            max_dd_values = max_dd_values.round(config.get_precision('percentage'))
            
            result[column_name] = max_dd_values
        
        # 数据清理
        numeric_columns = [col for col in result.columns if col.startswith('MAX_DD_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # 最大回撤应为正数
            result[col] = result[col].where(result[col] >= 0)
            
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        return {
            'name': 'MAX_DD',
            'description': '最大回撤 - 指定周期内的最大回撤率',
            'category': 'return_risk',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'maximum_drawdown',
            'formula': 'MAX_DD = MAX((累计最高价-当前价)/累计最高价) × 100%',
            'output_columns': [f'MAX_DD_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'MAX_DD_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'MAX_DD_{period}'
                dd_values = result[col_name].dropna()
                
                if len(dd_values) == 0:
                    continue
                
                # 最大回撤应为正数且在合理范围内
                if (dd_values < 0).any() or (dd_values > 100).any():
                    return False
            
            return True
        except Exception:
            return False


__all__ = ['MAX_DD']