"""
宏观经济数据加载器
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class MacroLoader:
    """宏观经济数据加载器"""

    def __init__(self, factor_data_path: Path):
        """初始化宏观数据加载器"""
        self.factor_data_path = factor_data_path

    def load_macro_factors(self) -> pd.DataFrame:
        """
        加载宏观因子数据

        Returns:
            宏观因子数据DataFrame
        """
        macro_path = self.factor_data_path / "macro"

        if not macro_path.exists():
            logger.warning(f"宏观因子目录不存在: {macro_path}")
            return pd.DataFrame()

        all_macro = pd.DataFrame()
        macro_files = list(macro_path.glob("*.csv"))

        if not macro_files:
            logger.warning(f"宏观因子目录为空: {macro_path}")
            return pd.DataFrame()

        try:
            for macro_file in macro_files:
                macro_name = macro_file.stem
                macro_df = pd.read_csv(macro_file)

                # 验证数据格式
                if 'trade_date' not in macro_df.columns:
                    logger.warning(f"宏观数据文件缺少trade_date列: {macro_file}")
                    continue

                # 转换日期格式
                macro_df['trade_date'] = pd.to_datetime(macro_df['trade_date'], format='%Y%m%d')

                # 重命名值列
                if 'value' in macro_df.columns:
                    macro_df = macro_df.rename(columns={'value': macro_name})

                # 合并数据（宏观数据通常没有ts_code）
                if all_macro.empty:
                    all_macro = macro_df[['trade_date', macro_name]].copy()
                else:
                    all_macro = pd.merge(
                        all_macro,
                        macro_df[['trade_date', macro_name]],
                        on='trade_date',
                        how='outer'
                    )

            # 按日期排序
            if not all_macro.empty:
                all_macro = all_macro.sort_values('trade_date')

            logger.info(f"宏观因子加载完成: 总因子数: {len(macro_files)}, 形状: {all_macro.shape}")

        except Exception as e:
            logger.error(f"宏观因子加载失败: {e}")
            return pd.DataFrame()

        return all_macro

    def get_macro_factor_list(self) -> List[str]:
        """
        获取宏观因子列表

        Returns:
            宏观因子名称列表
        """
        macro_path = self.factor_data_path / "macro"

        if not macro_path.exists():
            return []

        macro_files = list(macro_path.glob("*.csv"))
        macro_names = [f.stem for f in macro_files]

        logger.debug(f"宏观因子列表: 共{len(macro_names)}个因子")
        return macro_names

    def load_single_macro_factor(self, factor_name: str) -> pd.DataFrame:
        """
        加载单个宏观因子

        Args:
            factor_name: 因子名称

        Returns:
            单个宏观因子数据DataFrame
        """
        factor_file = self.factor_data_path / "macro" / f"{factor_name}.csv"

        if not factor_file.exists():
            logger.warning(f"宏观因子文件不存在: {factor_file}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(factor_file)
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            logger.debug(f"单个宏观因子加载完成: {factor_name}")
            return df

        except Exception as e:
            logger.error(f"单个宏观因子加载失败 {factor_name}: {e}")
            return pd.DataFrame()

    def load_economic_indicators(self, categories: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        按类别加载经济指标

        Args:
            categories: 指标类别列表，如['monetary', 'fiscal', 'market']

        Returns:
            按类别分组的经济指标数据
        """
        if categories is None:
            categories = ['monetary', 'fiscal', 'market', 'international']

        indicators = {}

        for category in categories:
            category_path = self.factor_data_path / "macro" / category

            if not category_path.exists():
                logger.warning(f"经济指标类别目录不存在: {category_path}")
                continue

            category_files = list(category_path.glob("*.csv"))
            if not category_files:
                continue

            category_data = pd.DataFrame()

            try:
                for indicator_file in category_files:
                    indicator_name = indicator_file.stem
                    indicator_df = pd.read_csv(indicator_file)

                    if 'trade_date' not in indicator_df.columns:
                        continue

                    indicator_df['trade_date'] = pd.to_datetime(indicator_df['trade_date'], format='%Y%m%d')

                    if 'value' in indicator_df.columns:
                        indicator_df = indicator_df.rename(columns={'value': indicator_name})

                    if category_data.empty:
                        category_data = indicator_df[['trade_date', indicator_name]].copy()
                    else:
                        category_data = pd.merge(
                            category_data,
                            indicator_df[['trade_date', indicator_name]],
                            on='trade_date',
                            how='outer'
                        )

                if not category_data.empty:
                    category_data = category_data.sort_values('trade_date')
                    indicators[category] = category_data

                logger.info(f"经济指标类别加载完成: {category}, 形状: {category_data.shape}")

            except Exception as e:
                logger.error(f"经济指标类别加载失败 {category}: {e}")

        return indicators

    def get_macro_data_summary(self) -> Dict:
        """
        获取宏观数据概要信息

        Returns:
            宏观数据概要信息
        """
        summary = {
            'total_factors': 0,
            'date_range': [None, None],
            'available_categories': [],
            'factor_list': []
        }

        try:
            # 获取所有宏观因子
            factor_list = self.get_macro_factor_list()
            summary['total_factors'] = len(factor_list)
            summary['factor_list'] = factor_list

            # 获取可用类别
            macro_path = self.factor_data_path / "macro"
            if macro_path.exists():
                categories = [d.name for d in macro_path.iterdir() if d.is_dir()]
                summary['available_categories'] = categories

            # 获取日期范围
            if factor_list:
                all_data = self.load_macro_factors()
                if not all_data.empty and 'trade_date' in all_data.columns:
                    summary['date_range'] = [
                        all_data['trade_date'].min().strftime('%Y-%m-%d'),
                        all_data['trade_date'].max().strftime('%Y-%m-%d')
                    ]

        except Exception as e:
            logger.error(f"获取宏观数据概要失败: {e}")

        return summary