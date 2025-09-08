"""
RSI - 相对强弱指标
Relative Strength Index - 动量震荡指标
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


class RSI(BaseFactor):
    """RSI指标因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化RSI因子
        Args:
            params: 参数字典，包含periods字段，默认{"periods": [6,14,24]}
        """
        # 处理参数格式
        if params is None:
            periods = [6, 14, 24]
        elif isinstance(params, dict):
            periods = params.get("periods", [6, 14, 24])
        elif isinstance(params, list):
            periods = params
        else:
            periods = [6, 14, 24]
        
        super().__init__({"periods": periods})
        
        # 验证参数
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")
        
        if not all(isinstance(p, int) and p > 1 for p in periods):
            raise ValueError("所有周期必须是大于1的正整数")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算RSI指标
        RSI = 100 - (100 / (1 + RS))
        RS = 平均上涨幅度 / 平均下跌幅度
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含RSI因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据 (按日期升序排列用于计算)
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']
        
        # 计算价格变化
        price_change = close_prices.diff()
        
        # 分离上涨和下跌
        gains = price_change.where(price_change > 0, 0)
        losses = -price_change.where(price_change < 0, 0)
        
        # 向量化计算所有周期的RSI
        for period in self.params["periods"]:
            column_name = f'RSI_{period}'
            
            # 计算平均收益和平均损失 (使用EMA)
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()
            
            # 计算相对强度RS
            rs = avg_gains / avg_losses
            
            # 计算RSI
            rsi_values = 100 - (100 / (1 + rs))
            
            # 处理特殊情况
            rsi_values = rsi_values.fillna(50)  # 当分母为0时，RSI为50
            
            # 应用全局精度配置
            rsi_values = rsi_values.round(config.get_precision('indicator'))
            
            result[column_name] = rsi_values
        
        # 恢复原始排序（最新日期在前）
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('RSI_')]
        for col in numeric_columns:
            # RSI应在0-100范围内
            result[col] = result[col].clip(0, 100)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算RSI所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'RSI',
            'description': '相对强弱指标 - 动量震荡指标，范围0-100',
            'category': 'trend_momentum',
            'periods': self.params['periods'],
            'data_type': 'momentum',
            'calculation_method': 'relative_strength_index',
            'formula': 'RSI = 100 - (100 / (1 + 平均收益/平均损失))',
            'output_columns': [f'RSI_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证RSI计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'RSI_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查RSI值的合理性
            for period in self.params['periods']:
                col_name = f'RSI_{period}'
                rsi_values = result[col_name].dropna()
                
                if len(rsi_values) == 0:
                    continue
                
                # RSI值应在0-100范围内
                if (rsi_values < 0).any() or (rsi_values > 100).any():
                    return False
                
                # 检查是否有异常值
                if rsi_values.isnull().all():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['RSI']


def create_default_rsi():
    """创建默认配置的RSI因子实例"""
    return RSI()


def create_custom_rsi(periods):
    """创建自定义周期的RSI因子实例"""
    return RSI({"periods": periods})


# 因子测试功能
def test_rsi_calculation():
    """测试RSI因子计算功能"""
    print("🧪 测试RSI因子计算...")
    
    # 创建测试数据 (包含上涨和下跌)
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_close': [10.0, 10.1, 9.9, 10.2, 9.8, 10.3, 10.0, 10.4, 10.1, 10.5,
                      10.2, 10.6, 10.3, 10.1, 10.7, 10.4, 10.8, 10.5, 10.2, 10.9]
    })
    
    # 创建RSI因子
    rsi_factor = RSI({"periods": [6, 14]})
    
    # 计算因子
    result = rsi_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - RSI_6样例: {result['RSI_6'].iloc[:3].tolist()}")
    print(f"   - RSI_14样例: {result['RSI_14'].iloc[:3].tolist()}")
    
    # 验证结果
    is_valid = rsi_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_rsi_calculation()