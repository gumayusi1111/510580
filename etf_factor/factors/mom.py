"""
MOM - 动量指标
Momentum - 价格变化的绝对值
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class MOM(BaseFactor):
    """MOM动量指标因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化MOM因子
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
        向量化计算MOM动量指标
        MOM = 当前价格 - N日前价格
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含MOM因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 向量化计算所有周期的MOM
        for period in self.params["periods"]:
            column_name = f'MOM_{period}'
            
            # 修复逻辑：正确处理历史数据
            # 前period行应该为NaN，因为没有足够的历史数据
            mom_values = pd.Series(index=close_prices.index, dtype=float)
            
            # 从第period行开始计算（有足够历史数据的位置）
            for i in range(period, len(close_prices)):
                current_price = close_prices.iloc[i]
                prev_price = close_prices.iloc[i - period]  # period天前的价格
                if pd.notna(current_price) and pd.notna(prev_price):
                    mom_values.iloc[i] = current_price - prev_price
                else:
                    mom_values.iloc[i] = pd.NA
            
            # 应用全局精度配置
            mom_values = mom_values.round(config.get_precision('price'))
            
            result[column_name] = mom_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('MOM_')]
        for col in numeric_columns:
            # 处理极值和异常值
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算MOM所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'MOM',
            'description': '动量指标 - 价格变化的绝对值',
            'category': 'trend_momentum',
            'periods': self.params['periods'],
            'data_type': 'price_diff',
            'calculation_method': 'momentum',
            'formula': 'MOM = 当前价格 - N日前价格',
            'output_columns': [f'MOM_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证MOM计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'MOM_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查MOM值的合理性
            for period in self.params['periods']:
                col_name = f'MOM_{period}'
                mom_values = result[col_name].dropna()
                
                if len(mom_values) == 0:
                    continue
                
                # MOM值应在合理范围内
                if (abs(mom_values) > 100).any():
                    return False
                
                # 检查是否有无穷大值
                if (mom_values == float('inf')).any() or (mom_values == float('-inf')).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['MOM']


def create_default_mom():
    """创建默认配置的MOM因子实例"""
    return MOM()


def create_custom_mom(periods):
    """创建自定义周期的MOM因子实例"""
    return MOM({"periods": periods})


# 因子测试功能
def test_mom_calculation():
    """测试MOM因子计算功能"""
    print("🧪 测试MOM因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 15,
        'trade_date': pd.date_range('2025-01-01', periods=15),
        'hfq_close': [10.0, 10.1, 10.2, 9.8, 10.5, 10.3, 10.7, 10.4, 10.8, 10.6,
                      11.0, 10.9, 11.2, 11.1, 11.5]
    })
    
    # 创建MOM因子
    mom_factor = MOM({"periods": [5, 10]})
    
    # 计算因子
    result = mom_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - MOM_5样例: {result['MOM_5'].iloc[:5].tolist()}")
    print(f"   - MOM_10样例: {result['MOM_10'].iloc[:5].tolist()}")
    
    # 验证结果
    is_valid = mom_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_mom_calculation()