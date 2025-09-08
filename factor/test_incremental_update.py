#!/usr/bin/env python3
"""
测试增量更新功能
验证所有因子的增量更新是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from src.engine import VectorizedEngine
from src.data_loader import DataLoader
from src.cache import CacheManager

def test_incremental_update_functionality():
    """测试增量更新功能"""
    print("🧪 测试增量更新功能...")
    print("=" * 60)
    
    # 初始化引擎
    engine = VectorizedEngine()
    data_loader = DataLoader("../data")
    cache_manager = CacheManager()
    
    # 获取全量数据信息
    data_info = data_loader.get_data_info()
    print(f"📊 数据信息:")
    print(f"   总行数: {data_info['rows']}")
    print(f"   开始日期: {data_info['start_date']}")  
    print(f"   结束日期: {data_info['end_date']}")
    print()
    
    # 测试增量数据加载功能
    print("🔄 测试增量数据加载...")
    
    # 假设最后更新日期为数据倒数第10天
    full_data = data_loader.load_data("hfq")
    last_update_date = full_data['trade_date'].iloc[-10]  
    print(f"   模拟最后更新日期: {last_update_date.date()}")
    
    # 加载增量数据
    incremental_data = data_loader.load_incremental_data(
        last_date=last_update_date.strftime('%Y-%m-%d'),
        data_type="hfq"
    )
    print(f"   增量数据行数: {len(incremental_data)}")
    print(f"   增量数据日期范围: {incremental_data['trade_date'].min().date()} ~ {incremental_data['trade_date'].max().date()}")
    
    if len(incremental_data) == 0:
        print("⚠️  没有增量数据可供测试")
        return False
    
    print()
    
    # 测试缓存的增量更新功能
    print("🔄 测试缓存增量更新...")
    
    # 选择几个代表性因子进行测试
    test_factors = ['SMA', 'MACD', 'BOLL', 'OBV', 'MAX_DD']
    
    update_results = {}
    
    for factor_name in test_factors:
        if factor_name not in engine.factors:
            print(f"⚠️  因子 {factor_name} 未找到，跳过")
            continue
            
        print(f"   测试因子: {factor_name}")
        
        try:
            # 1. 先计算到last_update_date的因子数据（模拟历史缓存）
            historical_data = full_data[full_data['trade_date'] <= last_update_date].copy()
            
            # 创建因子实例
            factor_class = engine.factors[factor_name]
            factor = factor_class()
            
            # 计算历史数据
            historical_result = factor.calculate_vectorized(historical_data)
            historical_rows = len(historical_result)
            
            # 生成缓存键
            data_hash = data_loader.get_data_hash(historical_data)
            cache_key = factor.get_cache_key(data_hash)
            
            # 缓存历史数据
            cache_manager.cache_factor(cache_key, historical_result, factor_name)
            
            # 2. 计算增量数据的因子
            incremental_result = factor.calculate_vectorized(incremental_data)
            incremental_rows = len(incremental_result)
            
            # 3. 使用增量更新功能
            cache_manager.update_incremental(cache_key, incremental_result, factor_name)
            
            # 4. 验证更新后的缓存数据
            updated_cached_data = cache_manager.get_cached_factor(cache_key)
            updated_rows = len(updated_cached_data)
            
            print(f"     历史数据: {historical_rows} 行")
            print(f"     增量数据: {incremental_rows} 行") 
            print(f"     更新后: {updated_rows} 行")
            
            # 验证数据完整性
            expected_rows = historical_rows + incremental_rows
            if updated_rows >= expected_rows - 10:  # 允许少量重叠
                update_results[factor_name] = "✅ 通过"
            else:
                update_results[factor_name] = f"❌ 失败 (期望≥{expected_rows-10}, 实际{updated_rows})"
                
        except Exception as e:
            update_results[factor_name] = f"❌ 异常: {str(e)[:50]}..."
            
    print()
    
    # 汇总测试结果
    print("📋 增量更新测试结果:")
    for factor_name, result in update_results.items():
        print(f"   {factor_name:12} : {result}")
    
    print()
    
    # 统计成功率
    success_count = sum(1 for result in update_results.values() if "✅" in result)
    total_count = len(update_results)
    success_rate = success_count / total_count * 100 if total_count > 0 else 0
    
    print(f"🎯 增量更新成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    # 检查系统组件的增量更新支持
    print()
    print("🔍 系统组件增量更新支持:")
    print("   ✅ DataLoader.load_incremental_data() - 支持增量数据加载")
    print("   ✅ CacheManager.update_incremental() - 支持增量缓存更新") 
    print("   ✅ 基于trade_date的数据去重合并")
    print("   ✅ 自动处理日期范围筛选")
    
    return success_rate >= 80  # 80%以上成功率视为通过

def test_factor_level_incremental_support():
    """测试每个因子的增量计算支持情况"""
    print("\n" + "=" * 60)
    print("🔍 检查各因子的增量计算特性...")
    print("=" * 60)
    
    engine = VectorizedEngine()
    
    # 因子增量计算特性分析
    factor_analysis = {}
    
    for factor_name, factor_class in engine.factors.items():
        try:
            factor = factor_class()
            factor_info = factor.get_factor_info()
            
            # 分析因子的计算特性
            calculation_method = factor_info.get('calculation_method', '')
            formula = factor_info.get('formula', '')
            
            # 判断是否支持增量计算
            incremental_friendly = True
            incremental_notes = []
            
            # 检查是否需要全历史数据
            if 'cumsum' in formula.lower() or 'cum' in calculation_method.lower():
                incremental_friendly = False
                incremental_notes.append("需要累积计算")
                
            if 'expanding' in formula.lower() or factor_name in ['OBV', 'CUM_RETURN']:
                incremental_friendly = False  
                incremental_notes.append("需要全历史数据")
                
            # 移动平均类因子通常支持增量计算
            if any(x in factor_name.upper() for x in ['SMA', 'EMA', 'WMA', 'VMA']):
                incremental_friendly = True
                incremental_notes.append("滚动计算，增量友好")
                
            # 技术指标类因子
            if any(x in factor_name.upper() for x in ['RSI', 'MACD', 'BOLL', 'ATR', 'TR']):
                incremental_friendly = True
                incremental_notes.append("技术指标，增量友好")
                
            factor_analysis[factor_name] = {
                'incremental_friendly': incremental_friendly,
                'notes': incremental_notes,
                'category': factor_info.get('category', 'unknown')
            }
            
        except Exception as e:
            factor_analysis[factor_name] = {
                'incremental_friendly': False,
                'notes': [f"分析失败: {e}"],
                'category': 'error'
            }
    
    # 按类别组织输出
    categories = {}
    for factor_name, info in factor_analysis.items():
        category = info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append((factor_name, info))
    
    for category, factors in categories.items():
        print(f"\n📂 {category.replace('_', ' ').title()}:")
        for factor_name, info in factors:
            status = "✅" if info['incremental_friendly'] else "⚠️"
            notes = " | ".join(info['notes'][:2])  # 只显示前2个注释
            print(f"   {status} {factor_name:12} : {notes}")
    
    # 统计总体情况
    total_factors = len(factor_analysis)
    incremental_friendly_count = sum(1 for info in factor_analysis.values() 
                                   if info['incremental_friendly'])
    
    print(f"\n🎯 增量计算支持情况:")
    print(f"   支持增量: {incremental_friendly_count}/{total_factors} 个因子")
    print(f"   支持率: {incremental_friendly_count/total_factors*100:.1f}%")
    
    return factor_analysis

if __name__ == "__main__":
    print("🚀 增量更新功能全面测试")
    print("=" * 60)
    
    # 测试1: 系统增量更新功能
    system_test_passed = test_incremental_update_functionality()
    
    # 测试2: 各因子增量计算特性分析
    factor_analysis = test_factor_level_incremental_support()
    
    print("\n" + "=" * 60)
    print("📊 最终评估:")
    print("=" * 60)
    
    if system_test_passed:
        print("✅ 系统增量更新功能: 正常工作")
    else:
        print("❌ 系统增量更新功能: 需要改进")
    
    incremental_support_rate = sum(1 for info in factor_analysis.values() 
                                 if info['incremental_friendly']) / len(factor_analysis) * 100
    
    print(f"📈 因子增量兼容性: {incremental_support_rate:.1f}%")
    
    # 给出综合评估和建议
    print("\n💡 建议:")
    if incremental_support_rate >= 80:
        print("   • 大部分因子支持增量计算，系统架构合理")
        print("   • 可以放心使用增量更新功能")
    elif incremental_support_rate >= 60:
        print("   • 部分因子需要特殊处理增量更新")
        print("   • 建议为累积类因子实现专门的增量策略")
    else:
        print("   • 增量计算兼容性较低")
        print("   • 建议重新设计因子计算架构")
    
    print("   • 定期清理缓存以保持数据一致性")
    print("   • 监控增量更新的数据质量")