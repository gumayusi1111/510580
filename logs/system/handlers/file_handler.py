"""
文件处理器 - 负责日志文件的写入和管理
职责：管理日志文件的创建、清理和写入
"""

import os
from typing import List
from ..core.config_manager import ConfigManager


class FileHandler:
    """日志文件处理器"""

    def __init__(self):
        self.config = ConfigManager()
        self._ensure_output_directory()
        if self.config.should_clear_on_start():
            self._clear_all_logs()

    def _ensure_output_directory(self):
        """确保输出目录存在"""
        output_dir = self.config.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

    def _clear_all_logs(self):
        """清空所有日志文件"""
        file_types = ['current', 'summary', 'errors']
        for file_type in file_types:
            self._clear_log_file(file_type)

    def _clear_log_file(self, file_type: str):
        """清空指定的日志文件"""
        try:
            file_path = self.config.get_file_path(file_type)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
        except Exception:
            pass  # 忽略清空失败

    def write_to_current(self, content: str):
        """写入当前运行日志"""
        self._write_to_file('current', content)

    def write_to_summary(self, content: str):
        """写入汇总日志"""
        self._write_to_file('summary', content)

    def write_to_errors(self, content: str):
        """写入错误日志"""
        self._write_to_file('errors', content)

    def _write_to_file(self, file_type: str, content: str):
        """写入指定类型的日志文件"""
        try:
            file_path = self.config.get_file_path(file_type)
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
        except Exception:
            pass  # 忽略写入失败

    def get_file_paths(self) -> dict:
        """获取所有日志文件路径"""
        return {
            'current': self.config.get_file_path('current'),
            'summary': self.config.get_file_path('summary'),
            'errors': self.config.get_file_path('errors')
        }