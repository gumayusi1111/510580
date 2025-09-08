"""
SMA - 简单移动均线因子
Simple Moving Average - 第一个示例因子
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class SMA(BaseFactor):
    """简单移动均线因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化SMA因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [5,10,20,60]}
        """
        # 处理参数格式
        if params is None:
            periods = [5, 10, 20, 60]
        elif isinstance(params, dict):
            periods = params.get("periods", [5, 10, 20, 60])
        elif isinstance(params, list):
            # 向后兼容：直接传入periods列表
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
        向量化计算简单移动均线
        使用pandas.rolling()进行高效计算
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含SMA因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 向量化计算所有周期的SMA
        for period in self.params["periods"]:
            column_name = f'SMA_{period}'
            
            # pandas向量化计算 - 核心优化点
            sma_values = close_prices.rolling(
                window=period, 
                min_periods=1  # 允许不足周期的计算
            ).mean()
            
            # 应用全局精度配置
            sma_values = sma_values.round(config.get_precision('price'))
            
            result[column_name] = sma_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('SMA_')]
        for col in numeric_columns:
            # 处理异常值
            result[col] = config.validate_data_range(result[col], 'price')
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算SMA所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'SMA',
            'description': '简单移动均线 - 趋势跟踪指标',
            'category': 'moving_average',
            'periods': self.params['periods'],
            'data_type': 'price',
            'calculation_method': 'rolling_mean',
            'output_columns': [f'SMA_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'SMA_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查SMA值的合理性
            for period in self.params['periods']:
                col_name = f'SMA_{period}'
                sma_values = result[col_name].dropna()
                
                if len(sma_values) == 0:
                    continue
                
                # SMA值应该为正数（价格数据）
                if (sma_values <= 0).any():
                    return False
                
                # SMA值应在合理范围内
                if (sma_values > 10000).any() or (sma_values < 0.001).any():
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_performance_stats(self, data: pd.DataFrame, result: pd.DataFrame) -> dict:
        """获取计算性能统计"""
        stats = {
            'input_rows': len(data),
            'output_rows': len(result),
            'periods_calculated': len(self.params['periods']),
            'output_columns': len([col for col in result.columns if col.startswith('SMA_')]),
            'data_completeness': {}
        }
        
        # 数据完整性统计
        for period in self.params['periods']:
            col_name = f'SMA_{period}'
            if col_name in result.columns:
                non_null_count = result[col_name].notna().sum()
                completeness = non_null_count / len(result) if len(result) > 0 else 0
                stats['data_completeness'][col_name] = {
                    'non_null_count': int(non_null_count),
                    'completeness_ratio': round(completeness, 4)
                }
        
        return stats


# 因子自动注册机制所需的导出
__all__ = ['SMA']


def create_default_sma():
    """创建默认配置的SMA因子实例"""
    return SMA()


def create_custom_sma(periods):
    """创建自定义周期的SMA因子实例"""
    return SMA({"periods": periods})


# 因子测试功能
def test_sma_calculation():
    """测试SMA因子计算功能"""
    print("🧪 测试SMA因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })
    
    # 创建SMA因子
    sma_factor = SMA({"periods": [3, 5]})
    
    # 计算因子
    result = sma_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - SMA_3样例: {result['SMA_3'].iloc[-3:].tolist()}")
    print(f"   - SMA_5样例: {result['SMA_5'].iloc[-3:].tolist()}")
    
    # 验证结果
    is_valid = sma_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    # 性能统计
    stats = sma_factor.get_performance_stats(test_data, result)
    print(f"   - 数据完整性: {stats['data_completeness']}")
    
    return result


if __name__ == "__main__":
    test_sma_calculation()