"""
MA_DIFF - 移动均线差值因子
Moving Average Difference - 不同周期均线间的差值
向量化实现，支持多组差值计算
文件限制: <200行
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_factor import BaseFactor
from src.config import config


class MA_DIFF(BaseFactor):
    """移动均线差值因子 - 向量化实现"""
    
    def __init__(self, params=None):
        """
        初始化MA_DIFF因子
        Args:
            params: 参数字典，包含pairs字段，默认{("pairs": [(5,10), (5,20), (10,20), (10,60)])}
        """
        # 处理参数格式
        if params is None:
            pairs = [(5, 10), (5, 20), (10, 20), (10, 60)]
        elif isinstance(params, dict):
            pairs = params.get("pairs", [(5, 10), (5, 20), (10, 20), (10, 60)])
        elif isinstance(params, list):
            pairs = params
        else:
            pairs = [(5, 10), (5, 20), (10, 20), (10, 60)]
        
        super().__init__({"pairs": pairs})
        
        # 验证参数
        if not isinstance(pairs, list) or len(pairs) == 0:
            raise ValueError("pairs必须是非空列表")
        
        for pair in pairs:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError("每个pair必须是包含2个元素的元组或列表")
            
            if not all(isinstance(p, int) and p > 0 for p in pair):
                raise ValueError("所有周期必须是正整数")
                
            if pair[0] >= pair[1]:
                raise ValueError(f"短周期({pair[0]})必须小于长周期({pair[1]})")
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算移动均线差值
        MA_DIFF = 短周期MA - 长周期MA
        
        Args:
            data: 包含价格数据的DataFrame
        Returns:
            包含MA_DIFF因子的DataFrame
        """
        # 基础结果DataFrame
        result = data[['ts_code', 'trade_date']].copy()
        
        # 获取收盘价数据
        close_prices = data['hfq_close']
        
        # 预计算所有需要的MA值
        ma_cache = {}
        all_periods = set()
        for short, long in self.params["pairs"]:
            all_periods.add(short)
            all_periods.add(long)
        
        # 向量化计算所有需要的MA
        for period in all_periods:
            ma_values = close_prices.rolling(
                window=period,
                min_periods=1
            ).mean()
            ma_cache[period] = ma_values
        
        # 计算所有差值对
        for short, long in self.params["pairs"]:
            column_name = f'MA_DIFF_{short}_{long}'
            
            # 计算差值：短周期MA - 长周期MA
            diff_values = ma_cache[short] - ma_cache[long]
            
            # 应用全局精度配置
            diff_values = diff_values.round(config.get_precision('price'))
            
            result[column_name] = diff_values
        
        # 数据验证和清理
        numeric_columns = [col for col in result.columns if col.startswith('MA_DIFF_')]
        for col in numeric_columns:
            # MA差值可以为负数，使用更宽松的验证
            result[col] = result[col].replace([float('inf'), -float('inf')], pd.NA)
            
        return result
    
    def get_required_columns(self) -> list:
        """获取计算MA_DIFF所需的数据列"""
        return ['ts_code', 'trade_date', 'hfq_close']
    
    def get_factor_info(self) -> dict:
        """获取因子信息"""
        return {
            'name': 'MA_DIFF',
            'description': '移动均线差值 - 不同周期均线间的差值',
            'category': 'moving_average',
            'pairs': self.params['pairs'],
            'data_type': 'price_diff',
            'calculation_method': 'moving_average_difference',
            'formula': 'MA_DIFF = 短周期MA - 长周期MA',
            'output_columns': [f'MA_DIFF_{p[0]}_{p[1]}' for p in self.params['pairs']]
        }
    
    def validate_calculation_result(self, result: pd.DataFrame) -> bool:
        """验证MA_DIFF计算结果的合理性"""
        try:
            # 检查输出列
            expected_columns = ['ts_code', 'trade_date'] + [f'MA_DIFF_{p[0]}_{p[1]}' for p in self.params['pairs']]
            if not all(col in result.columns for col in expected_columns):
                return False
            
            # 检查数据行数
            if len(result) == 0:
                return False
            
            # 检查MA_DIFF值的合理性
            for short, long in self.params['pairs']:
                col_name = f'MA_DIFF_{short}_{long}'
                diff_values = result[col_name].dropna()
                
                if len(diff_values) == 0:
                    continue
                
                # MA差值应在合理范围内（可以为负）
                if (abs(diff_values) > 1000).any():
                    return False
                
                # 检查是否有无穷大值
                if (diff_values == float('inf')).any() or (diff_values == float('-inf')).any():
                    return False
            
            return True
            
        except Exception:
            return False


# 因子自动注册机制所需的导出
__all__ = ['MA_DIFF']


def create_default_ma_diff():
    """创建默认配置的MA_DIFF因子实例"""
    return MA_DIFF()


def create_custom_ma_diff(pairs):
    """创建自定义差值对的MA_DIFF因子实例"""
    return MA_DIFF({"pairs": pairs})


# 因子测试功能
def test_ma_diff_calculation():
    """测试MA_DIFF因子计算功能"""
    print("🧪 测试MA_DIFF因子计算...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 10,
        'trade_date': pd.date_range('2025-01-01', periods=10),
        'hfq_close': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })
    
    # 创建MA_DIFF因子
    ma_diff_factor = MA_DIFF({"pairs": [(3, 5), (5, 10)]})
    
    # 计算因子
    result = ma_diff_factor.calculate_vectorized(test_data)
    
    print(f"   - 输入数据: {len(test_data)} 行")
    print(f"   - 输出数据: {len(result)} 行")
    print(f"   - 输出列: {list(result.columns)}")
    print(f"   - MA_DIFF_3_5样例: {result['MA_DIFF_3_5'].iloc[:3].tolist()}")
    print(f"   - MA_DIFF_5_10样例: {result['MA_DIFF_5_10'].iloc[:3].tolist()}")
    
    # 验证结果
    is_valid = ma_diff_factor.validate_calculation_result(result)
    print(f"   - 结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return result


if __name__ == "__main__":
    test_ma_diff_calculation()