"""
数据加载器主接口 - 整合所有加载功能
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .technical import TechnicalLoader
from .fundamental import FundamentalLoader
from .macro import MacroLoader

logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器 - 重构版本主接口"""

    def __init__(self, factor_data_path: Path):
        """
        初始化数据加载器

        Args:
            factor_data_path: 因子数据根路径
        """
        self.factor_data_path = factor_data_path

        # 初始化子加载器
        self.technical_loader = TechnicalLoader(factor_data_path)
        self.fundamental_loader = FundamentalLoader(factor_data_path)
        self.macro_loader = MacroLoader(factor_data_path)

        logger.info(f"数据加载器初始化，数据路径: {factor_data_path}")

    def load_complete_factors_file(self, etf_code: str) -> pd.DataFrame:
        """
        从complete目录加载完整因子数据

        Args:
            etf_code: ETF代码

        Returns:
            完整因子数据DataFrame
        """
        return self.technical_loader.load_complete_factors_file(etf_code)

    def load_technical_factors(self, etf_code: str) -> pd.DataFrame:
        """
        加载技术因子数据

        Args:
            etf_code: ETF代码

        Returns:
            技术因子数据DataFrame
        """
        return self.technical_loader.load_technical_factors(etf_code)

    def load_fundamental_factors(self, etf_code: str) -> pd.DataFrame:
        """
        加载基本面因子数据

        Args:
            etf_code: ETF代码

        Returns:
            基本面因子数据DataFrame
        """
        return self.fundamental_loader.load_fundamental_factors(etf_code)

    def load_macro_factors(self) -> pd.DataFrame:
        """
        加载宏观因子数据

        Returns:
            宏观因子数据DataFrame
        """
        return self.macro_loader.load_macro_factors()

    def get_factor_list(self, etf_code: str) -> List[str]:
        """
        获取指定ETF的所有可用因子列表

        Args:
            etf_code: ETF代码

        Returns:
            因子名称列表
        """
        factor_list = []

        try:
            # 技术因子
            technical_factors = self.technical_loader.get_technical_factor_list(etf_code)
            factor_list.extend([f"tech_{f}" for f in technical_factors])

            # 基本面因子
            fundamental_factors = self.fundamental_loader.get_fundamental_factor_list(etf_code)
            factor_list.extend([f"fund_{f}" for f in fundamental_factors])

            # 宏观因子
            macro_factors = self.macro_loader.get_macro_factor_list()
            factor_list.extend([f"macro_{f}" for f in macro_factors])

            logger.info(f"因子列表获取完成 {etf_code}: 共{len(factor_list)}个因子")

        except Exception as e:
            logger.error(f"获取因子列表失败 {etf_code}: {e}")

        return factor_list

    def load_factor_file(self, factor_name: str, etf_code: str) -> pd.DataFrame:
        """
        加载指定因子文件

        Args:
            factor_name: 因子名称
            etf_code: ETF代码

        Returns:
            因子数据DataFrame
        """
        try:
            # 根据因子名称前缀判断类型
            if factor_name.startswith("tech_"):
                actual_name = factor_name[5:]  # 移除"tech_"前缀
                return self.technical_loader.load_single_technical_factor(actual_name, etf_code)

            elif factor_name.startswith("fund_"):
                actual_name = factor_name[5:]  # 移除"fund_"前缀
                return self.fundamental_loader.load_single_fundamental_factor(actual_name, etf_code)

            elif factor_name.startswith("macro_"):
                actual_name = factor_name[6:]  # 移除"macro_"前缀
                return self.macro_loader.load_single_macro_factor(actual_name)

            else:
                # 默认尝试技术因子
                return self.technical_loader.load_single_technical_factor(factor_name, etf_code)

        except Exception as e:
            logger.error(f"加载因子文件失败 {factor_name} - {etf_code}: {e}")
            return pd.DataFrame()

    def get_data_summary(self, etf_code: str) -> Dict:
        """
        获取数据概要信息

        Args:
            etf_code: ETF代码

        Returns:
            数据概要信息
        """
        summary = {
            'etf_code': etf_code,
            'technical_factors': 0,
            'fundamental_factors': 0,
            'macro_factors': 0,
            'total_factors': 0,
            'data_availability': {},
            'date_ranges': {}
        }

        try:
            # 技术因子统计
            technical_factors = self.technical_loader.get_technical_factor_list(etf_code)
            summary['technical_factors'] = len(technical_factors)

            # 基本面因子统计
            fundamental_factors = self.fundamental_loader.get_fundamental_factor_list(etf_code)
            summary['fundamental_factors'] = len(fundamental_factors)

            # 宏观因子统计
            macro_factors = self.macro_loader.get_macro_factor_list()
            summary['macro_factors'] = len(macro_factors)

            summary['total_factors'] = sum([
                summary['technical_factors'],
                summary['fundamental_factors'],
                summary['macro_factors']
            ])

            # 数据可用性检查
            summary['data_availability'] = {
                'technical': len(technical_factors) > 0,
                'fundamental': len(fundamental_factors) > 0,
                'macro': len(macro_factors) > 0
            }

            # 获取日期范围（示例，实际可能需要加载数据）
            try:
                tech_data = self.load_technical_factors(etf_code)
                if not tech_data.empty and 'trade_date' in tech_data.columns:
                    summary['date_ranges']['technical'] = [
                        tech_data['trade_date'].min().strftime('%Y-%m-%d'),
                        tech_data['trade_date'].max().strftime('%Y-%m-%d')
                    ]
            except:
                pass

        except Exception as e:
            logger.error(f"获取数据概要失败 {etf_code}: {e}")
            summary['error'] = str(e)

        return summary

    def validate_data_paths(self) -> Dict:
        """
        验证数据路径结构

        Returns:
            验证结果
        """
        validation = {
            'root_exists': False,
            'technical_exists': False,
            'fundamental_exists': False,
            'macro_exists': False,
            'recommendations': []
        }

        try:
            # 检查根目录
            validation['root_exists'] = self.factor_data_path.exists()
            if not validation['root_exists']:
                validation['recommendations'].append(f"创建根目录: {self.factor_data_path}")

            # 检查子目录
            for data_type in ['technical', 'fundamental', 'macro']:
                path_key = f"{data_type}_exists"
                path = self.factor_data_path / data_type
                validation[path_key] = path.exists()

                if not validation[path_key]:
                    validation['recommendations'].append(f"创建{data_type}目录: {path}")

        except Exception as e:
            logger.error(f"数据路径验证失败: {e}")
            validation['error'] = str(e)

        return validation