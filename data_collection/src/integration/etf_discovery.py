#!/usr/bin/env python3
"""
ETF发现模块 - 负责发现和验证ETF代码
职责：发现现有ETF、验证ETF代码有效性
"""

import os
import sys
import pandas as pd

# 添加配置路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import FILE_TEMPLATES


class ETFDiscovery:
    """ETF发现器 - 单一职责：发现和验证ETF"""
    
    def __init__(self, data_dir):
        """初始化发现器"""
        self.data_dir = data_dir
    
    def get_existing_etfs(self):
        """获取现有的ETF代码列表"""
        if not os.path.exists(self.data_dir):
            return []
        
        etf_codes = []
        for item in os.listdir(self.data_dir):
            if self._is_valid_etf_dir(item):
                etf_codes.append(item)
        
        return sorted(etf_codes)
    
    def _is_valid_etf_dir(self, dir_name):
        """检查是否为有效的ETF目录"""
        item_path = os.path.join(self.data_dir, dir_name)
        
        # 必须是目录且为数字代码
        if not (os.path.isdir(item_path) and dir_name.isdigit()):
            return False
        
        # 必须包含基础数据文件
        basic_file = os.path.join(item_path, FILE_TEMPLATES["basic"])
        return os.path.exists(basic_file)
    
    def etf_exists(self, etf_code):
        """检查ETF是否已存在"""
        code_only = self._extract_code(etf_code)
        existing_etfs = self.get_existing_etfs()
        return code_only in existing_etfs
    
    def _extract_code(self, etf_code):
        """提取纯ETF代码（去掉.SH/.SZ后缀）"""
        return etf_code.split('.')[0]
    
    def normalize_etf_code(self, etf_code):
        """标准化ETF代码（添加.SH后缀）"""
        if '.' not in etf_code:
            return f"{etf_code}.SH"
        return etf_code
    
    def get_etf_stats(self, etf_code, data_processor):
        """获取ETF统计信息"""
        full_code = self.normalize_etf_code(etf_code)
        
        # 获取最新日期
        latest_date = data_processor.check_existing_data(full_code)
        
        # 获取记录数
        try:
            basic_file = data_processor.get_data_file_path(full_code, FILE_TEMPLATES["basic"])
            df = pd.read_csv(basic_file)
            record_count = len(df)
            date_range = f"{df['trade_date'].min()} ~ {df['trade_date'].max()}"
        except Exception:
            record_count = 0
            date_range = "N/A"
        
        return {
            'code': etf_code,
            'latest_date': latest_date or 'N/A',
            'record_count': record_count,
            'date_range': date_range
        }
    
    def validate_etf_code_format(self, etf_code):
        """验证ETF代码格式"""
        code_only = self._extract_code(etf_code)
        
        # 检查是否为6位数字
        if not (code_only.isdigit() and len(code_only) == 6):
            return False, "ETF代码必须为6位数字"
        
        # 检查后缀（如果有）
        if '.' in etf_code:
            suffix = etf_code.split('.')[1]
            if suffix not in ['SH', 'SZ']:
                return False, "ETF后缀只能是.SH或.SZ"
        
        return True, "格式正确"