#!/usr/bin/env python3
"""
检查510580.SH数据完整性
对比Tushare官方数据，确认是否有遗漏
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
import numpy as np

def check_data_completeness():
    """检查数据完整性"""
    print("🔍 检查510580.SH数据完整性...")
    print("=" * 60)
    
    # 1. 读取本地数据
    print("📁 读取本地数据...")
    local_data_path = "/Users/wenbai/Desktop/singleetfs/data/510580_SH_hfq_data.csv"
    
    try:
        local_data = pd.read_csv(local_data_path)
        local_data['trade_date'] = pd.to_datetime(local_data['trade_date'], format='%Y%m%d')
        local_data = local_data.sort_values('trade_date')
        
        print(f"   本地数据行数: {len(local_data)}")
        print(f"   本地数据起始: {local_data['trade_date'].min().strftime('%Y-%m-%d')}")
        print(f"   本地数据结束: {local_data['trade_date'].max().strftime('%Y-%m-%d')}")
        print()
        
    except Exception as e:
        print(f"❌ 读取本地数据失败: {e}")
        return False
    
    # 2. 获取Tushare数据进行对比
    print("🌐 连接Tushare获取官方数据...")
    
    try:
        # 初始化tushare (需要token)
        # 这里假设token已经设置，如果没有请先设置
        pro = ts.pro_api()
        
        # 获取510580.SH的完整历史数据
        tushare_data = pro.daily(
            ts_code='510580.SH',
            start_date='20180901',  # 从ETF可能的上市日期开始
            end_date=datetime.now().strftime('%Y%m%d')
        )
        
        if tushare_data.empty:
            print("⚠️  Tushare未返回数据，可能是token问题或网络问题")
            return False
            
        tushare_data['trade_date'] = pd.to_datetime(tushare_data['trade_date'], format='%Y%m%d')
        tushare_data = tushare_data.sort_values('trade_date')
        
        print(f"   Tushare数据行数: {len(tushare_data)}")
        print(f"   Tushare数据起始: {tushare_data['trade_date'].min().strftime('%Y-%m-%d')}")
        print(f"   Tushare数据结束: {tushare_data['trade_date'].max().strftime('%Y-%m-%d')}")
        print()
        
    except Exception as e:
        print(f"❌ 获取Tushare数据失败: {e}")
        print("   可能原因:")
        print("   1. 没有设置Tushare token")
        print("   2. 网络连接问题")
        print("   3. API调用限制")
        print("\n🔄 改为检查本地数据的内在完整性...")
        return check_local_data_integrity(local_data)
    
    # 3. 数据对比分析
    print("📊 数据完整性对比分析...")
    
    # 日期范围对比
    local_start = local_data['trade_date'].min()
    local_end = local_data['trade_date'].max()
    tushare_start = tushare_data['trade_date'].min()
    tushare_end = tushare_data['trade_date'].max()
    
    print(f"📅 日期范围对比:")
    print(f"   本地起始日期: {local_start.strftime('%Y-%m-%d')}")
    print(f"   官方起始日期: {tushare_start.strftime('%Y-%m-%d')}")
    print(f"   差异: {(local_start - tushare_start).days} 天")
    print()
    print(f"   本地结束日期: {local_end.strftime('%Y-%m-%d')}")
    print(f"   官方结束日期: {tushare_end.strftime('%Y-%m-%d')}")
    print(f"   差异: {(local_end - tushare_end).days} 天")
    print()
    
    # 数据量对比
    print(f"📈 数据量对比:")
    print(f"   本地数据: {len(local_data)} 条")
    print(f"   官方数据: {len(tushare_data)} 条")
    print(f"   差异: {len(local_data) - len(tushare_data)} 条")
    print()
    
    # 寻找缺失的交易日
    local_dates = set(local_data['trade_date'].dt.strftime('%Y%m%d'))
    tushare_dates = set(tushare_data['trade_date'].dt.strftime('%Y%m%d'))
    
    missing_dates = tushare_dates - local_dates
    extra_dates = local_dates - tushare_dates
    
    if missing_dates:
        print(f"❌ 本地缺失的交易日 ({len(missing_dates)} 个):")
        missing_sorted = sorted(list(missing_dates))
        for date in missing_sorted[:10]:  # 只显示前10个
            print(f"   {date[:4]}-{date[4:6]}-{date[6:]}")
        if len(missing_sorted) > 10:
            print(f"   ... 还有 {len(missing_sorted)-10} 个日期")
        print()
    
    if extra_dates:
        print(f"⚠️  本地多出的日期 ({len(extra_dates)} 个):")
        extra_sorted = sorted(list(extra_dates))
        for date in extra_sorted[:10]:
            print(f"   {date[:4]}-{date[4:6]}-{date[6:]}")
        if len(extra_sorted) > 10:
            print(f"   ... 还有 {len(extra_sorted)-10} 个日期")
        print()
    
    # 数据质量评估
    completeness_score = (len(local_data) / len(tushare_data)) * 100 if len(tushare_data) > 0 else 0
    
    print("🎯 数据完整性评估:")
    print(f"   完整性得分: {completeness_score:.2f}%")
    
    if completeness_score >= 99:
        print("   评级: ✅ 优秀 (数据基本完整)")
    elif completeness_score >= 95:
        print("   评级: ✅ 良好 (少量数据缺失)")
    elif completeness_score >= 90:
        print("   评级: ⚠️  一般 (部分数据缺失)")
    else:
        print("   评级: ❌ 较差 (大量数据缺失)")
    
    # 近期数据检查
    print("\n🔍 近期数据检查:")
    recent_days = 30
    recent_cutoff = datetime.now() - timedelta(days=recent_days)
    
    local_recent = local_data[local_data['trade_date'] >= recent_cutoff]
    tushare_recent = tushare_data[tushare_data['trade_date'] >= recent_cutoff]
    
    print(f"   近{recent_days}天本地数据: {len(local_recent)} 条")
    print(f"   近{recent_days}天官方数据: {len(tushare_recent)} 条")
    
    recent_completeness = (len(local_recent) / len(tushare_recent)) * 100 if len(tushare_recent) > 0 else 0
    print(f"   近期完整性: {recent_completeness:.1f}%")
    
    return completeness_score >= 95

def check_local_data_integrity(local_data):
    """检查本地数据内在完整性"""
    print("🔍 检查本地数据内在完整性...")
    print("=" * 40)
    
    # 1. 时间连续性检查
    print("📅 时间连续性检查:")
    local_data = local_data.sort_values('trade_date')
    dates = local_data['trade_date']
    
    # 计算日期间隔
    date_diffs = dates.diff().dt.days
    
    # 正常交易日间隔应该是1天（工作日）或3天（跨周末）
    normal_gaps = date_diffs[(date_diffs >= 1) & (date_diffs <= 3)]
    abnormal_gaps = date_diffs[date_diffs > 3]
    
    print(f"   总交易日: {len(local_data)} 天")
    print(f"   正常间隔: {len(normal_gaps)} 个")
    print(f"   异常间隔: {len(abnormal_gaps)} 个")
    
    if len(abnormal_gaps) > 0:
        print("   异常间隔详情:")
        for i, gap in abnormal_gaps.items():
            if pd.notna(gap):
                date = dates.iloc[i]
                print(f"     {date.strftime('%Y-%m-%d')}: 间隔{int(gap)}天")
    
    # 2. 数据质量检查
    print(f"\n📊 数据质量检查:")
    print(f"   空值检查:")
    for col in ['hfq_open', 'hfq_high', 'hfq_low', 'hfq_close', 'vol']:
        null_count = local_data[col].isna().sum()
        print(f"     {col}: {null_count} 个空值")
    
    # 3. 价格合理性检查
    print(f"\n💰 价格数据合理性:")
    close_prices = local_data['hfq_close']
    print(f"   价格范围: {close_prices.min():.3f} ~ {close_prices.max():.3f}")
    print(f"   最新价格: {close_prices.iloc[-1]:.3f}")
    print(f"   最早价格: {close_prices.iloc[0]:.3f}")
    
    # 价格异常检查（日涨跌幅超过20%可能异常）
    price_changes = close_prices.pct_change()
    extreme_changes = price_changes[abs(price_changes) > 0.2]
    
    if len(extreme_changes) > 0:
        print(f"   极端涨跌幅: {len(extreme_changes)} 次")
        print("   详情:")
        for i, change in extreme_changes.items():
            date = local_data.iloc[i]['trade_date']
            print(f"     {date.strftime('%Y-%m-%d')}: {change:.2%}")
    else:
        print("   ✅ 无异常涨跌幅")
    
    # 4. ETF基本信息
    print(f"\n📋 ETF基本信息:")
    total_days = (dates.max() - dates.min()).days
    trading_days = len(local_data)
    trading_ratio = trading_days / total_days * 100
    
    print(f"   数据跨度: {total_days} 天")
    print(f"   交易天数: {trading_days} 天") 
    print(f"   交易日比例: {trading_ratio:.1f}%")
    
    # 估算完整性
    # 一年约250个交易日，7年约1750个交易日
    years = total_days / 365
    expected_trading_days = years * 250
    estimated_completeness = (trading_days / expected_trading_days) * 100
    
    print(f"   预期交易日: {expected_trading_days:.0f} 天")
    print(f"   估算完整性: {estimated_completeness:.1f}%")
    
    print(f"\n🎯 本地数据评估:")
    if estimated_completeness >= 95:
        print("   ✅ 数据质量良好，基本完整")
        return True
    elif estimated_completeness >= 90:
        print("   ⚠️  数据基本完整，可能有少量缺失")
        return True
    else:
        print("   ❌ 数据可能有较多缺失")
        return False

def get_tushare_info():
    """获取Tushare连接信息"""
    print("🔧 Tushare配置检查:")
    
    try:
        import tushare as ts
        
        # 尝试获取token
        try:
            pro = ts.pro_api()
            # 尝试一个简单的查询来验证token
            test_data = pro.trade_cal(exchange='', start_date='20240101', end_date='20240102')
            if not test_data.empty:
                print("   ✅ Tushare token有效")
                return True
            else:
                print("   ❌ Tushare token可能无效")
                return False
        except Exception as e:
            print(f"   ❌ Tushare token问题: {e}")
            print("   💡 请设置环境变量或通过 ts.set_token() 设置")
            return False
            
    except ImportError:
        print("   ❌ 未安装tushare: pip install tushare")
        return False

if __name__ == "__main__":
    print("🚀 510580.SH ETF 数据完整性检查")
    print("=" * 60)
    
    # 检查Tushare配置
    tushare_available = get_tushare_info()
    print()
    
    # 执行完整性检查
    if tushare_available:
        result = check_data_completeness()
    else:
        # 没有Tushare时，仅检查本地数据完整性
        local_data = pd.read_csv("/Users/wenbai/Desktop/singleetfs/data/510580_SH_hfq_data.csv")
        local_data['trade_date'] = pd.to_datetime(local_data['trade_date'], format='%Y%m%d')
        result = check_local_data_integrity(local_data)
    
    print("\n" + "=" * 60)
    print("📊 最终结论:")
    
    if result:
        print("✅ 数据完整性良好，可以正常进行因子计算")
    else:
        print("⚠️  建议补充缺失数据以提高因子计算准确性")
    
    print("\n💡 建议:")
    print("   • 定期更新数据以保持最新")
    print("   • 监控数据质量，及时发现异常")
    print("   • 考虑设置自动化数据更新任务")