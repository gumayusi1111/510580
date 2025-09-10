"""
BaseFactor - 向量化因子基类
每个因子继承此基类，强制使用向量化计算
文件限制: <50行
"""

from abc import ABC, abstractmethod
import pandas as pd
import hashlib


class BaseFactor(ABC):
    """向量化因子基类 - 所有因子的统一接口"""
    
    def __init__(self, params: dict = None):
        """
        初始化因子
        Args:
            params: 因子参数字典
        """
        self.params = params or {}
        self.name = self.__class__.__name__
        self.cache_key = None
        
    @abstractmethod
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        向量化计算因子值 - 子类必须实现
        禁止使用循环，必须使用NumPy/Pandas向量化操作
        
        Args:
            data: 输入数据DataFrame
        Returns:
            包含因子值的DataFrame
        """
        pass
    
    @abstractmethod 
    def get_required_columns(self) -> list:
        """
        获取计算所需的数据列
        Returns:
            必需列名列表
        """
        pass
    
    def get_cache_key(self, data_hash: str) -> str:
        """生成缓存键"""
        try:
            # 安全地处理参数，避免unhashable类型
            safe_params = {}
            for k, v in self.params.items():
                if isinstance(v, (list, tuple)):
                    safe_params[k] = str(v)
                elif hasattr(v, 'to_dict'):  # DataFrame等
                    safe_params[k] = f"<{type(v).__name__}>"
                else:
                    safe_params[k] = str(v)
            
            param_str = str(sorted(safe_params.items()))
            combined = f"{self.name}_{data_hash}_{param_str}"
            return hashlib.md5(combined.encode()).hexdigest()[:16]
        except Exception:
            # 如果还是有问题，使用简化的缓存键
            return hashlib.md5(f"{self.name}_{data_hash}".encode()).hexdigest()[:16]
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据"""
        required = self.get_required_columns()
        return all(col in data.columns for col in required)