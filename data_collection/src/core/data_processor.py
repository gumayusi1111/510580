#!/usr/bin/env python3
"""
数据处理模块
"""

import os
import sys
import pandas as pd

# 添加配置路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import (
    BASIC_COLUMNS, RAW_COLUMNS, HFQ_COLUMNS, QFQ_COLUMNS,
    FILE_TEMPLATES, DATA_DIR_NAME
)


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, base_dir=None):
        """初始化处理器"""
        # 修复路径：从 data_collection/src/core/data_processor.py 到 data_collection/
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, DATA_DIR_NAME)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_data_file_path(self, etf_code, filename):
        """获取数据文件的绝对路径"""
        # 提取纯代码（去掉.SH/.SZ后缀）
        code_only = etf_code.split('.')[0]
        etf_dir = os.path.join(self.data_dir, code_only)
        os.makedirs(etf_dir, exist_ok=True)
        return os.path.join(etf_dir, filename)
    
    def merge_data(self, daily_data, adj_data):
        """合并日线数据和复权因子"""
        print("\n3. 合并数据...")
        merged_data = pd.merge(
            daily_data, adj_data, on=["ts_code", "trade_date"], how="inner"
        )
        print(f"合并后数据行数: {len(merged_data)}")
        return merged_data
    
    def calculate_adjusted_prices(self, merged_data):
        """计算前复权和后复权价格"""
        print("\n4. 计算复权价格...")
        
        # 获取最新复权因子（用于前复权计算）
        latest_adj_factor = merged_data.iloc[0]["adj_factor"]
        print(f"最新复权因子: {latest_adj_factor}")
        
        # 后复权计算: 价格 × 当日复权因子
        merged_data["hfq_open"] = merged_data["open"] * merged_data["adj_factor"]
        merged_data["hfq_high"] = merged_data["high"] * merged_data["adj_factor"]
        merged_data["hfq_low"] = merged_data["low"] * merged_data["adj_factor"]
        merged_data["hfq_close"] = merged_data["close"] * merged_data["adj_factor"]
        
        # 前复权计算: 价格 ÷ 最新复权因子
        merged_data["qfq_open"] = merged_data["open"] / latest_adj_factor
        merged_data["qfq_high"] = merged_data["high"] / latest_adj_factor
        merged_data["qfq_low"] = merged_data["low"] / latest_adj_factor
        merged_data["qfq_close"] = merged_data["close"] / latest_adj_factor
        
        print("复权价格计算完成")
        print("- hfq_*: 后复权价格 (价格 × 当日复权因子)")
        print("- qfq_*: 前复权价格 (价格 ÷ 最新复权因子)")
        
        return merged_data
    
    def organize_final_data(self, merged_data):
        """整理最终数据列顺序"""
        column_order = [
            # 基础信息
            "ts_code", "trade_date",
            # 原始价格数据
            "pre_close", "open", "high", "low", "close",
            "change", "pct_chg", "vol", "amount",
            # 复权因子
            "adj_factor",
            # 后复权价格
            "hfq_open", "hfq_high", "hfq_low", "hfq_close",
            # 前复权价格
            "qfq_open", "qfq_high", "qfq_low", "qfq_close",
        ]
        return merged_data[column_order]
    
    def save_separate_files(self, merged_data, etf_code):
        """保存4个独立的数据文件"""
        print("\n=== 生成4个专门数据文件 ===")
        
        saved_files = {}
        
        # 1. 基础数据文件
        basic_data = merged_data[BASIC_COLUMNS]
        basic_file = self.get_data_file_path(etf_code, FILE_TEMPLATES["basic"])
        basic_data.to_csv(basic_file, index=False)
        saved_files["basic"] = basic_file
        print(f"✅ 基础数据: {basic_file}")
        
        # 2. 除权数据文件
        raw_data = merged_data[RAW_COLUMNS]
        raw_file = self.get_data_file_path(etf_code, FILE_TEMPLATES["raw"])
        raw_data.to_csv(raw_file, index=False)
        saved_files["raw"] = raw_file
        print(f"✅ 除权数据: {raw_file}")
        
        # 3. 后复权数据文件
        hfq_data = merged_data[HFQ_COLUMNS]
        hfq_file = self.get_data_file_path(etf_code, FILE_TEMPLATES["hfq"])
        hfq_data.to_csv(hfq_file, index=False)
        saved_files["hfq"] = hfq_file
        print(f"✅ 后复权数据: {hfq_file}")
        
        # 4. 前复权数据文件
        qfq_data = merged_data[QFQ_COLUMNS]
        qfq_file = self.get_data_file_path(etf_code, FILE_TEMPLATES["qfq"])
        qfq_data.to_csv(qfq_file, index=False)
        saved_files["qfq"] = qfq_file
        print(f"✅ 前复权数据: {qfq_file}")
        
        return saved_files
    
    def show_data_summary(self, merged_data):
        """显示数据汇总信息"""
        print("\n=== 数据概览 ===")
        print(f"记录数: {len(merged_data)}")
        print(f"时间范围: {merged_data['trade_date'].min()} 到 {merged_data['trade_date'].max()}")
        
        # 显示复权因子统计
        unique_factors = merged_data["adj_factor"].unique()
        print(f"复权因子范围: {unique_factors.min():.3f} - {unique_factors.max():.3f}")
        print(f"复权因子唯一值数量: {len(unique_factors)}")
        
        # 显示样例数据对比
        print("\n=== 价格对比样例 (最近3天) ===")
        sample_data = merged_data.head(3)
        for _, row in sample_data.iterrows():
            print(f"\n日期: {row['trade_date']}")
            print(f"  除权收盘: {row['close']:.3f}")
            print(f"  后复权收盘: {row['hfq_close']:.3f} (×{row['adj_factor']:.2f})")
            print(f"  前复权收盘: {row['qfq_close']:.3f} (÷{row['adj_factor']:.2f})")
        
        print("\n=== 文件用途说明 ===")
        print("📊 basic_data.csv   - 基础数据 + 复权因子（完整信息）")
        print("📈 raw_data.csv     - 除权数据（原始交易价格）")
        print("🎯 hfq_data.csv     - 后复权数据（量化回测推荐）")
        print("💡 qfq_data.csv     - 前复权数据（当前价位分析）")
    
    def check_existing_data(self, etf_code):
        """检查现有数据文件的最新日期"""
        basic_file = self.get_data_file_path(etf_code, FILE_TEMPLATES["basic"])
        
        if not os.path.exists(basic_file):
            print(f"未找到现有数据文件: {basic_file}")
            return None
        
        try:
            df = pd.read_csv(basic_file)
            if len(df) == 0:
                return None
            # 确保trade_date是字符串类型
            df['trade_date'] = df['trade_date'].astype(str)
            latest_date = df['trade_date'].max()
            print(f"现有数据最新日期: {latest_date}")
            return str(latest_date)
        except Exception as e:
            print(f"读取现有数据文件失败: {e}")
            return None