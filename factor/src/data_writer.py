"""
DataWriter - 数据输出管理器
管理因子计算结果的文件输出
文件限制: <200行
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from .config import config


class DataWriter:
    """数据输出管理器"""
    
    def __init__(self, output_dir: str = "factor_data"):
        """
        初始化数据输出器
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.symbol = "510580_SH"  # ETF代码
        self.ensure_directories()
        
    def ensure_directories(self):
        """创建输出目录结构"""
        dirs = ["single_factors", "factor_groups", "complete", "cache"]
        for dir_name in dirs:
            path = os.path.join(self.output_dir, dir_name)
            os.makedirs(path, exist_ok=True)
            
    def save_single_factor(self, factor_name: str, data: pd.DataFrame) -> str:
        """
        保存单个因子到文件
        Args:
            factor_name: 因子名称
            data: 因子数据
        Returns:
            保存的文件路径
        """
        # 确保包含基础列
        if not all(col in data.columns for col in ['ts_code', 'trade_date']):
            raise ValueError("数据必须包含 ts_code 和 trade_date 列")
            
        # 生成文件路径
        filename = f"{factor_name}_{self.symbol}.csv"
        file_path = os.path.join(self.output_dir, "single_factors", filename)
        
        # 整理数据格式
        output_data = self._format_output_data(data)
        
        # 保存文件
        output_data.to_csv(file_path, index=False)
        
        print(f"✅ 保存单因子: {file_path}")
        return file_path
    
    def save_factor_group(self, group_name: str, factors_data: Dict[str, pd.DataFrame]) -> str:
        """
        保存因子组到文件
        Args:
            group_name: 分组名称 (如 'moving_average')
            factors_data: 因子数据字典 {因子名: DataFrame}
        Returns:
            保存的文件路径
        """
        if not factors_data:
            raise ValueError("因子数据不能为空")
            
        # 合并所有因子
        base_data = None
        for factor_name, factor_data in factors_data.items():
            if base_data is None:
                base_data = factor_data[['ts_code', 'trade_date']].copy()
                
            # 合并因子列
            factor_cols = [col for col in factor_data.columns 
                          if col not in ['ts_code', 'trade_date']]
            for col in factor_cols:
                base_data[col] = factor_data[col]
        
        # 生成文件路径
        filename = f"{group_name}_{self.symbol}.csv"
        file_path = os.path.join(self.output_dir, "factor_groups", filename)
        
        # 整理数据格式
        output_data = self._format_output_data(base_data)
        
        # 保存文件
        output_data.to_csv(file_path, index=False)
        
        print(f"✅ 保存因子组: {file_path}")
        return file_path
    
    def save_complete_factors(self, all_factors_data: pd.DataFrame) -> str:
        """
        保存完整因子数据
        Args:
            all_factors_data: 包含所有因子的DataFrame
        Returns:
            保存的文件路径
        """
        filename = f"all_factors_{self.symbol}.csv"
        file_path = os.path.join(self.output_dir, "complete", filename)
        
        # 整理数据格式
        output_data = self._format_output_data(all_factors_data)
        
        # 保存文件
        output_data.to_csv(file_path, index=False)
        
        print(f"✅ 保存完整因子数据: {file_path}")
        return file_path
    
    def _format_output_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """使用全局配置格式化输出数据"""
        # 使用全局配置格式化
        output_data = config.format_dataframe(data)
        
        # 按日期排序 (最新日期在前)
        if 'trade_date' in output_data.columns:
            output_data = output_data.sort_values('trade_date', ascending=False)
            
        return output_data
    
    def save_factor_metadata(self, metadata: dict) -> str:
        """
        保存因子元数据
        Args:
            metadata: 元数据字典
        Returns:
            保存的文件路径
        """
        import json
        
        # 添加时间戳
        metadata['last_updated'] = datetime.now().isoformat()
        
        file_path = os.path.join(self.output_dir, "cache", "metadata.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return file_path
    
    def get_output_info(self) -> dict:
        """获取输出目录信息"""
        info = {
            "output_dir": self.output_dir,
            "symbol": self.symbol,
            "directories": {}
        }
        
        # 统计各目录文件数量
        dirs = ["single_factors", "factor_groups", "complete", "cache"]
        for dir_name in dirs:
            dir_path = os.path.join(self.output_dir, dir_name)
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith(('.csv', '.json', '.pkl'))]
                info["directories"][dir_name] = {
                    "file_count": len(files),
                    "files": files[:5]  # 只显示前5个文件
                }
                
        return info
    
    def clean_output_dir(self, confirm: bool = False):
        """
        清理输出目录
        Args:
            confirm: 是否确认清理
        """
        if not confirm:
            print("⚠️  请设置 confirm=True 确认清理操作")
            return
            
        dirs = ["single_factors", "factor_groups", "complete", "cache"]
        for dir_name in dirs:
            dir_path = os.path.join(self.output_dir, dir_name)
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
        
        print(f"✅ 已清理输出目录: {self.output_dir}")