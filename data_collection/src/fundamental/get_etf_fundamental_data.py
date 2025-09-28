#!/usr/bin/env python3
"""
获取ETF基本面数据并存储到新的目录结构
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 设置token
TOKEN = "a44b1b3296e72fa73c18a1d739a6b5c7a6425351601bce03e34533b0"
ts.set_token(TOKEN)
pro = ts.pro_api()

def get_etf_nav_data(etf_code, start_date=None, end_date=None):
    """获取ETF净值数据"""
    if start_date is None:
        start_date = "20220101"
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')

    print(f"📊 获取 {etf_code} 净值数据...")
    nav_data = pro.fund_nav(ts_code=etf_code, start_date=start_date, end_date=end_date)

    if not nav_data.empty:
        # 统一使用trade_date列名
        nav_data['trade_date'] = pd.to_datetime(nav_data['nav_date']).dt.strftime('%Y%m%d')
        nav_data = nav_data.drop('nav_date', axis=1)
        nav_data = nav_data.sort_values('trade_date', ascending=False).reset_index(drop=True)

        # 计算净值相关因子
        nav_data['NAV_RETURN'] = nav_data['unit_nav'].pct_change()  # 净值收益率
        nav_data['NAV_MA_5'] = nav_data['unit_nav'].rolling(5).mean()   # 净值5日均线
        nav_data['NAV_MA_20'] = nav_data['unit_nav'].rolling(20).mean() # 净值20日均线
        nav_data['NAV_STD_20'] = nav_data['unit_nav'].rolling(20).std() # 净值波动率

        print(f"✅ 净值数据: {len(nav_data)}条记录")
        return nav_data
    return pd.DataFrame()

def get_index_valuation_data(index_code, start_date=None, end_date=None):
    """获取指数估值数据"""
    if start_date is None:
        start_date = "20220101"
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')

    print(f"📈 获取 {index_code} 指数估值数据...")
    index_data = pro.index_dailybasic(
        ts_code=index_code,
        start_date=start_date,
        end_date=end_date,
        fields='ts_code,trade_date,pe,pb,pe_ttm,pb_mrq,turnover_rate,volume_ratio'
    )

    if not index_data.empty:
        # 确保trade_date格式统一
        index_data['trade_date'] = pd.to_datetime(index_data['trade_date']).dt.strftime('%Y%m%d')
        index_data = index_data.sort_values('trade_date', ascending=False).reset_index(drop=True)

        # 计算估值分位数
        index_data['PE_PERCENTILE'] = index_data['pe'].rank(pct=True)
        index_data['PB_PERCENTILE'] = index_data['pb'].rank(pct=True)

        # 计算估值移动平均
        index_data['PE_MA_20'] = index_data['pe'].rolling(20).mean()
        index_data['PB_MA_20'] = index_data['pb'].rolling(20).mean()

        print(f"✅ 指数估值: {len(index_data)}条记录")
        return index_data
    return pd.DataFrame()

def get_etf_share_data(etf_code, start_date=None, end_date=None):
    """获取ETF份额数据"""
    if start_date is None:
        start_date = "20220101"
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')

    print(f"💼 获取 {etf_code} 份额数据...")
    share_data = pro.fund_share(ts_code=etf_code, start_date=start_date, end_date=end_date)

    if not share_data.empty:
        # 确保trade_date格式统一
        share_data['trade_date'] = pd.to_datetime(share_data['trade_date']).dt.strftime('%Y%m%d')
        share_data = share_data.sort_values('trade_date', ascending=False).reset_index(drop=True)

        # 计算份额变化相关因子
        share_data['SHARE_CHANGE'] = share_data['fd_share'].diff()
        share_data['SHARE_CHANGE_PCT'] = share_data['fd_share'].pct_change()
        share_data['SHARE_MA_5'] = share_data['fd_share'].rolling(5).mean()

        print(f"✅ 份额数据: {len(share_data)}条记录")
        return share_data
    return pd.DataFrame()

def get_macro_data():
    """获取宏观数据"""
    print("🌍 获取宏观经济数据...")

    # 获取利率数据
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y%m%d')

    shibor_data = pro.shibor(start_date=start_date, end_date=end_date)
    if not shibor_data.empty:
        # 统一使用trade_date列名和格式
        shibor_data['trade_date'] = pd.to_datetime(shibor_data['date']).dt.strftime('%Y%m%d')
        shibor_data = shibor_data.drop('date', axis=1)
        shibor_data = shibor_data.sort_values('trade_date', ascending=False).reset_index(drop=True)
        print(f"✅ 利率数据: {len(shibor_data)}条记录")

    return shibor_data

def save_fundamental_data():
    """保存所有基本面数据"""

    # ETF和对应指数的映射
    etf_index_mapping = {
        '510300.SH': '000300.SH',  # 沪深300ETF -> 沪深300指数
        '510580.SH': '000905.SH',  # 中证500ETF -> 中证500指数
        '513180.SH': 'HSTECH.HI'   # 恒生科技ETF -> 恒生科技指数
    }

    # 获取项目根目录
    script_dir = Path(__file__).parent.parent.parent.parent
    base_path = script_dir / "etf_factor" / "factor_data"

    for etf_code, index_code in etf_index_mapping.items():
        print(f"\n{'='*60}")
        print(f"🎯 处理 {etf_code} (对应指数: {index_code})")
        print(f"{'='*60}")

        etf_num = etf_code.split('.')[0]  # 提取ETF数字代码
        fund_dir = base_path / "fundamental" / etf_num

        # 1. 获取ETF净值数据
        nav_data = get_etf_nav_data(etf_code)
        if not nav_data.empty:
            nav_file = fund_dir / "ETF_NAV.csv"
            nav_data.to_csv(nav_file, index=False, encoding='utf-8')
            print(f"💾 净值数据保存到: {nav_file}")

        # 2. 获取指数估值数据
        index_data = get_index_valuation_data(index_code)
        if not index_data.empty:
            index_file = fund_dir / "INDEX_VALUATION.csv"
            index_data.to_csv(index_file, index=False, encoding='utf-8')
            print(f"💾 指数估值保存到: {index_file}")

        # 3. 获取ETF份额数据
        share_data = get_etf_share_data(etf_code)
        if not share_data.empty:
            share_file = fund_dir / "ETF_SHARE.csv"
            share_data.to_csv(share_file, index=False, encoding='utf-8')
            print(f"💾 份额数据保存到: {share_file}")

    # 4. 获取宏观数据（全局）
    print(f"\n{'='*60}")
    print("🌍 处理宏观经济数据")
    print(f"{'='*60}")

    macro_data = get_macro_data()
    if not macro_data.empty:
        macro_file = base_path / "macro" / "SHIBOR_RATES.csv"
        macro_data.to_csv(macro_file, index=False, encoding='utf-8')
        print(f"💾 宏观数据保存到: {macro_file}")

    print(f"\n🎉 所有ETF基本面数据获取完成!")

if __name__ == "__main__":
    save_fundamental_data()