"""
Global Configuration Manager - 全局配置管理器
统一管理精度、格式、常量等全局设置
文件限制: <200行
"""

import os
import yaml
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path


class GlobalConfig:
    """全局配置管理器 - 单例模式"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件"""
        config_file = Path(__file__).parent.parent / "config" / "global.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"全局配置文件不存在: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
            
        print(f"✅ 加载全局配置: {config_file}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值 (支持点号分隔的嵌套键)
        Args:
            key: 配置键 (如 "precision.price")
            default: 默认值
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_precision(self, data_type: str = "default") -> int:
        """获取指定数据类型的精度"""
        return self.get(f"precision.{data_type}", 6)
    
    def get_output_format(self) -> Dict[str, Any]:
        """获取输出格式配置"""
        return self.get("output_format", {})
    
    def get_etf_info(self) -> Dict[str, Any]:
        """获取ETF基础信息"""
        return self.get("etf_info", {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """获取数据验证规则"""
        return self.get("validation", {})
    
    def format_number(self, value: float, data_type: str = "default") -> float:
        """
        按配置精度格式化数值
        Args:
            value: 数值
            data_type: 数据类型 (price, percentage, indicator, statistics, default)
        Returns:
            格式化后的数值
        """
        if pd.isna(value):
            return value
            
        precision = self.get_precision(data_type)
        return round(float(value), precision)
    
    def format_dataframe(self, df: pd.DataFrame, column_types: Dict[str, str] = None) -> pd.DataFrame:
        """
        按配置格式化DataFrame
        Args:
            df: 输入DataFrame
            column_types: 列类型映射 {列名: 类型}
        Returns:
            格式化后的DataFrame
        """
        formatted_df = df.copy()
        column_types = column_types or {}
        
        # 格式化数值列
        numeric_columns = formatted_df.select_dtypes(include=['float64', 'int64']).columns
        
        for col in numeric_columns:
            if col in ['ts_code', 'trade_date']:
                continue
                
            # 根据列名推断数据类型
            data_type = self._infer_data_type(col, column_types.get(col))
            precision = self.get_precision(data_type)
            
            # 应用精度
            formatted_df[col] = formatted_df[col].round(precision)
        
        # 格式化日期列
        date_format = self.get("output_format.date_format", "%Y%m%d")
        if 'trade_date' in formatted_df.columns:
            if formatted_df['trade_date'].dtype == 'object':
                # 如果已经是字符串格式，保持不变
                pass
            else:
                # 转换为指定格式
                formatted_df['trade_date'] = pd.to_datetime(
                    formatted_df['trade_date']
                ).dt.strftime(date_format)
        
        return formatted_df
    
    def _infer_data_type(self, column_name: str, specified_type: str = None) -> str:
        """推断列的数据类型"""
        if specified_type:
            return specified_type
        
        col_lower = column_name.lower()
        
        # 价格类型
        if any(x in col_lower for x in ['price', 'open', 'high', 'low', 'close', 'sma', 'ema', 'wma', 'boll']):
            return "price"
        
        # 百分比类型
        if any(x in col_lower for x in ['pct', 'return', 'chg', 'rsi', 'wr', 'roc']):
            return "percentage"
        
        # 指标类型
        if any(x in col_lower for x in ['macd', 'cci', 'kdj', 'atr', 'obv']):
            return "indicator"
        
        # 统计量类型
        if any(x in col_lower for x in ['vol', 'std', 'corr', 'beta', 'sharpe']):
            return "statistics"
        
        return "default"
    
    def get_file_naming_template(self, file_type: str) -> str:
        """
        获取文件命名模板
        Args:
            file_type: 文件类型 (factor_file, group_file, complete_file)
        Returns:
            命名模板
        """
        template_key = f"naming_convention.{file_type}_template"
        return self.get(template_key, "{name}_{symbol}.csv")
    
    def validate_data_range(self, data: pd.Series, data_type: str) -> pd.Series:
        """
        验证数据范围
        Args:
            data: 数据序列
            data_type: 数据类型 (price, volume, percentage)
        Returns:
            验证后的数据 (异常值设为NaN)
        """
        if data_type not in ['price', 'volume', 'percentage']:
            return data
        
        range_config = self.get(f"validation.{data_type}_range")
        if not range_config:
            return data
        
        min_val = range_config.get('min')
        max_val = range_config.get('max')
        
        validated_data = data.copy()
        
        if min_val is not None:
            validated_data[validated_data < min_val] = pd.NA
        if max_val is not None:
            validated_data[validated_data > max_val] = pd.NA
            
        return validated_data
    
    def get_pandas_options(self) -> Dict[str, Any]:
        """获取pandas显示选项配置"""
        return {
            'display.precision': self.get_precision(),
            'display.float_format': lambda x: f'{x:.{self.get_precision()}f}',
            'display.max_columns': None,
            'display.width': None,
            'display.max_rows': 100
        }
    
    def apply_pandas_options(self):
        """应用pandas显示选项"""
        options = self.get_pandas_options()
        for key, value in options.items():
            pd.set_option(key, value)
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存相关配置"""
        return {
            'key_length': self.get('cache_settings.cache_key_length', 16),
            'compression': self.get('cache_settings.compression', True),
            'version': self.get('cache_settings.version', '1.0')
        }
    
    def is_debug_mode(self) -> bool:
        """是否为调试模式"""
        return self.get('environment.debug', False)
    
    def should_show_progress(self) -> bool:
        """是否显示进度"""
        return self.get('logging.show_progress', True)


# 全局配置实例
config = GlobalConfig()