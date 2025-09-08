#!/usr/bin/env python3
"""
ETF更新模块 - 负责ETF数据的增量和全量更新
职责：处理数据更新逻辑、日期范围计算、数据合并
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from config.settings import get_default_date_range, DATE_FORMAT, FILE_TEMPLATES
from config.settings import BASIC_COLUMNS, RAW_COLUMNS, HFQ_COLUMNS, QFQ_COLUMNS
from .factor_calculator import FactorCalculator
from .logger import get_etf_logger


class ETFUpdater:
    """ETF更新器 - 单一职责：处理数据更新"""
    
    def __init__(self, api_client, data_processor, auto_calculate_factors=True):
        """初始化更新器"""
        self.client = api_client
        self.processor = data_processor
        self.auto_calculate_factors = auto_calculate_factors
        self.factor_calculator = FactorCalculator() if auto_calculate_factors else None
        self.logger = get_etf_logger()
    
    def calculate_update_range(self, etf_code):
        """计算更新日期范围"""
        latest_date = self.processor.check_existing_data(etf_code)
        end_date = datetime.now().strftime(DATE_FORMAT)
        
        if latest_date is None:
            # 首次获取全部历史数据
            start_date, _ = get_default_date_range()
            return start_date, end_date, "首次获取"
        
        # 增量更新：从最新日期的下一天开始
        latest_dt = datetime.strptime(latest_date, DATE_FORMAT)
        start_dt = latest_dt + timedelta(days=1)
        start_date = start_dt.strftime(DATE_FORMAT)
        
        if start_date > end_date:
            return None, None, "已是最新"
        
        return start_date, end_date, "增量更新"
    
    def fetch_and_process_data(self, etf_code, start_date, end_date):
        """获取并处理ETF数据"""
        print(f"获取数据: {etf_code} ({start_date} - {end_date})")
        
        # 获取原始数据
        adj_data, daily_data = self.client.fetch_etf_data(etf_code, start_date, end_date)
        
        if adj_data is None or daily_data is None or len(daily_data) == 0:
            return None, "无法获取数据或无新数据"
        
        # 处理数据
        try:
            merged_data = self.processor.merge_data(daily_data, adj_data)
            merged_data = self.processor.calculate_adjusted_prices(merged_data)
            final_data = self.processor.organize_final_data(merged_data)
            return final_data, f"成功获取 {len(final_data)} 条记录"
        except Exception as e:
            return None, f"数据处理失败: {e}"
    
    def update_etf_incremental(self, etf_code):
        """增量更新ETF数据"""
        self.logger.log_operation("INCREMENTAL_UPDATE_START", etf_code, "开始")
        
        start_date, end_date, status = self.calculate_update_range(etf_code)
        
        if start_date is None:
            # 数据已是最新，但仍检查是否需要计算因子
            if self.auto_calculate_factors and self.factor_calculator:
                print("🔄 检查因子更新需求...")
                self.factor_calculator.calculate_factors(etf_code, incremental=True)
            self.logger.log_operation("INCREMENTAL_UPDATE_COMPLETE", etf_code, "数据已是最新")
            return True, "数据已是最新"
        
        print(f"{status}: {start_date} - {end_date}")
        
        new_data, message = self.fetch_and_process_data(etf_code, start_date, end_date)
        if new_data is None:
            self.logger.log_operation("INCREMENTAL_UPDATE_FAILED", etf_code, "数据获取失败", {"error": message})
            return False, message
        
        # 记录数据更新详情
        update_details = {
            "date_range": f"{start_date} - {end_date}",
            "records_updated": len(new_data)
        }
        self.logger.log_operation("DATA_UPDATE", etf_code, "成功", update_details)
        
        # 合并保存数据
        self._merge_and_save(new_data, etf_code)
        
        # 自动计算因子
        if self.auto_calculate_factors and self.factor_calculator:
            print("\n" + "="*50)
            print("🧮 自动计算技术因子")
            print("="*50)
            
            factor_start_time = datetime.now()
            factor_success = self.factor_calculator.calculate_factors(etf_code, incremental=True)
            factor_duration = (datetime.now() - factor_start_time).total_seconds()
            
            if factor_success:
                # 显示因子摘要
                summary = self.factor_calculator.get_factor_summary(etf_code)
                print(f"\n📊 因子计算摘要:")
                print(f"   ETF代码: {summary['etf_code']}")
                print(f"   因子文件数: {summary['factor_files']}")
                print(f"   最新日期: {summary['latest_date']}")
                print(f"   可用因子: {len(summary['available_factors'])} 个")
                
                # 记录因子计算成功
                self.logger.log_factor_calculation(etf_code, "ALL_FACTORS", "成功", 
                                                 factor_duration, len(new_data))
                self.logger.log_operation("INCREMENTAL_UPDATE_COMPLETE", etf_code, "成功", 
                                        {"with_factors": True})
                
                return True, f"增量更新成功: {message} + 因子计算完成"
            else:
                self.logger.log_factor_calculation(etf_code, "ALL_FACTORS", "失败", factor_duration)
                self.logger.log_operation("INCREMENTAL_UPDATE_COMPLETE", etf_code, "部分成功", 
                                        {"with_factors": False, "factor_error": True})
                return True, f"增量更新成功: {message} (因子计算失败)"
        
        self.logger.log_operation("INCREMENTAL_UPDATE_COMPLETE", etf_code, "成功")
        return True, f"增量更新成功: {message}"
    
    def update_etf_full(self, etf_code):
        """全量更新ETF数据"""
        start_date, end_date = get_default_date_range()
        print(f"全量更新: {start_date} - {end_date}")
        
        new_data, message = self.fetch_and_process_data(etf_code, start_date, end_date)
        if new_data is None:
            return False, message
        
        # 直接保存新数据（覆盖旧数据）
        self.processor.save_separate_files(new_data, etf_code)
        
        # 自动计算因子（全量）
        if self.auto_calculate_factors and self.factor_calculator:
            print("\n" + "="*50)
            print("🧮 全量计算技术因子")
            print("="*50)
            
            factor_success = self.factor_calculator.calculate_factors(etf_code, incremental=False)
            if factor_success:
                # 显示因子摘要
                summary = self.factor_calculator.get_factor_summary(etf_code)
                print(f"\n📊 因子计算摘要:")
                print(f"   ETF代码: {summary['etf_code']}")
                print(f"   因子文件数: {summary['factor_files']}")
                print(f"   最新日期: {summary['latest_date']}")
                print(f"   可用因子: {len(summary['available_factors'])} 个")
                
                return True, f"全量更新成功: {message} + 因子计算完成"
            else:
                return True, f"全量更新成功: {message} (因子计算失败)"
        
        return True, f"全量更新成功: {message}"
    
    def _merge_and_save(self, new_data, etf_code):
        """合并新数据与现有数据并保存"""
        data_sets = {
            "basic": new_data[BASIC_COLUMNS],
            "raw": new_data[RAW_COLUMNS], 
            "hfq": new_data[HFQ_COLUMNS],
            "qfq": new_data[QFQ_COLUMNS],
        }
        
        for data_type, new_df in data_sets.items():
            file_path = self.processor.get_data_file_path(etf_code, FILE_TEMPLATES[data_type])
            
            # 确保新数据的trade_date是字符串类型
            new_df = new_df.copy()
            new_df['trade_date'] = new_df['trade_date'].astype(str)
            
            if os.path.exists(file_path):
                # 合并现有数据
                existing_df = pd.read_csv(file_path)
                # 确保现有数据的trade_date也是字符串类型
                existing_df['trade_date'] = existing_df['trade_date'].astype(str)
                
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['trade_date'], keep='last')
                # 排序时确保数据类型一致
                combined_df = combined_df.sort_values('trade_date', ascending=False)
                combined_df.to_csv(file_path, index=False)
            else:
                # 保存新数据
                new_df.to_csv(file_path, index=False)