#!/usr/bin/env python3
"""
日志管理模块
统一管理ETF数据系统的所有日志记录
"""

import os
import logging
from datetime import datetime
from typing import Optional
import json
from .smart_report_generator import SmartReportGenerator


class ETFLogger:
    """ETF系统日志管理器"""
    
    def __init__(self, base_dir: str = None):
        """初始化日志管理器"""
        if base_dir is None:
            # 自动定位到项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.base_dir = os.path.dirname(current_dir)  # 项目根目录
        else:
            self.base_dir = base_dir
            
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.loggers = {}  # 缓存不同类型的logger
        
        # 确保日志目录存在
        self._ensure_log_directories()
    
    def _ensure_log_directories(self):
        """确保日志目录存在"""
        log_subdirs = ["etf_operations", "factor_calculations", "system", "archives"]
        for subdir in log_subdirs:
            dir_path = os.path.join(self.logs_dir, subdir)
            os.makedirs(dir_path, exist_ok=True)
    
    def get_logger(self, logger_type: str, etf_code: Optional[str] = None) -> logging.Logger:
        """获取指定类型的logger"""
        logger_name = f"{logger_type}_{etf_code}" if etf_code else logger_type
        
        if logger_name in self.loggers:
            return self.loggers[logger_name]
        
        # 创建新的logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 文件处理器
            log_file = self._get_log_file_path(logger_type, etf_code)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 控制台处理器（可选）
            if logger_type == "system":
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.WARNING)  # 只显示警告和错误
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
        
        self.loggers[logger_name] = logger
        return logger
    
    def _get_log_file_path(self, logger_type: str, etf_code: Optional[str] = None) -> str:
        """获取日志文件路径"""
        today = datetime.now().strftime("%Y%m%d")
        
        if logger_type == "etf_operations":
            if etf_code:
                filename = f"etf_{etf_code}_{today}.log"
            else:
                filename = f"etf_operations_{today}.log"
            return os.path.join(self.logs_dir, "etf_operations", filename)
        
        elif logger_type == "factor_calculations":
            if etf_code:
                filename = f"factors_{etf_code}_{today}.log"
            else:
                filename = f"factor_calculations_{today}.log"
            return os.path.join(self.logs_dir, "factor_calculations", filename)
        
        elif logger_type == "system":
            filename = f"system_{today}.log"
            return os.path.join(self.logs_dir, "system", filename)
        
        else:
            # 默认系统日志
            filename = f"{logger_type}_{today}.log"
            return os.path.join(self.logs_dir, "system", filename)
    
    def log_operation(self, operation: str, etf_code: str, status: str, details: dict = None):
        """记录ETF操作日志"""
        logger = self.get_logger("etf_operations", etf_code)
        
        log_data = {
            "operation": operation,
            "etf_code": etf_code,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        # 格式化日志消息
        message = f"{operation} | {etf_code} | {status}"
        if details:
            message += f" | {json.dumps(details, ensure_ascii=False)}"
        
        # 判断日志级别
        status_lower = status.lower()
        if any(word in status_lower for word in ["success", "completed", "成功", "完成", "✅"]):
            logger.info(message)
        elif any(word in status_lower for word in ["warning", "warn", "警告", "⚠️"]):
            logger.warning(message)
        elif any(word in status_lower for word in ["error", "failed", "失败", "错误", "❌"]):
            logger.error(message)
        else:
            # 默认为info级别
            logger.info(message)
    
    def log_factor_calculation(self, etf_code: str, factor_name: str, status: str, 
                             duration: float = None, record_count: int = None):
        """记录因子计算日志"""
        logger = self.get_logger("factor_calculations", etf_code)
        
        details = {}
        if duration is not None:
            details["duration_seconds"] = round(duration, 2)
        if record_count is not None:
            details["record_count"] = record_count
        
        message = f"Factor Calculation | {etf_code} | {factor_name} | {status}"
        if details:
            message += f" | {json.dumps(details)}"
        
        # 判断日志级别
        status_lower = status.lower()
        if any(word in status_lower for word in ["success", "completed", "成功", "完成", "✅"]):
            logger.info(message)
        elif any(word in status_lower for word in ["warning", "warn", "警告", "⚠️"]):
            logger.warning(message)
        elif any(word in status_lower for word in ["error", "failed", "失败", "错误", "❌"]):
            logger.error(message)
        else:
            # 默认为info级别
            logger.info(message)
    
    def log_system_event(self, event_type: str, message: str, level: str = "info"):
        """记录系统事件日志"""
        logger = self.get_logger("system")
        
        log_message = f"{event_type} | {message}"
        
        if level.lower() == "info":
            logger.info(log_message)
        elif level.lower() == "warning":
            logger.warning(log_message)
        elif level.lower() == "error":
            logger.error(log_message)
        else:
            logger.info(log_message)
    
    def get_recent_logs(self, logger_type: str, etf_code: str = None, lines: int = 50) -> list:
        """获取最近的日志记录"""
        log_file = self._get_log_file_path(logger_type, etf_code)
        
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception:
            return []
    
    def clean_weekly_logs(self, keep_weeks: int = 2):
        """每周清理日志 - 保留指定周数的日志"""
        from datetime import timedelta
        import shutil
        import zipfile
        
        print(f"🧹 开始每周日志清理...")
        
        current_time = datetime.now()
        cutoff_date = current_time - timedelta(weeks=keep_weeks)
        
        cleaned_count = 0
        archived_count = 0
        archived_size = 0
        
        log_dirs = ["etf_operations", "factor_calculations", "system"]
        
        # 创建压缩归档
        archive_filename = f"logs_archive_{current_time.strftime('%Y%m%d_%H%M%S')}.zip"
        archive_path = os.path.join(self.logs_dir, "archives", archive_filename)
        
        # 用于压缩的临时文件列表
        files_to_archive = []
        
        for log_dir in log_dirs:
            dir_path = os.path.join(self.logs_dir, log_dir)
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.log'):
                    continue
                
                file_path = os.path.join(dir_path, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                
                if file_mtime < cutoff_date:
                    # 记录要归档的文件
                    files_to_archive.append({
                        'file_path': file_path,
                        'archive_name': f"{log_dir}/{filename}",
                        'size': file_size
                    })
                    archived_size += file_size
                    archived_count += 1
        
        # 创建压缩归档
        if files_to_archive:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files_to_archive:
                    zipf.write(file_info['file_path'], file_info['archive_name'])
                    print(f"  📦 归档: {file_info['archive_name']} ({file_info['size']:,} bytes)")
            
            # 删除原文件
            for file_info in files_to_archive:
                os.remove(file_info['file_path'])
                cleaned_count += 1
            
            compression_ratio = os.path.getsize(archive_path) / archived_size if archived_size > 0 else 0
            
            print(f"✅ 日志清理完成:")
            print(f"   📦 归档文件: {archive_filename}")
            print(f"   🗂️  清理文件数: {cleaned_count}")
            print(f"   💾 原始大小: {archived_size/1024:.1f} KB")
            print(f"   📋 压缩后: {os.path.getsize(archive_path)/1024:.1f} KB")
            print(f"   📈 压缩率: {compression_ratio:.1%}")
            
            # 记录清理事件
            self.log_system_event("WEEKLY_CLEANUP", 
                                f"清理了 {cleaned_count} 个日志文件，归档到 {archive_filename}", 
                                "info")
        else:
            print("✅ 无需清理的日志文件")
        
        return cleaned_count, archive_path if files_to_archive else None

    def auto_cleanup_on_startup(self):
        """系统启动时自动检查并清理日志"""
        try:
            # 检查是否需要清理
            cleanup_marker = os.path.join(self.logs_dir, ".last_cleanup")
            current_time = datetime.now()
            
            should_cleanup = True
            if os.path.exists(cleanup_marker):
                try:
                    with open(cleanup_marker, 'r') as f:
                        last_cleanup = datetime.fromisoformat(f.read().strip())
                    
                    # 检查是否已经过了一周
                    days_since_cleanup = (current_time - last_cleanup).days
                    if days_since_cleanup < 7:
                        should_cleanup = False
                        print(f"📅 距离上次清理 {days_since_cleanup} 天，无需清理")
                except:
                    should_cleanup = True
            
            if should_cleanup:
                print("🕐 检测到需要进行每周日志清理...")
                cleaned_count, archive_path = self.clean_weekly_logs()
                
                # 更新清理标记
                with open(cleanup_marker, 'w') as f:
                    f.write(current_time.isoformat())
                
                return cleaned_count > 0
            
            return False
            
        except Exception as e:
            print(f"⚠️  自动清理失败: {e}")
            self.log_system_event("CLEANUP_ERROR", f"自动清理失败: {e}", "warning")
            return False

    def archive_old_logs(self, days_old: int = 30):
        """归档旧日志文件 - 保留原有功能"""
        from datetime import timedelta
        import shutil
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        log_dirs = ["etf_operations", "factor_calculations", "system"]
        
        for log_dir in log_dirs:
            dir_path = os.path.join(self.logs_dir, log_dir)
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.log'):
                    continue
                
                file_path = os.path.join(dir_path, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    # 移动到归档目录
                    archive_path = os.path.join(self.logs_dir, "archives", filename)
                    shutil.move(file_path, archive_path)
                    archived_count += 1
        
        if archived_count > 0:
            self.log_system_event("ARCHIVE", f"Archived {archived_count} old log files")
        
        return archived_count
    
    def get_log_summary(self) -> dict:
        """获取日志系统摘要"""
        summary = {
            "log_directories": [],
            "total_files": 0,
            "total_size_mb": 0
        }
        
        log_dirs = ["etf_operations", "factor_calculations", "system", "archives"]
        
        for log_dir in log_dirs:
            dir_path = os.path.join(self.logs_dir, log_dir)
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith('.log')]
                dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
                
                summary["log_directories"].append({
                    "name": log_dir,
                    "file_count": len(files),
                    "size_mb": round(dir_size / 1024 / 1024, 2)
                })
                
                summary["total_files"] += len(files)
                summary["total_size_mb"] += dir_size / 1024 / 1024
        
        summary["total_size_mb"] = round(summary["total_size_mb"], 2)
        return summary
    
    def generate_smart_report(self) -> str:
        """生成智能分析报告并清理旧日志"""
        try:
            generator = SmartReportGenerator(self.logs_dir)
            return generator.generate_report()
        except Exception as e:
            print(f"❌ 生成智能报告失败: {e}")
            # 创建简单的错误报告
            error_report = f"""
=================================================================
🚀 ETF数据管理系统 - 每日运行报告 (错误版本)
=================================================================
📅 日期: {datetime.now().strftime('%Y-%m-%d')}
❌ 状态: 报告生成失败: {e}
📝 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=================================================================
"""
            try:
                report_file = os.path.join(self.logs_dir, "report.txt")
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(error_report)
            except:
                pass
            return error_report


# 全局日志管理器实例
_global_logger = None

def get_etf_logger() -> ETFLogger:
    """获取全局日志管理器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ETFLogger()
    return _global_logger