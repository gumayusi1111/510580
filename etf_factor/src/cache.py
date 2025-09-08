"""
CacheManager - 缓存管理器
支持内存+磁盘缓存，增量更新
文件限制: <200行
"""

import os
import pickle
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from .config import config


class CacheManager:
    """缓存管理器 - 支持增量更新"""
    
    def __init__(self, cache_dir: str = "factor_data/cache"):
        """
        初始化缓存管理器
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.memory_cache = {}  # 内存缓存
        self.cache_file = os.path.join(cache_dir, "factor_cache.pkl")
        self.metadata_file = os.path.join(cache_dir, "metadata.json")
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 加载磁盘缓存
        self._load_cache_from_disk()
        
    def get_cached_factor(self, cache_key: str) -> Optional[pd.DataFrame]:
        """
        获取缓存的因子
        Args:
            cache_key: 缓存键
        Returns:
            缓存的DataFrame或None
        """
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key].copy()
        return None
    
    def cache_factor(self, cache_key: str, result: pd.DataFrame, factor_name: str = ""):
        """
        缓存因子结果
        Args:
            cache_key: 缓存键
            result: 计算结果
            factor_name: 因子名称（用于日志）
        """
        if result.empty:
            return
            
        # 内存缓存
        self.memory_cache[cache_key] = result.copy()
        
        # 更新元数据
        self._update_metadata(cache_key, factor_name)
        
        print(f"🔄 缓存因子: {factor_name} -> {cache_key[:8]}...")
    
    def is_cached(self, cache_key: str) -> bool:
        """检查是否已缓存"""
        return cache_key in self.memory_cache
    
    def save_cache_to_disk(self):
        """保存缓存到磁盘"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.memory_cache, f)
            print(f"💾 缓存已保存到磁盘: {self.cache_file}")
        except Exception as e:
            print(f"⚠️  保存缓存失败: {e}")
    
    def _load_cache_from_disk(self):
        """从磁盘加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.memory_cache = pickle.load(f)
                print(f"📂 从磁盘加载缓存: {len(self.memory_cache)} 项")
            except Exception as e:
                print(f"⚠️  加载缓存失败: {e}")
                self.memory_cache = {}
    
    def _update_metadata(self, cache_key: str, factor_name: str = ""):
        """更新元数据"""
        metadata = self._load_metadata()
        
        metadata['factors'][cache_key] = {
            'factor_name': factor_name,
            'cached_at': datetime.now().isoformat(),
            'data_rows': len(self.memory_cache[cache_key]) if cache_key in self.memory_cache else 0
        }
        metadata['last_updated'] = datetime.now().isoformat()
        
        self._save_metadata(metadata)
    
    def _load_metadata(self) -> dict:
        """加载元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认元数据结构
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'factors': {}
        }
    
    def _save_metadata(self, metadata: dict):
        """保存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  保存元数据失败: {e}")
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        metadata = self._load_metadata()
        
        memory_size = sum(
            df.memory_usage(deep=True).sum() 
            for df in self.memory_cache.values()
        ) / (1024 * 1024)  # MB
        
        return {
            'memory_cached_factors': len(self.memory_cache),
            'memory_size_mb': round(memory_size, 2),
            'disk_cache_exists': os.path.exists(self.cache_file),
            'metadata': metadata
        }
    
    def clear_cache(self, confirm: bool = False):
        """
        清理所有缓存
        Args:
            confirm: 确认清理
        """
        if not confirm:
            print("⚠️  请设置 confirm=True 确认清理操作")
            return
            
        # 清理内存缓存
        self.memory_cache.clear()
        
        # 删除磁盘缓存
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            
        # 重置元数据
        metadata = {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'factors': {}
        }
        self._save_metadata(metadata)
        
        print("🗑️  所有缓存已清理")
    
    def get_cache_keys_by_factor(self, factor_name: str) -> list:
        """
        根据因子名获取缓存键
        Args:
            factor_name: 因子名称
        Returns:
            相关的缓存键列表
        """
        keys = []
        metadata = self._load_metadata()
        
        for cache_key, info in metadata.get('factors', {}).items():
            if info.get('factor_name') == factor_name:
                keys.append(cache_key)
                
        return keys
    
    def update_incremental(self, cache_key: str, new_data: pd.DataFrame, factor_name: str = ""):
        """
        增量更新缓存
        Args:
            cache_key: 缓存键
            new_data: 新数据
            factor_name: 因子名称
        """
        if cache_key in self.memory_cache:
            # 合并新数据到现有缓存
            existing_data = self.memory_cache[cache_key]
            
            # 基于trade_date合并，避免重复
            combined = pd.concat([existing_data, new_data]).drop_duplicates(
                subset=['trade_date'], keep='last'
            ).sort_values('trade_date').reset_index(drop=True)
            
            self.memory_cache[cache_key] = combined
            print(f"📈 增量更新缓存: {factor_name} (+{len(new_data)} 行)")
        else:
            # 新缓存
            self.cache_factor(cache_key, new_data, factor_name)
    
    def __del__(self):
        """析构函数 - 自动保存缓存"""
        if hasattr(self, 'memory_cache') and self.memory_cache:
            self.save_cache_to_disk()