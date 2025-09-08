"""
MACD - 指数平滑移动平均线指标
Moving Average Convergence Divergence - 经典趋势动量指标
向量化实现，支持自定义参数
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class MACD(BaseFactor):
    """MACD指标因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化MACD因子
        Args:
            params: 参数字典，包含fast_period, slow_period, signal_period
                   默认{"fast_period": 12, "slow_period": 26, "signal_period": 9}
        """
        # 处理参数格式
        if params is None:
            fast_period = 12
            slow_period = 26
            signal_period = 9
        elif isinstance(params, dict):
            fast_period = params.get("fast_period", 12)
            slow_period = params.get("slow_period", 26)
            signal_period = params.get("signal_period", 9)
        else:
            fast_period = 12
            slow_period = 26
            signal_period = 9
        
        super().__init__({
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period
        })
        
        # 验证参数
        if not all(isinstance(p, int) and p > 0 for p in [fast_period, slow_period, signal_period]):
            raise ValueError("所有周期必须是正整数")
        
        if fast_period >= slow_period:
            raise ValueError("快线周期必须小于慢线周期")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算MACD指标
        DIF = EMA_fast - EMA_slow
        DEA = EMA(DIF, signal_period)
        HIST = DIF - DEA
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含MACD因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据 (按日期升序排列用于EMA计算)
        data_sorted = data.sort_values('trade_date')
        close_prices = data_sorted['hfq_close']
        
        # 计算快线和慢线EMA
        ema_fast = close_prices.ewm(
            span=self.params["fast_period"], 
            adjust=False
        ).mean()
        
        ema_slow = close_prices.ewm(
            span=self.params["slow_period"], 
            adjust=False
        ).mean()
        
        # 计算DIF (差离值)
        dif = ema_fast - ema_slow
        
        # 计算DEA (信号线) - DIF的EMA
        dea = dif.ewm(
            span=self.params["signal_period"], 
            adjust=False
        ).mean()
        
        # 计算HIST (柱状图) - DIF与DEA的差值
        hist = dif - dea
        
        # 应用全局精度配置
        dif = dif.round(config.get_precision('indicator'))
        dea = dea.round(config.get_precision('indicator'))
        hist = hist.round(config.get_precision('indicator'))
        
        # 添加到结果 (恢复原始排序)
        result['MACD_DIF'] = dif
        result['MACD_DEA'] = dea  
        result['MACD_HIST'] = hist
        
        # 恢复原始排序（最新日期在前）
        result = result.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 数据验证和清理
        numeric_columns = ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']
        for col in numeric_columns:
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算MACD所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'MACD',
            'description': 'MACD指标 - 经典趋势动量指标',
            'category': 'trend_momentum',
            'fast_period': self.params['fast_period'],
            'slow_period': self.params['slow_period'],
            'signal_period': self.params['signal_period'],
            'data_type': 'momentum',
            'calculation_method': 'exponential_moving_average_convergence_divergence',
            'formula': 'DIF=EMA_fast-EMA_slow, DEA=EMA(DIF), HIST=DIF-DEA',
            'output_columns': ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证MACD计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date', 'MACD_DIF', 'MACD_DEA', 'MACD_HIST']
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查MACD值的合理性
            macd_columns = ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']
            for col_name in macd_columns:
                values = result[col_name].dropna()
                
                if len(values) == 0:
                    continue
                
                # MACD值应在合理范围内
                if (abs(values) > 100).any():
                    return False
                
                # 检查是否有无穷大值
                if (values == float('inf')).any() or (values == float('-inf')).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['MACD']


def create_default_macd():
    """创建默认配置的MACD因子实例"""
    return MACD()


def create_custom_macd(fast_period, slow_period, signal_period):
    """创建自定义参数的MACD因子实例"""
    return MACD({
        "fast_period": fast_period, 
        "slow_period": slow_period, 
        "signal_period": signal_period
    })


# 因子测试功能
def test_macd_calculation():
    """测试MACD因子计算功能"""
    print("🧪 测试MACD因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 30,
        'trade_date': pd.date_range('2025-01-01', periods=30),
        'hfq_close': [1.0 + 0.01 * i + 0.005 * (i % 5) for i in range(30)]
    })
    
    # 创建MACD因子
    macd_factor = MACD()
    
    # 计算因子
    result = macd_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - MACD_DIF样例: {result['MACD_DIF'].iloc[:3].tolist()}")
    print(f"   - MACD_DEA样例: {result['MACD_DEA'].iloc[:3].tolist()}")
    print(f"   - MACD_HIST样例: {result['MACD_HIST'].iloc[:3].tolist()}")
    
    # 验证结果
    is_valid = macd_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_macd_calculation()