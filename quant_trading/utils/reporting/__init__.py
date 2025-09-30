"""
报告生成模块 - 重构版本
整合报告模板和生成器功能
"""

from .generator import ReportGenerator
from .templates import MarkdownTemplate
from .formatter import ReportFormatter

__all__ = ["ReportGenerator", "MarkdownTemplate", "ReportFormatter"]