"""
EMA - 指数移动均线因子
Exponential Moving Average - 对近期价格给予更高权重
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class EMA(BaseFactor):
    """指数移动均线因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化EMA因子
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
        向量化计算指数移动均线
        EMA = 前一日EMA × (1-α) + 今日收盘价 × α
        其中 α = 2/(N+1), N为周期
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含EMA因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据 (按日期升序排列用于EMA计算)
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']
        
        # 向量化计算所有周期的EMA
        for period in self.params["periods"]:
            column_name = f'EMA_{period}'
            
            # pandas向量化计算EMA - 核心优化点
            ema_values = close_prices.ewm(
                span=period,           # EMA周期
                adjust=False           # 不调整权重（标准EMA算法）
            ).mean()
            
            # 应用全局精度配置
            ema_values = ema_values.round(config.get_precision('price'))
            
            result[column_name] = ema_values
        
        # 恢复原始排序（最新日期在前）
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('EMA_')]
        for col in numeric_columns:
            result[col] = config.validate_data_range(result[col], 'price')
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算EMA所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'EMA',
            'description': '指数移动均线 - 对近期价格给予更高权重',
            'category': 'moving_average',
            'periods': self.params['periods'],
            'data_type': 'price',
            'calculation_method': 'exponential_weighted_mean',
            'formula': 'EMA = 前EMA × (1-α) + 当前价 × α, α=2/(N+1)',
            'output_columns': [f'EMA_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证EMA计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'EMA_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查EMA值的合理性
            for period in self.params['periods']:
                col_name = f'EMA_{period}'
                ema_values = result[col_name].dropna()
                
                if len(ema_values) == 0:
                    continue
                
                # EMA值应该为正数
                if (ema_values <= 0).any():
                    return False
                
                # EMA值应在合理范围内
                if (ema_values > 10000).any() or (ema_values < 0.001).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['EMA']


def create_default_ema():
    """创建默认配置的EMA因子实例"""
    return EMA()


def create_custom_ema(periods):
    """创建自定义周期的EMA因子实例"""
    return EMA({"periods": periods})


# 因子测试功能
def test_ema_calculation():
    """测试EMA因子计算功能"""
    print("🧪 测试EMA因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })
    
    # 创建EMA因子
    ema_factor = EMA({"periods": [3, 5]})
    
    # 计算因子
    result = ema_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - EMA_3样例: {result['EMA_3'].iloc[:3].tolist()}")
    print(f"   - EMA_5样例: {result['EMA_5'].iloc[:3].tolist()}")
    
    # 验证结果
    is_valid = ema_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_ema_calculation()