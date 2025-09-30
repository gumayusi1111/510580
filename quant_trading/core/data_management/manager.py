"""
数据管理器 - 重构版本主接口
整合所有数据管理功能的统一接口
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import logging

from ..loading import DataLoader
from ..processing import DataProcessor
from ..validation import DataValidator
from .cache import CacheManager

logger = logging.getLogger(__name__)


class DataManager:
    """ETF因子数据管理器 - 重构版本"""

    def __init__(self, factor_data_path: str = None):
        """
        初始化数据管理器

        Args:
            factor_data_path: 因子数据路径，默认为项目根目录下的etf_factor/factor_data
        """
        if factor_data_path is None:
            # 自动检测项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            self.factor_data_path = project_root / "etf_factor" / "factor_data"
        else:
            self.factor_data_path = Path(factor_data_path)

        # 初始化组件
        self.loader = DataLoader(self.factor_data_path)
        self.processor = DataProcessor()
        self.validator = DataValidator()

        # 专业缓存管理器
        cache_dir = self.factor_data_path.parent / "cache"
        self.cache = CacheManager(
            max_memory_mb=256,
            max_items=50,
            default_ttl=3600,  # 1小时
            enable_disk_cache=True,
            cache_dir=str(cache_dir)
        )

        logger.info(f"数据管理器初始化，因子数据路径: {self.factor_data_path}")

    def load_complete_factors(self, etf_code: str = "510580") -> pd.DataFrame:
        """
        加载完整的因子数据集

        Args:
            etf_code: ETF代码，默认510580

        Returns:
            包含所有因子的DataFrame
        """
        cache_key = f"complete_{etf_code}"

        # 从缓存获取数据
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"从缓存加载完整因子数据: {etf_code}")
            return cached_data

        try:
            # 首先尝试从complete目录加载
            complete_df = self.loader.load_complete_factors_file(etf_code)

            if not complete_df.empty:
                # 数据验证
                validation_result = self.validator.validate_basic_structure(complete_df)
                if not validation_result['is_valid']:
                    logger.warning(f"Complete数据验证失败: {validation_result['errors']}")

                # 数据清洗
                complete_df = self.processor.clean_data(complete_df)
                self.cache.put(cache_key, complete_df)
                return complete_df

            # 如果complete文件不存在，则合并各类数据
            logger.info(f"Complete文件不存在，尝试合并各类因子数据: {etf_code}")
            return self.load_all_factors(etf_code)

        except Exception as e:
            logger.error(f"加载完整因子数据失败 {etf_code}: {e}")
            return pd.DataFrame()

    def load_all_factors(self, etf_code: str = "510580") -> pd.DataFrame:
        """
        加载并合并所有类型的因子数据

        Args:
            etf_code: ETF代码

        Returns:
            合并后的所有因子数据
        """
        cache_key = f"all_{etf_code}"

        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"从缓存加载所有因子数据: {etf_code}")
            return cached_data

        try:
            # 分别加载各类数据
            technical_df = self.loader.load_technical_factors(etf_code)
            fundamental_df = self.loader.load_fundamental_factors(etf_code)
            macro_df = self.loader.load_macro_factors()

            # 合并数据
            all_factors_df = self.processor.merge_factor_data(
                technical_df, fundamental_df, macro_df
            )

            if not all_factors_df.empty:
                # 数据清洗
                all_factors_df = self.processor.clean_data(all_factors_df)
                self.cache.put(cache_key, all_factors_df)

            return all_factors_df

        except Exception as e:
            logger.error(f"加载所有因子数据失败 {etf_code}: {e}")
            return pd.DataFrame()

    def get_factor_list(self, etf_code: str = "510580") -> List[str]:
        """
        获取指定ETF的所有可用因子列表

        Args:
            etf_code: ETF代码

        Returns:
            因子名称列表
        """
        return self.loader.get_factor_list(etf_code)

    def get_factor_data(self, factors: List[str], etf_code: str = "510580") -> pd.DataFrame:
        """
        获取指定因子的数据

        Args:
            factors: 因子名称列表
            etf_code: ETF代码

        Returns:
            指定因子的数据DataFrame
        """
        try:
            # 先获取完整数据
            complete_df = self.load_complete_factors(etf_code)

            if complete_df.empty:
                logger.warning(f"无法获取 {etf_code} 的完整因子数据")
                return pd.DataFrame()

            # 筛选指定因子
            factor_df = self.processor.filter_factor_data(complete_df, factors)
            return factor_df

        except Exception as e:
            logger.error(f"获取因子数据失败 {etf_code}: {e}")
            return pd.DataFrame()

    def get_returns_data(self, etf_code: str = "510580") -> pd.Series:
        """
        获取ETF收益率数据

        Args:
            etf_code: ETF代码

        Returns:
            收益率数据序列
        """
        try:
            # 从技术因子中获取价格数据
            technical_df = self.loader.load_technical_factors(etf_code)

            if technical_df.empty:
                logger.warning(f"无法获取 {etf_code} 的技术因子数据")
                return pd.Series()

            # 优先查找已计算的收益率列，再尝试价格列
            if 'DAILY_RETURN' in technical_df.columns:
                # 使用已计算的日收益率
                returns = technical_df['DAILY_RETURN'].dropna()
                logger.info("使用技术因子中的DAILY_RETURN列")
            else:
                # 寻找价格列（通常是收盘价）
                price_columns = ['close', 'hfq_close', 'qfq_close', 'adj_close']
                price_column = None

                for col in price_columns:
                    if col in technical_df.columns:
                        price_column = col
                        break

                if price_column is None:
                    logger.error("在技术因子数据中未找到价格列或收益率列")
                    return pd.Series()

                # 计算收益率
                returns = self.processor.calculate_returns(technical_df, price_column)
                returns.index = technical_df['trade_date'].iloc[1:len(returns)+1].values

            return returns

        except Exception as e:
            logger.error(f"获取收益率数据失败 {etf_code}: {e}")
            return pd.Series()

    def get_data_info(self, etf_code: str = "510580") -> Dict:
        """
        获取数据基本信息

        Args:
            etf_code: ETF代码

        Returns:
            数据信息字典
        """
        try:
            factor_df = self.load_complete_factors(etf_code)

            if factor_df.empty:
                return {
                    'etf_code': etf_code,
                    'data_shape': (0, 0),
                    'factor_count': 0,
                    'date_range': [None, None],
                    'missing_data_ratio': 1.0,
                    'data_quality': 'poor'
                }

            # 获取统计信息
            stats = self.processor.get_data_statistics(factor_df)

            # 数据质量验证
            factor_columns = [col for col in factor_df.columns
                            if col not in ['ts_code', 'trade_date']]
            quality_result = self.validator.validate_factor_data_quality(
                factor_df, factor_columns
            )

            return {
                'etf_code': etf_code,
                'data_shape': stats.get('shape', (0, 0)),
                'factor_count': len(factor_columns),
                'date_range': stats.get('date_range', [None, None]),
                'missing_data_ratio': stats.get('missing_data_ratio', 0),
                'data_quality': 'good' if quality_result['quality_score'] > 0.7 else 'poor',
                'quality_score': quality_result['quality_score'],
                'trading_days': stats.get('trading_days', 0)
            }

        except Exception as e:
            logger.error(f"获取数据信息失败 {etf_code}: {e}")
            return {
                'etf_code': etf_code,
                'error': str(e)
            }

    def validate_data_quality(self, etf_code: str = "510580") -> Dict:
        """
        验证数据质量

        Args:
            etf_code: ETF代码

        Returns:
            数据质量验证结果
        """
        try:
            factor_df = self.load_complete_factors(etf_code)

            if factor_df.empty:
                return {'is_valid': False, 'error': 'no_data'}

            # 基本结构验证
            structure_result = self.validator.validate_basic_structure(factor_df)

            # 因子质量验证
            factor_columns = [col for col in factor_df.columns
                            if col not in ['ts_code', 'trade_date']]
            quality_result = self.validator.validate_factor_data_quality(
                factor_df, factor_columns
            )

            # 时间序列连续性验证
            continuity_result = self.validator.validate_time_series_continuity(factor_df)

            return {
                'etf_code': etf_code,
                'structure_validation': structure_result,
                'quality_validation': quality_result,
                'continuity_validation': continuity_result,
                'overall_score': (
                    (1.0 if structure_result['is_valid'] else 0.0) * 0.3 +
                    quality_result['quality_score'] * 0.5 +
                    (1.0 if continuity_result['is_continuous'] else 0.7) * 0.2
                )
            }

        except Exception as e:
            logger.error(f"数据质量验证失败 {etf_code}: {e}")
            return {'is_valid': False, 'error': str(e)}

    def clean_data(self, df: pd.DataFrame, method: str = "forward_fill") -> pd.DataFrame:
        """
        清洗数据

        Args:
            df: 输入数据DataFrame
            method: 清洗方法

        Returns:
            清洗后的DataFrame
        """
        return self.processor.clean_data(df, method)

    def clear_cache(self, etf_code: str = None):
        """
        清除数据缓存

        Args:
            etf_code: 要清除的ETF代码，None表示清除所有缓存
        """
        if etf_code is None:
            self.cache.clear()
            logger.info("已清除所有数据缓存")
        else:
            self.cache.clear(pattern=etf_code)
            logger.info(f"已清除 {etf_code} 相关的数据缓存")

    def get_cache_info(self) -> Dict:
        """
        获取缓存信息

        Returns:
            缓存信息字典
        """
        return self.cache.get_stats()