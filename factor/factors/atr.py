"""
ATR - 平均真实波幅
Average True Range - TR的移动平均，衡量波动性
向量化实现，支持多周期计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class ATR(BaseFactor):
    """ATR平均真实波幅因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化ATR因子
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
        向量化计算ATR平均真实波幅
        ATR = TR的移动平均
        
        Args:
            data: 包含OHLC数据的DataFrame
        Returns:
            包含ATR因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 先计算TR
        high = data['hfq_high']
        low = data['hfq_low']
        close = data['hfq_close']
        
        # 获取前一日收盘价
        prev_close = close.shift(1)
        
        # 计算TR
        hl = high - low
        hc = (high - prev_close).abs()
        lc = (low - prev_close).abs()
        tr_values = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        
        # 向量化计算所有周期的ATR
        for period in self.params["periods"]:
            column_name = f'ATR_{period}'
            
            # 计算TR的移动平均 (使用EMA更平滑)
            atr_values = tr_values.ewm(
                span=period,
                adjust=False
            ).mean()
            
            # 应用全局精度配置
            atr_values = atr_values.round(config.get_precision('price'))
            
            result[column_name] = atr_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('ATR_')]
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            # ATR应为正数
            result[col] = result[col].where(result[col] >= 0)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算ATR所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'ATR',
            'description': '平均真实波幅 - TR的移动平均，衡量波动性',
            'category': 'volatility',
            'periods': self.params['periods'],
            'data_type': 'volatility',
            'calculation_method': 'average_true_range',
            'formula': 'ATR = EMA(TR, period)',
            'output_columns': [f'ATR_{p}' for p in self.params['periods']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证ATR计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'ATR_{p}' for p in self.params['periods']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查ATR值的合理性
            for period in self.params['periods']:
                col_name = f'ATR_{period}'
                atr_values = result[col_name].dropna()
                
                if len(atr_values) == 0:
                    continue
                
                # ATR值应为正数
                if (atr_values < 0).any():
                    return False
                
                # ATR值应在合理范围内
                if (atr_values > 100).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['ATR']


def create_default_atr():
    """创建默认配置的ATR因子实例"""
    return ATR()


def create_custom_atr(periods):
    """创建自定义周期的ATR因子实例"""
    return ATR({"periods": periods})


# 因子测试功能
def test_atr_calculation():
    """测试ATR因子计算功能"""
    print("🧪 测试ATR因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_high':  [10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.2, 11.0, 11.3,
                      11.1, 11.4, 11.2, 11.5, 11.3, 11.6, 11.4, 11.7, 11.5, 11.8],
        'hfq_low':   [10.0, 10.2, 10.1, 10.3, 10.1, 10.4, 10.2, 10.5, 10.3, 10.6,
                      10.4, 10.7, 10.5, 10.8, 10.6, 10.9, 10.7, 11.0, 10.8, 11.1],
        'hfq_close': [10.2, 10.5, 10.3, 10.6, 10.4, 10.7, 10.5, 10.8, 10.6, 10.9,
                      10.7, 11.0, 10.8, 11.1, 10.9, 11.2, 11.0, 11.3, 11.1, 11.4]
    })
    
    # 创建ATR因子
    atr_factor = ATR({"periods": [14]})
    
    # 计算因子
    result = atr_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - ATR_14样例: {result['ATR_14'].iloc[:5].tolist()}")
    
    # 验证结果
    is_valid = atr_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_atr_calculation()