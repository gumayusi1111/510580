"""
缓存管理器 - 专业的数据缓存系统
支持多种缓存策略、过期机制和内存管理
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import time
import hashlib
import pickle
import logging
from pathlib import Path
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheManager:
    """专业的缓存管理器"""

    def __init__(self,
                 max_memory_mb: int = 512,
                 max_items: int = 100,
                 default_ttl: int = 3600,
                 enable_disk_cache: bool = True,
                 cache_dir: str = None):
        """
        初始化缓存管理器

        Args:
            max_memory_mb: 最大内存使用量(MB)
            max_items: 最大缓存项数
            default_ttl: 默认缓存时间(秒)
            enable_disk_cache: 是否启用磁盘缓存
            cache_dir: 磁盘缓存目录
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_items = max_items
        self.default_ttl = default_ttl
        self.enable_disk_cache = enable_disk_cache

        # 内存缓存 - 使用OrderedDict实现LRU
        self._memory_cache = OrderedDict()
        self._cache_info = {}  # 存储元数据
        self._lock = threading.RLock()

        # 磁盘缓存设置
        if cache_dir is None:
            cache_dir = Path.home() / ".quant_trading_cache"
        self.cache_dir = Path(cache_dir)
        if self.enable_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"缓存管理器初始化 - 内存限制: {max_memory_mb}MB, 最大项数: {max_items}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存数据

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存的数据或默认值
        """
        with self._lock:
            # 检查内存缓存
            if key in self._memory_cache:
                # 检查是否过期
                if self._is_expired(key):
                    self._remove_from_memory(key)
                else:
                    # 移到末尾(LRU)
                    value = self._memory_cache.pop(key)
                    self._memory_cache[key] = value
                    logger.debug(f"内存缓存命中: {key}")
                    return value

            # 检查磁盘缓存
            if self.enable_disk_cache:
                disk_value = self._get_from_disk(key)
                if disk_value is not None:
                    # 加载到内存缓存
                    self._put_to_memory(key, disk_value)
                    logger.debug(f"磁盘缓存命中: {key}")
                    return disk_value

            logger.debug(f"缓存未命中: {key}")
            return default

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        存储数据到缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)，None使用默认值

        Returns:
            是否成功存储
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            with self._lock:
                # 计算数据大小
                data_size = self._calculate_size(value)

                # 检查是否超过单个项的大小限制
                if data_size > self.max_memory_bytes * 0.5:
                    logger.warning(f"数据太大，直接存储到磁盘: {key}")
                    if self.enable_disk_cache:
                        return self._put_to_disk(key, value, ttl)
                    return False

                # 存储到内存
                success = self._put_to_memory(key, value, ttl, data_size)

                # 同时存储到磁盘（如果启用）
                if success and self.enable_disk_cache:
                    self._put_to_disk(key, value, ttl)

                return success

        except Exception as e:
            logger.error(f"缓存存储失败 {key}: {e}")
            return False

    def remove(self, key: str) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        with self._lock:
            removed = False

            # 从内存删除
            if key in self._memory_cache:
                self._remove_from_memory(key)
                removed = True

            # 从磁盘删除
            if self.enable_disk_cache:
                disk_removed = self._remove_from_disk(key)
                removed = removed or disk_removed

            if removed:
                logger.debug(f"缓存项已删除: {key}")

            return removed

    def clear(self, pattern: Optional[str] = None):
        """
        清空缓存

        Args:
            pattern: 键模式，None表示清空所有
        """
        with self._lock:
            if pattern is None:
                # 清空所有
                self._memory_cache.clear()
                self._cache_info.clear()
                if self.enable_disk_cache:
                    self._clear_disk_cache()
                logger.info("所有缓存已清空")
            else:
                # 清空匹配模式的缓存
                keys_to_remove = [key for key in self._memory_cache.keys()
                                if pattern in key]
                for key in keys_to_remove:
                    self.remove(key)
                logger.info(f"已清空匹配 '{pattern}' 的缓存")

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        with self._lock:
            total_memory = sum(info.get('size', 0) for info in self._cache_info.values())

            stats = {
                'memory_cache': {
                    'items': len(self._memory_cache),
                    'total_size_mb': total_memory / (1024 * 1024),
                    'max_size_mb': self.max_memory_bytes / (1024 * 1024),
                    'usage_percent': (total_memory / self.max_memory_bytes) * 100,
                },
                'disk_cache': {
                    'enabled': self.enable_disk_cache,
                    'directory': str(self.cache_dir) if self.enable_disk_cache else None
                },
                'settings': {
                    'max_items': self.max_items,
                    'default_ttl': self.default_ttl
                }
            }

            if self.enable_disk_cache:
                disk_stats = self._get_disk_stats()
                stats['disk_cache'].update(disk_stats)

            return stats

    def _put_to_memory(self, key: str, value: Any, ttl: int = None, data_size: int = None) -> bool:
        """存储到内存缓存"""
        if ttl is None:
            ttl = self.default_ttl

        if data_size is None:
            data_size = self._calculate_size(value)

        # 检查内存限制
        self._ensure_memory_limit(data_size)

        # 存储数据
        self._memory_cache[key] = value
        self._cache_info[key] = {
            'created_at': time.time(),
            'ttl': ttl,
            'size': data_size,
            'access_count': 1
        }

        logger.debug(f"数据已存储到内存缓存: {key} ({data_size} bytes)")
        return True

    def _get_from_disk(self, key: str) -> Any:
        """从磁盘缓存获取数据"""
        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            meta_file = self.cache_dir / f"{self._hash_key(key)}.meta"

            if not cache_file.exists() or not meta_file.exists():
                return None

            # 检查元数据
            with open(meta_file, 'r') as f:
                import json
                meta = json.load(f)

            # 检查过期
            if time.time() > meta['created_at'] + meta['ttl']:
                self._remove_from_disk(key)
                return None

            # 加载数据
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        except Exception as e:
            logger.error(f"磁盘缓存读取失败 {key}: {e}")
            return None

    def _put_to_disk(self, key: str, value: Any, ttl: int) -> bool:
        """存储到磁盘缓存"""
        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            meta_file = self.cache_dir / f"{self._hash_key(key)}.meta"

            # 存储数据
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)

            # 存储元数据
            meta = {
                'key': key,
                'created_at': time.time(),
                'ttl': ttl,
                'size': int(self._calculate_size(value))  # 确保为标准int类型
            }

            with open(meta_file, 'w') as f:
                import json
                json.dump(meta, f)

            return True

        except Exception as e:
            logger.error(f"磁盘缓存存储失败 {key}: {e}")
            return False

    def _remove_from_memory(self, key: str):
        """从内存缓存删除"""
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._cache_info:
            del self._cache_info[key]

    def _remove_from_disk(self, key: str) -> bool:
        """从磁盘缓存删除"""
        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            meta_file = self.cache_dir / f"{self._hash_key(key)}.meta"

            removed = False
            if cache_file.exists():
                cache_file.unlink()
                removed = True
            if meta_file.exists():
                meta_file.unlink()
                removed = True

            return removed

        except Exception as e:
            logger.error(f"磁盘缓存删除失败 {key}: {e}")
            return False

    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self._cache_info:
            return True

        info = self._cache_info[key]
        return time.time() > info['created_at'] + info['ttl']

    def _ensure_memory_limit(self, new_size: int):
        """确保内存使用不超限"""
        current_memory = sum(info.get('size', 0) for info in self._cache_info.values())

        # 如果添加新数据会超过限制，清理旧数据
        while (current_memory + new_size > self.max_memory_bytes or
               len(self._memory_cache) >= self.max_items):

            if not self._memory_cache:
                break

            # 删除最旧的项(LRU)
            old_key = next(iter(self._memory_cache))
            old_size = self._cache_info.get(old_key, {}).get('size', 0)

            self._remove_from_memory(old_key)
            current_memory -= old_size

            logger.debug(f"LRU清理: {old_key}")

    def _calculate_size(self, obj: Any) -> int:
        """计算对象大小(字节)"""
        try:
            if isinstance(obj, pd.DataFrame):
                return obj.memory_usage(deep=True).sum()
            elif isinstance(obj, pd.Series):
                return obj.memory_usage(deep=True)
            elif isinstance(obj, np.ndarray):
                return obj.nbytes
            else:
                return len(pickle.dumps(obj))
        except Exception:
            # 如果计算失败，返回保守估计
            return 1024

    def _hash_key(self, key: str) -> str:
        """生成键的哈希值"""
        return hashlib.md5(key.encode()).hexdigest()

    def _clear_disk_cache(self):
        """清空磁盘缓存"""
        try:
            for file in self.cache_dir.glob("*.cache"):
                file.unlink()
            for file in self.cache_dir.glob("*.meta"):
                file.unlink()
        except Exception as e:
            logger.error(f"清空磁盘缓存失败: {e}")

    def _get_disk_stats(self) -> Dict:
        """获取磁盘缓存统计"""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                'items': len(cache_files),
                'total_size_mb': total_size / (1024 * 1024)
            }
        except Exception:
            return {'items': 0, 'total_size_mb': 0}