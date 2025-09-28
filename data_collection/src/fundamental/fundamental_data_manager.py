#!/usr/bin/env python3
"""
基本面数据管理器
负责ETF基本面数据的获取、更新和管理
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import yaml


class FundamentalDataManager:
    """ETF基本面数据管理器"""

    def __init__(self, tushare_client=None):
        """
        初始化基本面数据管理器

        Args:
            tushare_client: Tushare API客户端
        """
        self.client = tushare_client
        self.logger = None

        # 获取项目根目录和配置
        script_dir = Path(__file__).parent.parent
        self.project_root = script_dir.parent
        self.factor_data_path = self.project_root / "etf_factor" / "factor_data"

        # 加载全局配置
        self._load_config()

    def _load_config(self):
        """加载全局配置"""
        try:
            config_path = self.project_root / "etf_factor" / "config" / "global.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            # 使用默认配置
            self.config = {
                'precision': {
                    'price': 4,
                    'indicator': 4,
                    'percentage': 4,
                    'statistics': 4,
                    'default': 4
                }
            }

    def get_etf_fundamental_data(self, etf_code: str, incremental: bool = True) -> bool:
        """
        获取ETF基本面数据

        Args:
            etf_code: ETF代码 (如 '510580.SH')
            incremental: 是否增量更新

        Returns:
            bool: 是否成功
        """
        if not self.client:
            print("❌ Tushare客户端未初始化")
            return False

        try:
            etf_num = etf_code.replace('.SH', '').replace('.SZ', '')
            fund_dir = self.factor_data_path / "fundamental" / etf_num
            fund_dir.mkdir(parents=True, exist_ok=True)

            print(f"📊 获取 {etf_code} 基本面数据...")

            success = True

            # 1. 获取ETF净值数据
            if self._get_etf_nav_data(etf_code, fund_dir, incremental):
                print("  ✅ ETF净值数据获取完成")
            else:
                print("  ⚠️ ETF净值数据获取失败")
                success = False

            # 2. 获取指数估值数据
            if self._get_index_valuation_data(etf_code, fund_dir, incremental):
                print("  ✅ 指数估值数据获取完成")
            else:
                print("  ⚠️ 指数估值数据获取失败")

            # 3. 获取ETF份额数据
            if self._get_etf_share_data(etf_code, fund_dir, incremental):
                print("  ✅ ETF份额数据获取完成")
            else:
                print("  ⚠️ ETF份额数据获取失败")

            # 4. 获取宏观数据（所有ETF共享）
            if self._get_macro_data(incremental):
                print("  ✅ 宏观数据更新完成")
            else:
                print("  ⚠️ 宏观数据更新失败")

            return success

        except Exception as e:
            print(f"❌ 获取基本面数据失败: {e}")
            return False

    def _get_etf_nav_data(self, etf_code: str, fund_dir: Path, incremental: bool) -> bool:
        """获取ETF净值数据"""
        try:
            file_path = fund_dir / "ETF_NAV.csv"

            # 确定查询日期范围
            start_date = "20220101"  # 默认起始日期
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty:
                    # 从最新日期开始增量更新
                    latest_date = existing_df['trade_date'].max()
                    start_date = str(int(latest_date) + 1)  # 下一天开始

            end_date = datetime.now().strftime('%Y%m%d')

            # 调用Tushare API获取净值数据
            nav_df = self.client.fund_nav(ts_code=etf_code, start_date=start_date, end_date=end_date)

            if nav_df.empty:
                if incremental:
                    return True  # 增量更新时没有新数据是正常的
                else:
                    return False

            # 计算因子
            nav_df = self._calculate_nav_factors(nav_df)

            # 应用精度配置
            nav_df = self._apply_precision(nav_df, 'nav')

            # 数据合并和保存
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                # 合并数据，去重
                combined_df = pd.concat([existing_df, nav_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')
            else:
                combined_df = nav_df

            # 按日期倒序排列
            combined_df['trade_date'] = combined_df['trade_date'].astype(str)
            combined_df = combined_df.sort_values('trade_date', ascending=False).reset_index(drop=True)

            combined_df.to_csv(file_path, index=False, encoding='utf-8')
            return True

        except Exception as e:
            print(f"  获取净值数据时出错: {e}")
            return False

    def _get_index_valuation_data(self, etf_code: str, fund_dir: Path, incremental: bool) -> bool:
        """获取指数估值数据"""
        try:
            # ETF对应的指数代码映射
            index_mapping = {
                '510300.SH': '000300.SH',  # 沪深300
                '510580.SH': '000905.SH',  # 中证500
                '513180.SH': 'HSTECH.HI'   # 恒生科技
            }

            index_code = index_mapping.get(etf_code)
            if not index_code:
                print(f"  未找到 {etf_code} 对应的指数代码")
                return False

            # 跳过无法获取的指数
            if index_code == 'HSTECH.HI':
                print(f"  跳过 {index_code} (暂不支持)")
                return True

            file_path = fund_dir / "INDEX_VALUATION.csv"

            # 确定查询日期范围
            start_date = "20220101"
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty:
                    latest_date = existing_df['trade_date'].max()
                    start_date = str(int(latest_date) + 1)

            end_date = datetime.now().strftime('%Y%m%d')

            # 获取指数估值数据
            val_df = self.client.index_dailybasic(ts_code=index_code, start_date=start_date, end_date=end_date)

            if val_df.empty:
                if incremental:
                    return True
                else:
                    return False

            # 计算因子
            val_df = self._calculate_valuation_factors(val_df)

            # 应用精度配置
            val_df = self._apply_precision(val_df, 'valuation')

            # 数据合并和保存
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                combined_df = pd.concat([existing_df, val_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')
            else:
                combined_df = val_df

            # 按日期倒序排列
            combined_df['trade_date'] = combined_df['trade_date'].astype(str)
            combined_df = combined_df.sort_values('trade_date', ascending=False).reset_index(drop=True)

            combined_df.to_csv(file_path, index=False, encoding='utf-8')
            return True

        except Exception as e:
            print(f"  获取指数估值数据时出错: {e}")
            return False

    def _get_etf_share_data(self, etf_code: str, fund_dir: Path, incremental: bool) -> bool:
        """获取ETF份额数据"""
        try:
            file_path = fund_dir / "ETF_SHARE.csv"

            # 确定查询日期范围
            start_date = "20220101"
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty:
                    latest_date = existing_df['trade_date'].max()
                    start_date = str(int(latest_date) + 1)

            end_date = datetime.now().strftime('%Y%m%d')

            # 获取基金份额数据
            share_df = self.client.fund_share(ts_code=etf_code, start_date=start_date, end_date=end_date)

            if share_df.empty:
                if incremental:
                    return True
                else:
                    return False

            # 计算因子
            share_df = self._calculate_share_factors(share_df)

            # 应用精度配置
            share_df = self._apply_precision(share_df, 'share')

            # 数据合并和保存
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                combined_df = pd.concat([existing_df, share_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')
            else:
                combined_df = share_df

            # 按日期倒序排列
            combined_df['trade_date'] = combined_df['trade_date'].astype(str)
            combined_df = combined_df.sort_values('trade_date', ascending=False).reset_index(drop=True)

            combined_df.to_csv(file_path, index=False, encoding='utf-8')
            return True

        except Exception as e:
            print(f"  获取份额数据时出错: {e}")
            return False

    def _get_macro_data(self, incremental: bool) -> bool:
        """获取宏观数据"""
        try:
            macro_dir = self.factor_data_path / "macro"
            macro_dir.mkdir(parents=True, exist_ok=True)
            file_path = macro_dir / "SHIBOR_RATES.csv"

            # 确定查询日期范围
            start_date = "20231001"  # SHIBOR数据相对较新
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty:
                    latest_date = existing_df['trade_date'].max()
                    start_date = str(int(latest_date) + 1)

            end_date = datetime.now().strftime('%Y%m%d')

            # 获取SHIBOR利率数据
            shibor_df = self.client.shibor(start_date=start_date, end_date=end_date)

            if shibor_df.empty:
                if incremental:
                    return True
                else:
                    return False

            # 重命名列
            if 'date' in shibor_df.columns:
                shibor_df.rename(columns={'date': 'trade_date'}, inplace=True)

            # 应用精度配置
            shibor_df = self._apply_precision(shibor_df, 'macro')

            # 数据合并和保存
            if incremental and file_path.exists():
                existing_df = pd.read_csv(file_path)
                combined_df = pd.concat([existing_df, shibor_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['trade_date'], keep='last')
            else:
                combined_df = shibor_df

            # 按日期倒序排列
            combined_df['trade_date'] = combined_df['trade_date'].astype(str)
            combined_df = combined_df.sort_values('trade_date', ascending=False).reset_index(drop=True)

            combined_df.to_csv(file_path, index=False, encoding='utf-8')
            return True

        except Exception as e:
            print(f"  获取宏观数据时出错: {e}")
            return False

    def _calculate_nav_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算净值相关因子"""
        if df.empty:
            return df

        df = df.copy()
        df = df.sort_values('trade_date').reset_index(drop=True)

        # 净值收益率
        df['NAV_RETURN'] = df['adj_nav'].pct_change()

        # 净值移动平均
        df['NAV_MA_5'] = df['adj_nav'].rolling(window=5).mean()
        df['NAV_MA_20'] = df['adj_nav'].rolling(window=20).mean()

        # 净值波动率
        df['NAV_STD_20'] = df['NAV_RETURN'].rolling(window=20).std()

        return df

    def _calculate_valuation_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算估值相关因子"""
        if df.empty:
            return df

        df = df.copy()
        df = df.sort_values('trade_date').reset_index(drop=True)

        # PE/PB百分位数（需要历史数据计算）
        df['PE_PERCENTILE'] = df['pe'].rolling(window=252, min_periods=30).rank(pct=True)
        df['PB_PERCENTILE'] = df['pb'].rolling(window=252, min_periods=30).rank(pct=True)

        # PE/PB移动平均
        df['PE_MA_20'] = df['pe'].rolling(window=20).mean()
        df['PB_MA_20'] = df['pb'].rolling(window=20).mean()

        return df

    def _calculate_share_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算份额相关因子"""
        if df.empty:
            return df

        df = df.copy()
        df = df.sort_values('trade_date').reset_index(drop=True)

        # 份额变化
        df['SHARE_CHANGE'] = df['fd_share'].diff()
        df['SHARE_CHANGE_PCT'] = df['fd_share'].pct_change()

        # 份额移动平均
        df['SHARE_MA_5'] = df['fd_share'].rolling(window=5).mean()

        return df

    def _apply_precision(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """应用精度配置"""
        if df.empty:
            return df

        precision = self.config['precision']

        if data_type == 'nav':
            # 净值数据精度
            price_cols = ['unit_nav', 'accum_nav', 'accum_div', 'net_asset', 'total_netasset', 'adj_nav']
            for col in price_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['price'])

            factor_cols = ['NAV_RETURN', 'NAV_MA_5', 'NAV_MA_20', 'NAV_STD_20']
            for col in factor_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['indicator'])

        elif data_type == 'valuation':
            # 估值数据精度
            valuation_cols = ['pe', 'pb', 'pe_ttm', 'pb_mrq']
            for col in valuation_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['indicator'])

            ratio_cols = ['turnover_rate', 'volume_ratio']
            for col in ratio_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['percentage'])

            percentile_cols = ['PE_PERCENTILE', 'PB_PERCENTILE']
            for col in percentile_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['statistics'])

            ma_cols = ['PE_MA_20', 'PB_MA_20']
            for col in ma_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['indicator'])

        elif data_type == 'share':
            # 份额数据精度
            share_cols = ['fd_share']
            for col in share_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['default'])

            change_cols = ['SHARE_CHANGE', 'SHARE_CHANGE_PCT']
            for col in change_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['percentage'])

            ma_cols = ['SHARE_MA_5']
            for col in ma_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['default'])

        elif data_type == 'macro':
            # 宏观数据精度
            rate_cols = ['1m', '3m', '6m', '9m', '1y', '2w', '1w', 'on']
            for col in rate_cols:
                if col in df.columns:
                    df[col] = df[col].round(precision['percentage'])

        return df

    def cleanup_fundamental_data(self, etf_code: str) -> bool:
        """清理ETF基本面数据"""
        try:
            etf_num = etf_code.replace('.SH', '').replace('.SZ', '')
            fund_dir = self.factor_data_path / "fundamental" / etf_num

            if fund_dir.exists():
                import shutil
                shutil.rmtree(fund_dir)
                print(f"✅ 已删除基本面数据: {fund_dir}")
                return True
            else:
                print(f"⚠️ 基本面数据目录不存在: {fund_dir}")
                return True

        except Exception as e:
            print(f"❌ 清理基本面数据失败: {e}")
            return False

    def get_fundamental_summary(self, etf_code: str) -> dict:
        """获取基本面数据摘要"""
        try:
            etf_num = etf_code.replace('.SH', '').replace('.SZ', '')
            fund_dir = self.factor_data_path / "fundamental" / etf_num

            summary = {
                'etf_code': etf_code,
                'fundamental_files': 0,
                'latest_date': 'N/A',
                'available_data': []
            }

            if not fund_dir.exists():
                return summary

            # 统计文件
            csv_files = list(fund_dir.glob("*.csv"))
            summary['fundamental_files'] = len(csv_files)

            # 获取可用数据类型和最新日期
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    if not df.empty and 'trade_date' in df.columns:
                        latest_date = str(df['trade_date'].max())
                        summary['available_data'].append({
                            'type': csv_file.stem,
                            'records': len(df),
                            'latest_date': latest_date
                        })

                        # 更新总体最新日期
                        if summary['latest_date'] == 'N/A' or latest_date > summary['latest_date']:
                            summary['latest_date'] = latest_date
                except Exception:
                    continue

            return summary

        except Exception as e:
            print(f"❌ 获取基本面数据摘要失败: {e}")
            return {
                'etf_code': etf_code,
                'fundamental_files': 0,
                'latest_date': 'N/A',
                'available_data': []
            }