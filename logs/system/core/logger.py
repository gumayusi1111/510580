"""
主日志器 - 提供统一的日志接口
职责：协调各个模块，提供简洁的API接口
"""

from .formatter import LogFormatter
from ..handlers.file_handler import FileHandler
from ..handlers.summary_handler import SummaryHandler


class ETFLogger:
    """ETF日志系统主接口"""

    def __init__(self):
        self.formatter = LogFormatter()
        self.file_handler = FileHandler()
        self.summary_handler = SummaryHandler()

    def startup(self, etf_count: int, token_valid: bool):
        """记录系统启动"""
        log_msg = self.formatter.format_startup(etf_count, token_valid)
        self.file_handler.write_to_current(log_msg)

    def update_etf(self, etf_code: str, success: bool, records: int = 0,
                   duration: float = 0, error_msg: str = ""):
        """记录ETF数据更新"""
        log_msg = self.formatter.format_update(
            etf_code, success, records, duration, error_msg
        )

        # 写入当前日志
        self.file_handler.write_to_current(log_msg)

        # 如果是错误，也写入错误日志
        if not success:
            self.file_handler.write_to_errors(log_msg)

        # 更新汇总统计
        self.summary_handler.add_etf_update(etf_code, success, records)

    def factor_calculation(self, etf_code: str, success: bool, factors: int = 0,
                          duration: float = 0, error_msg: str = ""):
        """记录因子计算"""
        log_msg = self.formatter.format_factor(
            etf_code, success, factors, duration, error_msg
        )

        # 写入当前日志
        self.file_handler.write_to_current(log_msg)

        # 如果是错误，也写入错误日志
        if not success:
            self.file_handler.write_to_errors(log_msg)

        # 更新汇总统计
        self.summary_handler.add_factor_calculation(etf_code, success, factors)

    def error(self, component: str, error_msg: str):
        """记录错误事件"""
        log_msg = self.formatter.format_error(component, error_msg)

        # 写入当前日志和错误日志
        self.file_handler.write_to_current(log_msg)
        self.file_handler.write_to_errors(log_msg)

        # 更新错误统计
        self.summary_handler.add_error()

    def shutdown(self):
        """记录系统关闭并生成汇总"""
        # 获取统计信息
        stats = self.summary_handler.get_stats()

        # 记录关闭日志
        log_msg = self.formatter.format_shutdown(
            stats['duration'],
            stats['etf_count'],
            stats['total_records']
        )
        self.file_handler.write_to_current(log_msg)

        # 生成并写入汇总报告
        summary = self.summary_handler.generate_summary()
        self.file_handler.write_to_summary(summary)

    def get_file_paths(self) -> dict:
        """获取所有日志文件路径"""
        return self.file_handler.get_file_paths()


# 全局实例
_etf_logger = None

def get_etf_logger() -> ETFLogger:
    """获取ETF日志器全局实例"""
    global _etf_logger
    if _etf_logger is None:
        _etf_logger = ETFLogger()
    return _etf_logger