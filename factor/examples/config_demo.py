"""
全局配置演示
展示如何使用全局配置系统
"""

import sys
import os
sys.path.append('..')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.config import config

def demo_global_config():
    """演示全局配置功能"""
    
    print("🔧 全局配置系统演示")
    print("=" * 50)
    
    # 1. 基本配置获取
    print("1. 基本配置获取:")
    print(f"   - 价格精度: {config.get_precision('price')}")
    print(f"   - 百分比精度: {config.get_precision('percentage')}")
    print(f"   - ETF代码: {config.get('etf_info.symbol')}")
    print(f"   - 调试模式: {config.is_debug_mode()}")
    
    # 2. 创建示例数据
    print("\n2. 数据格式化演示:")
    sample_data = pd.DataFrame({
        'ts_code': ['510580.SH'] * 5,
        'trade_date': pd.date_range('2025-09-01', periods=5),
        'close_price': [3.123456789, 3.234567890, 3.345678901, 3.456789012, 3.567890123],
        'volume': [123456.789, 234567.890, 345678.901, 456789.012, 567890.123],
        'daily_return_pct': [0.123456, -0.234567, 0.345678, -0.456789, 0.567890],
        'rsi_indicator': [65.123456789, 45.234567890, 75.345678901, 35.456789012, 55.567890123]
    })
    
    print("   原始数据:")
    print(sample_data.head(2))
    
    # 3. 应用全局格式化
    print("\n3. 全局格式化后:")
    formatted_data = config.format_dataframe(sample_data, {
        'close_price': 'price',
        'volume': 'statistics', 
        'daily_return_pct': 'percentage',
        'rsi_indicator': 'indicator'
    })
    print(formatted_data.head(2))
    
    # 4. 数值格式化
    print("\n4. 单个数值格式化:")
    test_value = 3.123456789
    print(f"   - 原值: {test_value}")
    print(f"   - 价格格式: {config.format_number(test_value, 'price')}")
    print(f"   - 百分比格式: {config.format_number(test_value, 'percentage')}")
    print(f"   - 指标格式: {config.format_number(test_value, 'indicator')}")
    
    # 5. 数据验证
    print("\n5. 数据范围验证:")
    test_prices = pd.Series([3.1, -1.0, 99999.0, 2.5])  # 包含异常值
    validated_prices = config.validate_data_range(test_prices, 'price')
    print(f"   - 原始价格: {test_prices.tolist()}")
    print(f"   - 验证后: {validated_prices.tolist()}")
    
    # 6. 配置信息总览
    print("\n6. 配置信息总览:")
    etf_info = config.get_etf_info()
    print(f"   - ETF名称: {etf_info.get('name')}")
    print(f"   - 交易所: {etf_info.get('exchange')}")
    print(f"   - 交易时间: {etf_info.get('trading_hours', {}).get('start')} - {etf_info.get('trading_hours', {}).get('end')}")
    
    # 7. 文件命名模板
    print("\n7. 文件命名模板:")
    factor_template = config.get_file_naming_template('factor_file')
    print(f"   - 因子文件: {factor_template}")
    
    # 8. 缓存配置
    print("\n8. 缓存配置:")
    cache_config = config.get_cache_config()
    print(f"   - 缓存键长度: {cache_config['key_length']}")
    print(f"   - 压缩: {cache_config['compression']}")
    
    print("\n✅ 全局配置演示完成")
    print("💡 配置文件位置: config/global.yaml")

if __name__ == "__main__":
    demo_global_config()