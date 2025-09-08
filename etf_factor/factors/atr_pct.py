"""
ATR_PCT - ATR百分比
ATR Percentage - ATR相对于价格的百分比，标准化的波动率指标
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class ATR_PCT(BaseFactor):
    """ATR百分比因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化ATR_PCT因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [14]}
        """
        # 处理参数格式
        if params is None:
            periods = [14]
        elif isinstance(params, dict):
            periods = params.get("periods", [14])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [14]
        
        super().__init__({"periods": periods})
        
        # 验证参数
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("所有周期必须是正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算ATR百分比
        ATR_PCT = ATR / 收盘价 × 100%
        
        Args:
            data: 包含OHLC数据的DataFrame
        Returns:
            包含ATR_PCT因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 计算TR
        high = data['hfq_high']
        low = data['hfq_low']
        close = data['hfq_close']
        prev_close = close.shift(1)
        
        hl = high - low
        hc = (high - prev_close).abs()
        lc = (low - prev_close).abs()
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        
        # 计算各周期的ATR_PCT
        for period in self.params["periods"]:
            column_name = f'ATR_PCT_{period}'
            
            # 计算ATR
            atr_values = tr_values.ewm(span=period, adjust=False).mean()
            
            # 计算ATR百分比
            atr_pct_values = (atr_values / close) * 100
            
            # 应用全局精度配置
            atr_pct_values = atr_pct_values.round(config.get_precision('percentage'))
            
            result[column_name] = atr_pct_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('ATR_PCT_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            result[col] = config.validate_data_range(result[col], 'percentage')
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算ATR_PCT所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'ATR_PCT',
            'description': 'ATR百分比 - ATR相对于价格的百分比',
            'category': 'volatility',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'atr_percentage',
            'formula': 'ATR_PCT = ATR / 收盘价 × 100%',
            'output_columns': [f'ATR_PCT_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证ATR_PCT计算结果的合理性"""
        try:
            expected_columns = ['ts_code', 'trade_date'] + [f'ATR_PCT_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            for period in self.params['periods']:
                col_name = f'ATR_PCT_{period}'
                values = result[col_name].dropna()
                
                if len(values) == 0:
                    continue
                
                # ATR_PCT应为正数且在合理范围内
                if (values < 0).any() or (values > 100).any():
                    return False
            
            return True
            
        except Exception:
            return False


__all__ = ['ATR_PCT']

if __name__ == "__main__":
    # 简单测试
    import pandas as pd
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high': [10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.2, 11.0, 11.3],
        'hfq_low': [10.0, 10.2, 10.1, 10.3, 10.1, 10.4, 10.2, 10.5, 10.3, 10.6],
        'hfq_close': [10.2, 10.5, 10.3, 10.6, 10.4, 10.7, 10.5, 10.8, 10.6, 10.9]
    })
    
    factor = ATR_PCT()
    result = factor.calculate_vectorized(test_data)
    print(f"✅ ATR_PCT测试: {result['ATR_PCT_14'].iloc[:3].tolist()}")
    print(f"验证: {'通过' if factor.validate_calculation_result(result) else '失败'}")