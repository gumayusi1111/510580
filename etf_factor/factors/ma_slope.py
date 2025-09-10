"""
MA_SLOPE - 移动均线斜率因子
Moving Average Slope - 反映移动均线的趋势方向和强度
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


class MA_SLOPE(BaseFactor):
    """移动均线斜率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化MA_SLOPE因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20]}
        """
        # 处理参数格式
        if params is None:
            periods = [5, 10, 20]
        elif isinstance(params, dict):
            periods = params.get("periods", [5, 10, 20])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [5, 10, 20]
        
        super().__init__({"periods": periods})
        
        # 验证参数
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 1 for p in periods):
            raise ValueError("所有周期必须是大于1的正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算移动均线斜率
        斜率 = (当前MA - N日前MA) / N
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含MA_SLOPE因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 向量化计算所有周期的MA斜率
        for period in self.params["periods"]:
            column_name = f'MA_SLOPE_{period}'
            
            # 先计算移动均线
            ma_values = close_prices.rolling(
                window=period,
                min_periods=1
            ).mean()
            
            # 修复逻辑：正确计算斜率
            # 前period行应该为NaN，因为没有足够的历史数据
            slope_values = pd.Series(index=ma_values.index, dtype=float)
            
            # 从第period行开始计算（有足够历史数据的位置）
            for i in range(period, len(ma_values)):
                current_ma = ma_values.iloc[i]
                prev_ma = ma_values.iloc[i - period]  # period天前的MA值
                if pd.notna(current_ma) and pd.notna(prev_ma):
                    slope_values.iloc[i] = (current_ma - prev_ma) / period
                else:
                    slope_values.iloc[i] = pd.NA
            
            # 应用全局精度配置
            slope_values = slope_values.round(config.get_precision('indicator'))
            
            result[column_name] = slope_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('MA_SLOPE_')]
        for col in numeric_columns:
            # 处理极值和异常值
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算MA_SLOPE所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'MA_SLOPE',
            'description': '移动均线斜率 - 反映移动均线的趋势方向和强度',
            'category': 'moving_average',
            'periods': self.params['periods'],
            'data_type': 'slope',
            'calculation_method': 'moving_average_slope',
            'formula': 'MA_SLOPE = (当前MA - N日前MA) / N',
            'output_columns': [f'MA_SLOPE_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证MA_SLOPE计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'MA_SLOPE_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查MA_SLOPE值的合理性
            for period in self.params['periods']:
                col_name = f'MA_SLOPE_{period}'
                slope_values = result[col_name].dropna()
                
                if len(slope_values) == 0:
                    continue
                
                # 斜率值应在合理范围内
                if (abs(slope_values) > 10).any():
                    return False
                
                # 检查是否有无穷大值
                if (slope_values == float('inf')).any() or (slope_values == float('-inf')).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['MA_SLOPE']


def create_default_ma_slope():
    """创建默认配置的MA_SLOPE因子实例"""
    return MA_SLOPE()


def create_custom_ma_slope(periods):
    """创建自定义周期的MA_SLOPE因子实例"""
    return MA_SLOPE({"periods": periods})


# 因子测试功能
def test_ma_slope_calculation():
    """测试MA_SLOPE因子计算功能"""
    print("🧪 测试MA_SLOPE因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [1.0, 1.1, 1.2, 1.15, 1.25, 1.35, 1.3, 1.4, 1.45, 1.5, 
                      1.55, 1.6, 1.58, 1.65, 1.7]
    })
    
    # 创建MA_SLOPE因子
    ma_slope_factor = MA_SLOPE({"periods": [5, 10]})
    
    # 计算因子
    result = ma_slope_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - MA_SLOPE_5样例: {result['MA_SLOPE_5'].iloc[:5].tolist()}")
    print(f"   - MA_SLOPE_10样例: {result['MA_SLOPE_10'].iloc[:5].tolist()}")
    
    # 验证结果
    is_valid = ma_slope_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_ma_slope_calculation()