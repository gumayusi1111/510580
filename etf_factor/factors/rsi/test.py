"""
RSI测试模块
独立的测试和示例功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加路径以导入因子
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from core import RSI


def test_rsi_basic():
    print("🧪 测试RSI基础功能...")
    
    test_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 20,
        'trade_date': pd.date_range('2025-01-01', periods=20),
        'hfq_close': [10.0, 10.1, 9.9, 10.2, 9.8, 10.3, 10.0, 10.4, 10.1, 10.5,
                      10.2, 10.6, 10.3, 10.1, 10.7, 10.4, 10.8, 10.5, 10.2, 10.9]
    })
    
    factor = RSI()
    result = factor.calculate_vectorized(test_data)
    
    print(f"   输入数据: {len(test_data)} 行")
    print(f"   输出数据: {len(result)} 行")
    print(f"   输出列: {list(result.columns)}")
    
    rsi_cols = [col for col in result.columns if col.startswith('RSI_')]
    for col in rsi_cols[:2]:
        print(f"   {col}样例: {result[col].iloc[:3].tolist()}")
    
    is_valid = factor.validate_calculation_result(result)
    print(f"   结果验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    # 检查RSI值范围
    for col in rsi_cols[:2]:
        rsi_values = result[col].dropna()
        if len(rsi_values) > 0:
            in_range = (rsi_values >= 0).all() and (rsi_values <= 100).all()
            print(f"   {col}范围检查: {'✅' if in_range else '❌'} [{rsi_values.min():.1f}, {rsi_values.max():.1f}]")
    
    return result


def run_all_tests():
    print("📊 RSI因子模块化测试")
    print("=" * 50)
    
    try:
        test_rsi_basic()
        print("\n✅ 所有测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()