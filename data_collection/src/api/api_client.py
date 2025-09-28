#!/usr/bin/env python3
"""
Tushare API客户端模块
"""

import sys
import os
import time
import traceback
import tushare as ts  # cspell:ignore tushare

# 添加配置路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import MAX_RETRY_TIMES, REQUEST_DELAY


class TushareClient:
    """Tushare API客户端"""
    
    def __init__(self, token):
        """初始化客户端"""
        self.token = token
        self.pro_api = self._setup_api()
    
    def _setup_api(self):
        """设置tushare API"""  # cspell:ignore tushare
        ts.set_token(self.token)
        return ts.pro_api()
    
    def fetch_with_retry(self, api_method, **kwargs):
        """带重试机制的API调用"""
        for attempt in range(MAX_RETRY_TIMES):
            try:
                time.sleep(REQUEST_DELAY)  # API请求间隔
                return api_method(**kwargs)
            except Exception as e:
                print(f"API调用失败 (尝试 {attempt + 1}/{MAX_RETRY_TIMES}): {e}")
                if attempt == MAX_RETRY_TIMES - 1:
                    raise e
                time.sleep(1 * (attempt + 1))  # 递增等待时间
        return None
    
    def fetch_fund_daily(self, ts_code, start_date, end_date):
        """获取基金日线数据"""
        print(f"获取基金日线数据: {ts_code} ({start_date} - {end_date})")
        return self.fetch_with_retry(
            self.pro_api.fund_daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
    
    def fetch_fund_adj(self, ts_code, start_date, end_date):
        """获取基金复权因子"""
        print(f"获取基金复权因子: {ts_code} ({start_date} - {end_date})")
        return self.fetch_with_retry(
            self.pro_api.fund_adj,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
    
    def fetch_etf_data(self, etf_code, start_date, end_date):
        """获取ETF完整数据"""
        print(f"开始获取 {etf_code} 数据...")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        try:
            # 获取复权因子
            print("\n1. 获取基金复权因子...")
            adj_data = self.fetch_fund_adj(etf_code, start_date, end_date)
            if adj_data is None or len(adj_data) == 0:
                print("警告: 未获取到复权因子数据")
                return None, None
            print(f"获取到 {len(adj_data)} 条复权因子数据")
            
            # 获取日线数据
            print("\n2. 获取基金日线数据...")
            daily_data = self.fetch_fund_daily(etf_code, start_date, end_date)
            if daily_data is None or len(daily_data) == 0:
                print("警告: 未获取到日线数据")
                return adj_data, None
            print(f"获取到 {len(daily_data)} 条日线数据")
            
            return adj_data, daily_data
            
        except Exception as e:
            print(f"获取数据时出错: {e}")
            traceback.print_exc()
            return None, None