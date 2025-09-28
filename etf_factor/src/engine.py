"""
VectorizedEngine - 向量化因子计算引擎
核心计算引擎，支持批量向量化计算和缓存
文件限制: <200行
"""

import os
import sys
import importlib
from typing import List, Dict, Optional, Union
import pandas as pd

# 动态导入解决相对导入问题
try:
    # 首先尝试相对导入（在src内部调用时）
    from .data_loader import DataLoader
    from .data_writer import DataWriter
    from .cache import CacheManager
    from .base_factor import BaseFactor
except ImportError:
    # 相对导入失败时，使用绝对导入（外部调用时）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    from data_loader import DataLoader
    from data_writer import DataWriter
    from cache import CacheManager
    from base_factor import BaseFactor


class VectorizedEngine:
    """向量化因子计算引擎"""
    
    def __init__(self, data_dir: str = "../data_collection/data/510580", output_dir: str = "factor_data"):
        """
        初始化引擎
        Args:
            data_dir: 数据源目录
            output_dir: 输出目录
        """
        self.data_loader = DataLoader(data_dir)
        # 从data_dir推断ETF代码 (如：../data_collection/data/510580 -> 510580)
        etf_code = os.path.basename(data_dir) if os.path.basename(data_dir).isdigit() else "510580"
        self.data_writer = DataWriter(output_dir, etf_code)
        self.cache = CacheManager(f"{output_dir}/cache")
        self.factors = {}  # 注册的因子实例
        
        # 自动发现并注册因子
        self._discover_factors()
        
    def _discover_factors(self):
        """自动发现factors目录下的因子(支持文件和文件夹结构)"""
        # 获取当前文件所在的目录，然后找到factors目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        etf_factor_root = os.path.dirname(current_dir)  # 上级目录是etf_factor
        factors_dir = os.path.join(etf_factor_root, "factors")

        if not os.path.exists(factors_dir):
            print(f"⚠️  因子目录不存在: {factors_dir}")
            return

        # 添加etf_factor根目录到sys.path以支持factors导入
        import sys
        if etf_factor_root not in sys.path:
            sys.path.insert(0, etf_factor_root)

        for item in os.listdir(factors_dir):
            item_path = os.path.join(factors_dir, item)
            module_name = None

            # 处理.py文件 (原有的单文件因子)
            if item.endswith('.py') and not item.startswith('__'):
                module_name = item[:-3]  # 去掉.py扩展名

            # 处理文件夹 (新的模块化因子)
            elif os.path.isdir(item_path) and not item.startswith('__'):
                init_file = os.path.join(item_path, '__init__.py')
                if os.path.exists(init_file):
                    module_name = item

            if module_name:
                try:
                    # 处理相对导入问题，确保每个模块在独立的命名空间中加载
                    # 对于文件夹结构的因子，需要特殊处理导入路径
                    if os.path.isdir(os.path.join(factors_dir, module_name)):
                        # 文件夹结构的模块化因子
                        # 临时添加特定模块路径到sys.path
                        module_path = os.path.join(factors_dir, module_name)
                        if module_path not in sys.path:
                            sys.path.insert(0, module_path)
                        try:
                            # 导入该模块的__init__.py
                            module = importlib.import_module(f"factors.{module_name}")
                            # 移除临时路径以避免污染
                            if module_path in sys.path:
                                sys.path.remove(module_path)
                        except:
                            if module_path in sys.path:
                                sys.path.remove(module_path)
                            raise
                    else:
                        # 单文件因子
                        module = importlib.import_module(f"factors.{module_name}")

                    # 查找BaseFactor的子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, BaseFactor) and
                            attr != BaseFactor):
                            # 注册因子
                            factor_name = attr.__name__
                            self.factors[factor_name] = attr

                except Exception as e:
                    print(f"⚠️  加载因子失败 {module_name}: {e}")

        print(f"🔍 发现 {len(self.factors)} 个因子: {list(self.factors.keys())}")
    
    def register_factor(self, factor_class: type):
        """
        手动注册因子
        Args:
            factor_class: 因子类
        """
        if not issubclass(factor_class, BaseFactor):
            raise ValueError("因子必须继承BaseFactor基类")
            
        factor_name = factor_class.__name__
        self.factors[factor_name] = factor_class
        print(f"📝 注册因子: {factor_name}")
    
    def calculate_single_factor(self, factor_name: str, params: dict = None, 
                              data_type: str = "hfq", use_cache: bool = True) -> pd.DataFrame:
        """
        计算单个因子
        Args:
            factor_name: 因子名称
            params: 因子参数
            data_type: 数据类型
            use_cache: 是否使用缓存
        Returns:
            因子计算结果
        """
        if factor_name not in self.factors:
            raise ValueError(f"未知因子: {factor_name}")
            
        # 创建因子实例
        factor_class = self.factors[factor_name]
        factor = factor_class(params) if params else factor_class()
        
        # 加载数据
        data = self.data_loader.load_data(data_type)
        data_hash = self.data_loader.get_data_hash(data)
        
        # 检查缓存
        cache_key = factor.get_cache_key(data_hash)
        if use_cache and self.cache.is_cached(cache_key):
            print(f"🎯 使用缓存: {factor_name}")
            return self.cache.get_cached_factor(cache_key)
        
        # 验证数据
        if not factor.validate_data(data):
            raise ValueError(f"数据验证失败，缺少必要列: {factor.get_required_columns()}")
        
        # 向量化计算
        print(f"⚡ 向量化计算: {factor_name}")
        result = factor.calculate_vectorized(data)
        
        # 缓存结果
        if use_cache:
            self.cache.cache_factor(cache_key, result, factor_name)
        
        return result
    
    def calculate_batch_factors(self, factor_names: List[str], params_dict: dict = None,
                              data_type: str = "hfq", use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量计算因子
        Args:
            factor_names: 因子名称列表
            params_dict: 因子参数字典 {因子名: 参数}
            data_type: 数据类型
            use_cache: 是否使用缓存
        Returns:
            因子结果字典
        """
        results = {}
        params_dict = params_dict or {}
        
        print(f"🚀 批量计算 {len(factor_names)} 个因子")
        
        for factor_name in factor_names:
            try:
                params = params_dict.get(factor_name)
                result = self.calculate_single_factor(
                    factor_name, params, data_type, use_cache
                )
                results[factor_name] = result
                
            except Exception as e:
                print(f"❌ {factor_name} 计算失败: {e}")
                continue
                
        print(f"✅ 完成批量计算: {len(results)}/{len(factor_names)} 个因子")
        return results
    
    def calculate_all_factors(self, data_type: str = "hfq", use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """计算所有已注册的因子"""
        return self.calculate_batch_factors(
            list(self.factors.keys()), data_type=data_type, use_cache=use_cache
        )
    
    def save_factor_results(self, results: Dict[str, pd.DataFrame], 
                          output_type: str = "single") -> List[str]:
        """
        保存因子结果
        Args:
            results: 因子结果字典
            output_type: 输出类型 ('single', 'group', 'complete')
        Returns:
            保存的文件路径列表
        """
        saved_files = []
        
        if output_type == "single":
            # 保存单个因子文件
            for factor_name, data in results.items():
                file_path = self.data_writer.save_single_factor(factor_name, data)
                saved_files.append(file_path)
                
        elif output_type == "group":
            # 按分组保存 (需要实现因子分组逻辑)
            groups = self._group_factors_by_category(results)
            for group_name, group_data in groups.items():
                file_path = self.data_writer.save_factor_group(group_name, group_data)
                saved_files.append(file_path)
                
        elif output_type == "complete":
            # 合并所有因子保存
            combined_data = self._combine_all_factors(results)
            file_path = self.data_writer.save_complete_factors(combined_data)
            saved_files.append(file_path)
            
        return saved_files
    
    def _group_factors_by_category(self, results: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """按类别分组因子"""
        groups = {
            'moving_average': {},
            'trend_momentum': {}, 
            'volatility': {},
            'volume_price': {},
            'return_risk': {}
        }
        
        # 简单的分组规则 (可以从配置文件读取)
        for factor_name, data in results.items():
            name_upper = factor_name.upper()
            if any(x in name_upper for x in ['SMA', 'EMA', 'WMA', 'MA_']):
                groups['moving_average'][factor_name] = data
            elif any(x in name_upper for x in ['MACD', 'RSI', 'ROC', 'MOM']):
                groups['trend_momentum'][factor_name] = data
            elif any(x in name_upper for x in ['ATR', 'BOLL', 'HV', 'TR', 'DC', 'STOCH']):
                groups['volatility'][factor_name] = data
            elif any(x in name_upper for x in ['VMA', 'OBV', 'KDJ', 'CCI', 'WR', 'MFI']):
                groups['volume_price'][factor_name] = data
            elif any(x in name_upper for x in ['RETURN', 'VOL', 'DD']):
                groups['return_risk'][factor_name] = data
        
        # 移除空分组
        return {k: v for k, v in groups.items() if v}
    
    def _combine_all_factors(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """合并所有因子到一个DataFrame"""
        if not results:
            return pd.DataFrame()
            
        # 以第一个因子为基础
        base_data = None
        for factor_name, factor_data in results.items():
            if base_data is None:
                base_data = factor_data[['ts_code', 'trade_date']].copy()
                
            # 合并因子列
            factor_cols = [col for col in factor_data.columns 
                          if col not in ['ts_code', 'trade_date']]
            for col in factor_cols:
                base_data[col] = factor_data[col]
        
        return base_data
    
    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            'registered_factors': list(self.factors.keys()),
            'factor_count': len(self.factors),
            'cache_info': self.cache.get_cache_info(),
            'data_info': self.data_loader.get_data_info(),
            'output_info': self.data_writer.get_output_info()
        }