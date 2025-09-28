"""
汇总处理器 - 负责生成运行汇总信息
职责：收集运行统计信息并生成汇总报告
"""

import time
from typing import Set, Dict, Any


class SummaryHandler:
    """运行汇总处理器"""

    def __init__(self):
        self.start_time = time.time()
        self.stats = {
            'total_records': 0,
            'success_count': 0,
            'error_count': 0,
            'etf_processed': set(),
            'factors_calculated': 0
        }

    def add_etf_update(self, etf_code: str, success: bool, records: int = 0):
        """添加ETF更新统计"""
        if success:
            self.stats['total_records'] += records
            self.stats['success_count'] += 1
            self.stats['etf_processed'].add(etf_code)
        else:
            self.stats['error_count'] += 1

    def add_factor_calculation(self, etf_code: str, success: bool, factors: int = 0):
        """添加因子计算统计"""
        if success:
            self.stats['factors_calculated'] += factors
            self.stats['success_count'] += 1
        else:
            self.stats['error_count'] += 1

    def add_error(self):
        """添加错误统计"""
        self.stats['error_count'] += 1

    def get_total_duration(self) -> float:
        """获取总运行时长（秒）"""
        return round(time.time() - self.start_time, 1)

    def generate_summary(self) -> str:
        """生成运行汇总报告"""
        duration = self.get_total_duration()
        etf_count = len(self.stats['etf_processed'])
        records = self.stats['total_records']
        factors = self.stats['factors_calculated']
        errors = self.stats['error_count']

        summary_lines = [
            f"运行时间: {duration}s",
            f"处理ETF: {etf_count}个",
            f"获取数据: {records}条记录",
            f"计算因子: {factors}个",
            f"错误数量: {errors}"
        ]

        if self.stats['etf_processed']:
            etf_list = ", ".join(sorted(self.stats['etf_processed']))
            summary_lines.append(f"ETF列表: {etf_list}")

        return "\n".join(summary_lines)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'duration': self.get_total_duration(),
            'etf_count': len(self.stats['etf_processed']),
            'total_records': self.stats['total_records'],
            'factors_calculated': self.stats['factors_calculated'],
            'success_count': self.stats['success_count'],
            'error_count': self.stats['error_count']
        }