"""
日志格式化器 - 负责统一的日志格式化
职责：根据不同类型格式化日志消息
"""

from datetime import datetime
from typing import Dict, Any
from .config_manager import ConfigManager


class LogFormatter:
    """日志格式化器"""

    def __init__(self):
        self.config = ConfigManager()

    def format_log(self, level: str, module: str, message: str,
                  log_type: str = "current") -> str:
        """
        格式化日志消息

        Args:
            level: 日志级别 (STARTUP, UPDATE, FACTOR, ERROR, SHUTDOWN)
            module: 模块名称 (SYSTEM, ETF, CALC)
            message: 日志消息
            log_type: 日志类型 (current, summary, error)
        """
        timestamp = self._get_timestamp()
        template = self.config.get_template(log_type)

        return template.format(
            time=timestamp,
            level=level,
            module=module,
            message=message
        )

    def _get_timestamp(self) -> str:
        """获取格式化的时间戳"""
        fmt = self.config.get_timestamp_format()
        return datetime.now().strftime(fmt)

    def format_startup(self, etf_count: int, token_valid: bool) -> str:
        """格式化启动日志"""
        token_status = "Token验证通过" if token_valid else "Token验证失败"
        message = f"{token_status}, 管理{etf_count}个ETF"
        return self.format_log("STARTUP", "SYSTEM", message)

    def format_update(self, etf_code: str, success: bool,
                     records: int = 0, duration: float = 0,
                     error_msg: str = "") -> str:
        """格式化ETF更新日志"""
        if success:
            message = f"{etf_code}: 获取{records}条数据, 耗时{duration}s"
            return self.format_log("UPDATE", "ETF", message)
        else:
            message = f"{etf_code}: {error_msg}"
            return self.format_log("UPDATE", "ETF", message, "error")

    def format_factor(self, etf_code: str, success: bool,
                     factors: int = 0, duration: float = 0,
                     error_msg: str = "") -> str:
        """格式化因子计算日志"""
        if success:
            message = f"{etf_code}: 计算{factors}个因子, 耗时{duration}s"
            return self.format_log("FACTOR", "CALC", message)
        else:
            message = f"{etf_code}: 因子计算失败 - {error_msg}"
            return self.format_log("FACTOR", "CALC", message, "error")

    def format_error(self, component: str, error_msg: str) -> str:
        """格式化错误日志"""
        message = f"{component}: {error_msg}"
        return self.format_log("ERROR", "SYSTEM", message, "error")

    def format_shutdown(self, total_duration: float, etf_count: int,
                       total_records: int) -> str:
        """格式化关闭日志"""
        message = f"总耗时{total_duration}s, 处理{etf_count}个ETF, 获取{total_records}条记录"
        return self.format_log("SHUTDOWN", "SYSTEM", message)