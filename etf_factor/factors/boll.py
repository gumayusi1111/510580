"""
BOLL - 布林带
Bollinger Bands - 基于移动平均和标准差的波动率指标
向量化实现，输出上轨、中轨、下轨
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class BOLL(BaseFactor):
    """布林带因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化BOLL因子
        Args:
            params: 参数字典，默认{"period": 20, "std_dev": 2}
        """
        if params is None:
            period = 20
            std_dev = 2
        elif isinstance(params, dict):
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2)
        else:
            period = 20
            std_dev = 2
        
        super().__init__({"period": period, "std_dev": std_dev})
        
        # 验证参数
        if not isinstance(period, int) or period <= 0:
            raise ValueError("period必须是正整数")
        if not isinstance(std_dev, (int, float)) or std_dev <= 0:
            raise ValueError("std_dev必须是正数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算布林带
        MID = SMA(收盘价, period)
        UPPER = MID + std_dev × STD(收盘价, period)
        LOWER = MID - std_dev × STD(收盘价, period)
        """
        result = data[['ts_code', 'trade_date']].copy()
        
        close = data['hfq_close']
        period = self.params["period"]
        std_dev = self.params["std_dev"]
        
        # 计算中轨 (移动平均)
        mid = close.rolling(window=period, min_periods=1).mean()
        
        # 计算标准差
        std = close.rolling(window=period, min_periods=1).std()
        
        # 计算上下轨
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        
        # 应用精度配置
        precision = config.get_precision('price')
        result['BOLL_UPPER'] = upper.round(precision)
        result['BOLL_MID'] = mid.round(precision)
        result['BOLL_LOWER'] = lower.round(precision)
        
        # 数据清理
        for col in ['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算BOLL所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'BOLL',
            'description': '布林带 - 基于移动平均和标准差的波动率指标',
            'category': 'volatility',
            'period': self.params['period'],
            'std_dev': self.params['std_dev'],
            'data_type': 'price',
            'calculation_method': 'bollinger_bands',
            'formula': 'UPPER=SMA+2×STD, MID=SMA, LOWER=SMA-2×STD',
            'output_columns': ['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证BOLL计算结果的合理性"""
        try:
            expected_columns = ['ts_code', 'trade_date', 'BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER']
            if not all(col in result.columns for col in expected_columns):
                return False
            
            if len(result) == 0:
                return False
            
            # 检查上中下轨的逻辑关系
            valid_data = result.dropna(subset=['BOLL_UPPER', 'BOLL_MID', 'BOLL_LOWER'])
            if len(valid_data) > 0:
                # 上轨应大于中轨，中轨应大于下轨
                if not ((valid_data['BOLL_UPPER'] >= valid_data['BOLL_MID']).all() and 
                        (valid_data['BOLL_MID'] >= valid_data['BOLL_LOWER']).all()):
                    return False
            
            return True
            
        except Exception:
            return False


__all__ = ['BOLL']

if __name__ == "__main__":
    import pandas as pd
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 25,
        'trade_date': pd.date_range('2025-01-01', periods=25),
        'hfq_close': [10.0 + 0.1 * i + 0.05 * (i % 3) for i in range(25)]
    })
    
    factor = BOLL()
    result = factor.calculate_vectorized(test_data)
    print(f"✅ BOLL测试: UPPER={result['BOLL_UPPER'].iloc[20]:.3f}, MID={result['BOLL_MID'].iloc[20]:.3f}, LOWER={result['BOLL_LOWER'].iloc[20]:.3f}")
    print(f"验证: {'通过' if factor.validate_calculation_result(result) else '失败'}")