#!/usr/bin/env python3
"""
数据收集配置文件
"""

from datetime import datetime, timedelta

# Tushare配置
TUSHARE_TOKEN = "a44b1b3296e72fa73c18a1d739a6b5c7a6425351601bce03e34533b0"

# ETF配置
DEFAULT_ETF_CODE = "510580.SH"  # 中证500ETF易方达
DEFAULT_ETF_NAME = "中证500ETF易方达"

# 数据获取配置
DEFAULT_DAYS = None  # 默认获取全部历史数据
MAX_RETRY_TIMES = 3  # API请求重试次数
REQUEST_DELAY = 0.1  # API请求间隔(秒)

# 文件路径配置
DATA_DIR_NAME = "data"
BACKUP_DIR_NAME = "backup"

# 数据文件命名模板
FILE_TEMPLATES = {
    "basic": "basic_data.csv",
    "raw": "raw_data.csv", 
    "hfq": "hfq_data.csv",
    "qfq": "qfq_data.csv"
}

# 数据列配置
BASIC_COLUMNS = [
    "ts_code", "trade_date", "pre_close", "open", "high", "low", "close",
    "change", "pct_chg", "vol", "amount", "adj_factor"
]

RAW_COLUMNS = [
    "ts_code", "trade_date", "pre_close", "open", "high", "low", "close",
    "change", "pct_chg", "vol", "amount"
]

HFQ_COLUMNS = [
    "ts_code", "trade_date", "hfq_open", "hfq_high", "hfq_low", "hfq_close",
    "vol", "amount"
]

QFQ_COLUMNS = [
    "ts_code", "trade_date", "qfq_open", "qfq_high", "qfq_low", "qfq_close", 
    "vol", "amount"
]

# 日期格式
DATE_FORMAT = "%Y%m%d"

def get_default_date_range():
    """获取默认日期范围"""
    end_date = datetime.now().strftime(DATE_FORMAT)
    if DEFAULT_DAYS is None:
        # 获取全部历史数据，从2009年开始（ETF成立较早时间）
        start_date = "20090101"
    else:
        start_date = (datetime.now() - timedelta(days=DEFAULT_DAYS)).strftime(DATE_FORMAT)
    return start_date, end_date