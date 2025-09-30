"""
评级分配模块
负责根据总分分配因子评级
"""

import logging
from typing import Dict
from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class FactorGrader:
    """
    因子评级器

    负责根据总分和IC结果分配因子评级

    Attributes:
        config: 评分配置实例
        thresholds: 评级阈值配置
    """

    def __init__(self, config=None):
        """
        初始化因子评级器

        Args:
            config: 评分配置实例，默认使用DEFAULT_CONFIG
        """
        self.config = config or DEFAULT_CONFIG
        self.thresholds = self.config.grade_thresholds

    def assign_grade(self, total_score: float, ic_results: Dict) -> str:
        """
        分配因子评级

        Args:
            total_score: 总分
            ic_results: IC分析结果

        Returns:
            评级 (A/B/C/D/F)
        """
        t = self.thresholds

        # 基础评级
        if total_score >= t.grade_a:
            grade = 'A'
        elif total_score >= t.grade_b:
            grade = 'B'
        elif total_score >= t.grade_c:
            grade = 'C'
        elif total_score >= t.grade_d:
            grade = 'D'
        else:
            grade = 'F'

        # 智能验证机制 - 基于综合表现而非单一IC指标
        if ic_results and 'statistics' in ic_results and 'period_1' in ic_results['statistics']:
            ic_stats = ic_results['statistics']['period_1']
            sample_size = ic_stats.get('sample_size', 0)

            # 只在极端情况下降级
            if sample_size < 10 and total_score < 0.8:
                if grade == 'A':
                    grade = 'B'
                    logger.info(f"样本量过少({sample_size})且总分不够高({total_score:.3f})，A级降为B级")
            elif sample_size == 0 and total_score < 0.75:
                if grade == 'A':
                    grade = 'B'
                    logger.info(f"IC计算失败且替代评分不够高({total_score:.3f})，A级降为B级")

        return grade

    def get_grade_details(self, grade: str) -> Dict:
        """
        获取评级详细信息

        Args:
            grade: 评级

        Returns:
            评级详情字典
        """
        grade_info = {
            'A': {
                'description': 'ETF优秀因子',
                'usage': '核心策略因子',
                'confidence': 'high',
                'ic_range': '≥5%'
            },
            'B': {
                'description': 'ETF良好因子',
                'usage': '主要策略因子',
                'confidence': 'medium-high',
                'ic_range': '3-5%'
            },
            'C': {
                'description': 'ETF可用因子',
                'usage': '辅助策略因子',
                'confidence': 'medium',
                'ic_range': '2-3%'
            },
            'D': {
                'description': 'ETF较弱因子',
                'usage': '谨慎使用',
                'confidence': 'low',
                'ic_range': '1-2%'
            },
            'F': {
                'description': '无效因子',
                'usage': '不建议使用',
                'confidence': 'very-low',
                'ic_range': '<1%'
            }
        }
        return grade_info.get(grade, grade_info['F'])