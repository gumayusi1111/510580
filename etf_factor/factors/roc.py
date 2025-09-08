"""
ROC - 变动率指标
Rate of Change - 价格变动百分比
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class ROC(BaseFactor):
    """ROC变动率因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化ROC因子
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
        
        if not all(isinstance(p, int) and p > 0 for p in periods):
            raise ValueError("所有周期必须是正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算ROC指标
        ROC = (当前价格 - N日前价格) / N日前价格 × 100%
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含ROC因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 向量化计算所有周期的ROC
        for period in self.params["periods"]:
            column_name = f'ROC_{period}'
            
            # 获取N日前的价格
            prev_prices = close_prices.shift(period)
            
            # 计算变动率
            roc_values = ((close_prices - prev_prices) / prev_prices) * 100
            
            # 应用全局精度配置
            roc_values = roc_values.round(config.get_precision('percentage'))
            
            result[column_name] = roc_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('ROC_')]
        for col in numeric_columns:
            # 处理极值和异常值
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # 使用配置的百分比数据范围验证
            result[col] = config.validate_data_range(result[col], 'percentage')
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算ROC所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'ROC',
            'description': 'Rate of Change - 价格变动百分比',
            'category': 'trend_momentum',
            'periods': self.params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'rate_of_change',
            'formula': 'ROC = (当前价格 - N日前价格) / N日前价格 × 100%',
            'output_columns': [f'ROC_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证ROC计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'ROC_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查ROC值的合理性
            for period in self.params['periods']:
                col_name = f'ROC_{period}'
                roc_values = result[col_name].dropna()
                
                if len(roc_values) == 0:
                    continue
                
                # ROC值应在合理的百分比范围内
                if (abs(roc_values) > 1000).any():  # 超过1000%变动为异常
                    return False
                
                # 检查是否有无穷大值
                if (roc_values == float('inf')).any() or (roc_values == float('-inf')).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['ROC']


def create_default_roc():
    """创建默认配置的ROC因子实例"""
    return ROC()


def create_custom_roc(periods):
    """创建自定义周期的ROC因子实例"""
    return ROC({"periods": periods})


# 因子测试功能
def test_roc_calculation():
    """测试ROC因子计算功能"""
    print("🧪 测试ROC因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [10.0, 10.1, 10.2, 9.8, 10.5, 10.3, 10.7, 10.4, 10.8, 10.6,
                      11.0, 10.9, 11.2, 11.1, 11.5]
    })
    
    # 创建ROC因子
    roc_factor = ROC({"periods": [5, 10]})
    
    # 计算因子
    result = roc_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - ROC_5样例: {result['ROC_5'].iloc[:5].tolist()}")
    print(f"   - ROC_10样例: {result['ROC_10'].iloc[:5].tolist()}")
    
    # 验证结果
    is_valid = roc_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_roc_calculation()