"""
TR - 真实波幅
True Range - 衡量价格波动幅度的指标
向量化实现，是ATR计算的基础
文件限制: <200行
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class TR(BaseFactor):
    """TR真实波幅因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化TR因子
        Args:
            params: 参数字典 (TR没有参数，保持接口一致性)
        """
        super().__init__(params or {})
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算TR真实波幅
        TR = MAX(高-低, ABS(高-昨收), ABS(低-昨收))
        
        Args:
            data: 包含OHLC数据的DataFrame
        Returns:
            包含TR因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取OHLC数据
        high = data['hfq_high']
        low = data['hfq_low']
        close = data['hfq_close']
        
        # 获取前一日收盘价
        prev_close = close.shift(1)
        
        # 计算三种波幅
        hl = high - low  # 当日最高价与最低价之差
        hc = (high - prev_close).abs()  # 当日最高价与昨收之差的绝对值
        lc = (low - prev_close).abs()   # 当日最低价与昨收之差的绝对值
        
        # 取三者中的最大值
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        
        # 应用全局精度配置
        tr_values = tr_values.round(config.get_precision('price'))
        
        result['TR'] = tr_values
        
        # 数据验证和清理
        result['TR'] = result['TR'].replace([float('inf'), -float('inf')], pd.NA)
        # TR应为正数
        result['TR'] = result['TR'].where(result['TR'] >= 0)
        
        return result
    
    def get_required_columns(self) -> list:
        """获取计算TR所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'TR',
            'description': '真实波幅 - 衡量价格波动幅度的指标',
            'category': 'volatility',
            'data_type': 'volatility',
            'calculation_method': 'true_range',
            'formula': 'TR = MAX(高-低, ABS(高-昨收), ABS(低-昨收))',
            'output_columns': ['TR']
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证TR计算结果的合理性"""
        try:
            # 检查输出列
            if 'TR' not in result.columns:
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查TR值的合理性
            tr_values = result['TR'].dropna()
            
            if len(tr_values) == 0:
                # 第一行可能为NA（因为缺少前一日收盘价）
                return len(result) > 0
            
            # TR值应为正数
            if (tr_values < 0).any():
                return False
            
            # TR值应在合理范围内
            if (tr_values > 100).any():
                return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['TR']


def create_default_tr():
    """创建默认配置的TR因子实例"""
    return TR()


# 因子测试功能
def test_tr_calculation():
    """测试TR因子计算功能"""
    print("🧪 测试TR因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_high':  [10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.2, 11.0, 11.3],
        'hfq_low':   [10.0, 10.2, 10.1, 10.3, 10.1, 10.4, 10.2, 10.5, 10.3, 10.6],
        'hfq_close': [10.2, 10.5, 10.3, 10.6, 10.4, 10.7, 10.5, 10.8, 10.6, 10.9]
    })
    
    # 创建TR因子
    tr_factor = TR()
    
    # 计算因子
    result = tr_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - TR样例: {result['TR'].iloc[:5].tolist()}")
    
    # 验证结果
    is_valid = tr_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_tr_calculation()