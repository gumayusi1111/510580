#!/usr/bin/env python3
"""
ETF操作模块 - 负责高级ETF操作
职责：批量更新、添加新ETF、删除ETF、状态显示
"""

import os
import shutil
# 日志系统通过ETFManager传递，无需直接导入


class ETFOperations:
    """ETF操作器 - 单一职责：高级ETF操作"""
    
    def __init__(self, discovery, updater, data_processor):
        """初始化操作器"""
        self.discovery = discovery
        self.updater = updater
        self.processor = data_processor
        # 如果updater支持因子计算，获取因子计算器
        self.factor_calculator = getattr(updater, 'factor_calculator', None)
        # 如果updater支持基本面数据，获取基本面数据管理器
        self.fundamental_manager = getattr(updater, 'fundamental_manager', None)
        # 日志器将通过ETFManager传递
        self.logger = None
    
    def update_all_existing(self):
        """更新所有现有ETF"""
        existing_etfs = self.discovery.get_existing_etfs()
        
        if not existing_etfs:
            return 0, 0, "暂无现有ETF数据"
        
        print(f"\n🔄 开始更新 {len(existing_etfs)} 个ETF...")
        print(f"ETF列表: {', '.join(existing_etfs)}")
        
        success_count = 0
        for etf_code in existing_etfs:
            print(f"\n{'='*40}")
            print(f"更新 ETF: {etf_code}")
            print(f"{'='*40}")
            
            full_code = self.discovery.normalize_etf_code(etf_code)
            success, message = self.updater.update_etf_incremental(full_code)
            
            if success:
                print(f"✅ {message}")
                success_count += 1
            else:
                print(f"❌ {message}")
        
        return success_count, len(existing_etfs), f"批量更新完成"
    
    def add_new_etf(self, etf_code):
        """添加新ETF"""
        # 验证代码格式
        is_valid, error_msg = self.discovery.validate_etf_code_format(etf_code)
        if not is_valid:
            return False, error_msg
        
        full_code = self.discovery.normalize_etf_code(etf_code)
        code_only = self.discovery._extract_code(etf_code)
        
        # 检查是否已存在
        if self.discovery.etf_exists(etf_code):
            print(f"⚠️ ETF {etf_code} 已存在")
            confirm = input("输入 'y' 重新获取全部数据，其他键取消: ").lower()
            if confirm != 'y':
                return False, "用户取消操作"
        
        print(f"\n➕ 添加新ETF: {etf_code}")
        success, message = self.updater.update_etf_full(full_code)
        
        if success:
            return True, f"成功添加ETF {etf_code}: {message}"
        else:
            return False, f"添加ETF {etf_code} 失败: {message}"
    
    def delete_etf(self, etf_code):
        """删除ETF及其所有数据（包括对应的因子数据）"""
        if not self.discovery.etf_exists(etf_code):
            if self.logger:
                self.logger.error("DELETE_ETF", f"ETF {etf_code} 不存在")
            return False, f"ETF {etf_code} 不存在"
        
        code_only = self.discovery._extract_code(etf_code)
        etf_dir = os.path.join(self.processor.data_dir, code_only)
        
        try:
            # 显示将要删除的ETF数据文件
            files = os.listdir(etf_dir)
            print(f"\n🗑️ 将删除 ETF {etf_code} 的以下数据:")
            print("📊 ETF数据文件:")
            for file in files:
                file_size = os.path.getsize(os.path.join(etf_dir, file))
                print(f"   - {file} ({file_size:,} 字节)")
            
            # 检查并显示对应的因子数据和基本面数据
            factor_info = self._check_factor_data(etf_code)
            fundamental_info = self._check_fundamental_data(etf_code)

            if factor_info['exists']:
                print(f"\n📈 技术因子数据文件:")
                print(f"   - 因子目录: etf_factor/factor_data/technical/{code_only}/")
                print(f"   - 因子文件数: {factor_info['file_count']}")
                print(f"   - 示例因子: {', '.join(factor_info['sample_factors'])}")

            if fundamental_info['exists']:
                print(f"\n📊 基本面数据文件:")
                print(f"   - 基本面目录: etf_factor/factor_data/fundamental/{code_only}/")
                print(f"   - 基本面文件数: {fundamental_info['file_count']}")
                print(f"   - 可用数据: {', '.join(fundamental_info['available_data'])}")
            
            # 确认删除
            data_types = []
            if factor_info['exists']:
                data_types.append("技术因子")
            if fundamental_info['exists']:
                data_types.append("基本面数据")

            if data_types:
                delete_msg = f"所有数据和对应的{'/'.join(data_types)}"
            else:
                delete_msg = "所有数据"

            confirm = input(f"\n确认删除 ETF {etf_code} 的{delete_msg}? (输入 'DELETE' 或 'delete' 确认): ")
            if confirm.upper() != 'DELETE':
                return False, "用户取消删除操作"
            
            # 删除ETF数据
            shutil.rmtree(etf_dir)
            print(f"✅ 已删除ETF数据: {etf_dir}")
            
            # 删除对应的因子数据和基本面数据
            cleanup_results = []

            if factor_info['exists'] and self.factor_calculator:
                factor_success = self.factor_calculator.cleanup_factor_data(etf_code)
                if factor_success:
                    print(f"✅ 已删除对应的技术因子数据")
                    cleanup_results.append("技术因子清理成功")
                else:
                    print(f"⚠️ 技术因子清理失败")
                    cleanup_results.append("技术因子清理失败")

            if fundamental_info['exists'] and self.fundamental_manager:
                fundamental_success = self.fundamental_manager.cleanup_fundamental_data(etf_code)
                if fundamental_success:
                    print(f"✅ 已删除对应的基本面数据")
                    cleanup_results.append("基本面数据清理成功")
                else:
                    print(f"⚠️ 基本面数据清理失败")
                    cleanup_results.append("基本面数据清理失败")

            # 生成返回消息
            if cleanup_results:
                cleanup_msg = ", ".join(cleanup_results)
                all_success = all("成功" in result for result in cleanup_results)
                if all_success:
                    return True, f"成功删除 ETF {etf_code} 的所有数据和相关因子数据"
                else:
                    return True, f"ETF {etf_code} 数据已删除，但部分清理失败: {cleanup_msg}"
            
            return True, f"成功删除 ETF {etf_code} 的所有数据"
            
        except Exception as e:
            return False, f"删除失败: {e}"
    
    def _check_factor_data(self, etf_code):
        """检查ETF对应的因子数据"""
        info = {
            'exists': False,
            'file_count': 0,
            'sample_factors': []
        }
        
        try:
            if self.factor_calculator:
                summary = self.factor_calculator.get_factor_summary(etf_code)
                info['exists'] = summary['factor_files'] > 0
                info['file_count'] = summary['factor_files']
                info['sample_factors'] = summary['available_factors'][:3]  # 显示前3个
        except Exception:
            pass  # 忽略错误，可能因子系统不可用
        
        return info

    def _check_fundamental_data(self, etf_code):
        """检查ETF对应的基本面数据"""
        info = {
            'exists': False,
            'file_count': 0,
            'available_data': []
        }

        try:
            if self.fundamental_manager:
                summary = self.fundamental_manager.get_fundamental_summary(etf_code)
                info['exists'] = summary['fundamental_files'] > 0
                info['file_count'] = summary['fundamental_files']
                info['available_data'] = [data['type'] for data in summary['available_data'][:3]]  # 显示前3个
        except Exception:
            pass  # 忽略错误，可能基本面系统不可用

        return info
    
    def show_all_etf_status(self):
        """显示所有ETF状态"""
        existing_etfs = self.discovery.get_existing_etfs()
        
        if not existing_etfs:
            print("📭 暂无ETF数据")
            return
        
        print(f"\n📊 当前管理的ETF ({len(existing_etfs)} 个):")
        print("-" * 70)
        print(f"{'代码':>8} | {'最新日期':>10} | {'记录数':>6} | {'日期范围':>20}")
        print("-" * 70)
        
        for etf_code in existing_etfs:
            stats = self.discovery.get_etf_stats(etf_code, self.processor)
            print(f"{stats['code']:>8} | {stats['latest_date']:>10} | "
                  f"{stats['record_count']:>6} | {stats['date_range']:>20}")
        
        print("-" * 70)
    
    def get_summary(self):
        """获取系统摘要信息"""
        existing_etfs = self.discovery.get_existing_etfs()
        total_records = 0
        
        for etf_code in existing_etfs:
            stats = self.discovery.get_etf_stats(etf_code, self.processor)
            total_records += stats['record_count']
        
        return {
            'etf_count': len(existing_etfs),
            'total_records': total_records,
            'etf_codes': existing_etfs
        }