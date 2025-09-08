"""
DataLoader - 数据加载器
支持多种数据源和复权类型
文件限制: <200行
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Union, List
import hashlib


class DataLoader:
    """数据加载和预处理器"""
    
    def __init__(self, data_dir: str = "../data"):
        """
        初始化数据加载器
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.data_cache = {}
        self.data_files = {
            "basic": "510580_SH_basic_data.csv",
            "raw": "510580_SH_raw_data.csv", 
            "hfq": "510580_SH_hfq_data.csv",
            "qfq": "510580_SH_qfq_data.csv"
        }
        
    def load_data(self, data_type: str = "hfq") -> pd.DataFrame:
        """
        加载指定类型的数据
        Args:
            data_type: 数据类型 ('basic', 'raw', 'hfq', 'qfq')
        Returns:
            预处理后的DataFrame
        """
        if data_type in self.data_cache:
            return self.data_cache[data_type].copy()
            
        if data_type not in self.data_files:
            raise ValueError(f"不支持的数据类型: {data_type}")
            
        file_path = os.path.join(self.data_dir, self.data_files[data_type])
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
            
        # 加载数据
        data = pd.read_csv(file_path)
        
        # 预处理
        data = self._preprocess_data(data)
        
        # 缓存数据
        self.data_cache[data_type] = data.copy()
        
        return data
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 确保基础列存在
        required_cols = ['ts_code', 'trade_date']
        if not all(col in data.columns for col in required_cols):
            raise ValueError("数据缺少必要列: ts_code, trade_date")
            
        # 日期处理
        data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')
        
        # 按日期排序
        data = data.sort_values('trade_date').reset_index(drop=True)
        
        # 数值列转换
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
        return data
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """数据质量检查"""
        if data.empty:
            return False
            
        # 检查必要列
        required_cols = ['ts_code', 'trade_date']
        if not all(col in data.columns for col in required_cols):
            return False
            
        # 检查数据连续性
        if data['trade_date'].isna().any():
            return False
            
        return True
    
    def get_data_hash(self, data: pd.DataFrame) -> str:
        """生成数据哈希用于缓存"""
        # 使用形状和最后日期生成简单哈希
        shape_str = f"{data.shape[0]}_{data.shape[1]}"
        last_date = str(data['trade_date'].iloc[-1])
        combined = f"{shape_str}_{last_date}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def get_required_columns_for_factors(self, factor_names: List[str]) -> List[str]:
        """
        获取因子列表所需的所有列
        Args:
            factor_names: 因子名称列表
        Returns:
            所需列名列表
        """
        # 基础列总是需要的
        required = ['ts_code', 'trade_date']
        
        # 根据因子类型添加所需列
        for factor_name in factor_names:
            if factor_name.upper() in ['SMA', 'EMA', 'WMA', 'MACD', 'RSI', 'ROC', 'MOM']:
                required.extend(['hfq_open', 'hfq_high', 'hfq_low', 'hfq_close'])
            elif factor_name.upper() in ['VMA', 'VOLUME_RATIO', 'OBV']:
                required.extend(['vol', 'amount'])
            elif factor_name.upper() in ['BOLL', 'ATR', 'HV']:
                required.extend(['hfq_open', 'hfq_high', 'hfq_low', 'hfq_close'])
                
        return list(set(required))  # 去重
    
    def load_incremental_data(self, last_date: str, data_type: str = "hfq") -> pd.DataFrame:
        """
        加载增量数据
        Args:
            last_date: 最后更新日期
            data_type: 数据类型
        Returns:
            增量数据DataFrame
        """
        full_data = self.load_data(data_type)
        last_date = pd.to_datetime(last_date)
        
        # 筛选新数据
        incremental = full_data[full_data['trade_date'] > last_date]
        
        return incremental
    
    def get_data_info(self, data_type: str = "hfq") -> dict:
        """获取数据基本信息"""
        data = self.load_data(data_type)
        
        return {
            "rows": len(data),
            "columns": len(data.columns),
            "start_date": str(data['trade_date'].min().date()),
            "end_date": str(data['trade_date'].max().date()),
            "data_hash": self.get_data_hash(data)
        }