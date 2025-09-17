"""
RSI核心计算模块
专注于RSI指标的算法实现
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.base_factor import BaseFactor
from src.config import config

# 使用绝对路径导入避免模块名冲突
import importlib.util

# 导入RsiConfig
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'config.py')
spec = importlib.util.spec_from_file_location("rsi_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
RsiConfig = config_module.RsiConfig


class RSI(BaseFactor):
    """相对强弱指标因子 - 模块化实现"""

    def __init__(self, params=None):
        validated_params = RsiConfig.validate_params(params)
        super().__init__(validated_params)

    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data[['ts_code', 'trade_date']].copy()
        
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']
        
        price_change = close_prices.diff()
        gains = price_change.where(price_change > 0, 0)
        losses = -price_change.where(price_change < 0, 0)
        
        for period in self.params["periods"]:
            column_name = f'RSI_{period}'
            
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()
            
            rs = avg_gains / avg_losses
            rsi_values = 100 - (100 / (1 + rs))
            rsi_values = rsi_values.fillna(50)
            rsi_values = rsi_values.round(config.get_precision('indicator'))
            
            result[column_name] = rsi_values
        
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # RSI应在0-100范围内
        numeric_columns = [col for col in result.columns if col.startswith('RSI_')]
        for col in numeric_columns:
            result[col] = result[col].clip(0, 100)
            
        return result
    
    def get_required_columns(self) -> list:
        return RsiConfig.get_required_columns()
    
    def get_factor_info(self) -> dict:
        return RsiConfig.get_factor_info(self.params)
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        try:
            expected_columns = ['ts_code', 'trade_date'] + RsiConfig.get_expected_output_columns(self.params)
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'RSI_{period}'
                rsi_values = result[col_name].dropna()
                
                if len(rsi_values) == 0:
                    continue
                
                if (rsi_values < 0).any() or (rsi_values > 100).any():
                    return False
                    
            return True
        except Exception:
            return False