"""
WMA - 加权移动均线因子
Weighted Moving Average - 线性递减权重，最近的价格权重最高
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class WMA(BaseFactor):
    """加权移动均线因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化WMA因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20,60]}
        """
        # 处理参数格式
        if params is None:
            periods = [5, 10, 20, 60]
        elif isinstance(params, dict):
            periods = params.get("periods", [5, 10, 20, 60])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [5, 10, 20, 60]
        
        super().__init__({"periods": periods})
        
        # 验证参数
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("所有周期必须是正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算加权移动均线
        WMA = Σ(价格 × 权重) / Σ(权重)
        权重: [1,2,3,...,N] (最近的价格权重最高)
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含WMA因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 向量化计算所有周期的WMA
        for period in self.params["periods"]:
            column_name = f'WMA_{period}'
            
            # 生成权重：[1,2,3,...,period]
            weights = list(range(1, period + 1))
            weights_sum = sum(weights)
            
            # 向量化计算WMA - 核心优化点
            def calculate_wma_single(series):
                """计算单个WMA值"""
                if len(series) < period:
                    # 不足周期时使用可用数据
                    available_weights = weights[:len(series)]
                    available_weights_sum = sum(available_weights)
                    return (series * available_weights).sum() / available_weights_sum
                else:
                    return (series * weights).sum() / weights_sum
            
            # 使用rolling + apply进行向量化计算
            wma_values = close_prices.rolling(
                window=period,
                min_periods=1
            ).apply(calculate_wma_single, raw=True)
            
            # 应用全局精度配置
            wma_values = wma_values.round(config.get_precision('price'))
            
            result[column_name] = wma_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('WMA_')]
        for col in numeric_columns:
            result[col] = config.validate_data_range(result[col], 'price')
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算WMA所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'WMA',
            'description': '加权移动均线 - 线性递减权重，最近价格权重最高',
            'category': 'moving_average',
            'periods': self.params['periods'],
            'data_type': 'price',
            'calculation_method': 'linear_weighted_average',
            'formula': 'WMA = Σ(价格 × [1,2,3...N]) / Σ[1,2,3...N]',
            'output_columns': [f'WMA_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证WMA计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'WMA_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查WMA值的合理性
            for period in self.params['periods']:
                col_name = f'WMA_{period}'
                wma_values = result[col_name].dropna()
                
                if len(wma_values) == 0:
                    continue
                
                # WMA值应该为正数
                if (wma_values <= 0).any():
                    return False
                
                # WMA值应在合理范围内
                if (wma_values > 10000).any() or (wma_values < 0.001).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['WMA']


def create_default_wma():
    """创建默认配置的WMA因子实例"""
    return WMA()


def create_custom_wma(periods):
    """创建自定义周期的WMA因子实例"""
    return WMA({"periods": periods})


# 因子测试功能
def test_wma_calculation():
    """测试WMA因子计算功能"""
    print("🧪 测试WMA因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 6,
        'trade_date': pd.date_range('2025-01-01', periods=6),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    })
    
    # 创建WMA因子
    wma_factor = WMA({"periods": [3, 5]})
    
    # 计算因子
    result = wma_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - WMA_3样例: {result['WMA_3'].iloc[:3].tolist()}")
    print(f"   - WMA_5样例: {result['WMA_5'].iloc[:3].tolist()}")
    
    # 验证结果
    is_valid = wma_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_wma_calculation()