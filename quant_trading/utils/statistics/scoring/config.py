"""
评分系统配置
定义所有评分阈值和权重配置
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoringWeights:
    """
    评分权重配置 (第三版优化)

    Attributes:
        ic: IC表现权重，默认0.40 (降低从0.50，避免高IC低稳定因子虚高)
        stability: 稳定性权重，默认0.25 (提高从0.20，重视因子稳定性)
        data_quality: 数据质量权重，默认0.10
        distribution: 分布合理性权重，默认0.20 (提高从0.15，重视统计有效性)
        consistency: 一致性权重，默认0.05
    """
    ic: float = 0.40              # IC表现权重 (v3: 50%→40%)
    stability: float = 0.25       # 稳定性权重 (v3: 20%→25%)
    data_quality: float = 0.10    # 数据质量权重
    distribution: float = 0.20    # 分布合理性权重 (v3: 15%→20%)
    consistency: float = 0.05     # 一致性权重

    def __post_init__(self):
        """
        验证权重总和为1.0

        Raises:
            ValueError: 当权重总和不为1.0时抛出
        """
        total = self.ic + self.stability + self.data_quality + self.distribution + self.consistency
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"权重总和必须为1.0, 当前为{total:.3f}")


@dataclass
class ICThresholds:
    """
    IC强度评分阈值 (适用于标准化后的因子)

    Attributes:
        excellent: A级阈值，默认0.08
        good: B级阈值，默认0.05
        fair: C级阈值，默认0.03
        acceptable: D级阈值，默认0.02
        weak: E级阈值，默认0.01
        ir_excellent: IR优秀阈值，默认1.0
        ir_good: IR良好阈值，默认0.5
        win_rate_good: 胜率良好阈值，默认0.6
        win_rate_poor: 胜率较差阈值，默认0.4
    """
    excellent: float = 0.08      # A级: 极其优秀
    good: float = 0.05           # B级: 优秀
    fair: float = 0.03           # C级: 良好
    acceptable: float = 0.02     # D级: 可用
    weak: float = 0.01           # E级: 较弱

    # IR阈值
    ir_excellent: float = 1.0
    ir_good: float = 0.5

    # 胜率阈值
    win_rate_good: float = 0.6
    win_rate_poor: float = 0.4


@dataclass
class GradeThresholds:
    """
    评级阈值配置

    Attributes:
        grade_a: A级阈值，默认0.80
        grade_b: B级阈值，默认0.65
        grade_c: C级阈值，默认0.45
        grade_d: D级阈值，默认0.30
    """
    grade_a: float = 0.80    # A级: 优秀因子
    grade_b: float = 0.65    # B级: 良好因子
    grade_c: float = 0.45    # C级: 可用因子
    grade_d: float = 0.30    # D级: 较弱因子
    # F级: < 0.30


@dataclass
class DataQualityThresholds:
    """
    数据质量评分阈值

    Attributes:
        missing_perfect: 完美缺失率，默认0.00
        missing_excellent: 优秀缺失率，默认0.05
        missing_good: 良好缺失率，默认0.10
        missing_acceptable: 可接受缺失率，默认0.20
        outlier_excellent: 优秀异常值比例，默认0.02
        outlier_good: 良好异常值比例，默认0.05
        outlier_acceptable: 可接受异常值比例，默认0.10
        outlier_warning: 异常值警告比例，默认0.20
        cv_min: 最小变异系数，默认0.01
        cv_max: 最大变异系数，默认5.0
    """
    # 缺失率阈值
    missing_perfect: float = 0.00
    missing_excellent: float = 0.05
    missing_good: float = 0.10
    missing_acceptable: float = 0.20

    # 异常值比例阈值
    outlier_excellent: float = 0.02
    outlier_good: float = 0.05
    outlier_acceptable: float = 0.10
    outlier_warning: float = 0.20

    # 变异系数阈值
    cv_min: float = 0.01
    cv_max: float = 5.0


@dataclass
class DistributionThresholds:
    """
    分布评分阈值

    Attributes:
        skew_excellent: 优秀偏度阈值，默认1.0
        skew_good: 良好偏度阈值，默认2.0
        skew_acceptable: 可接受偏度阈值，默认3.0
        skew_warning: 偏度警告阈值，默认5.0
        skew_poor: 较差偏度阈值，默认8.0
        kurt_excellent: 优秀峰度阈值，默认3.0
        kurt_good: 良好峰度阈值，默认5.0
        kurt_acceptable: 可接受峰度阈值，默认8.0
        kurt_warning: 峰度警告阈值，默认12.0
        kurt_poor: 较差峰度阈值，默认20.0
    """
    # 偏度阈值
    skew_excellent: float = 1.0
    skew_good: float = 2.0
    skew_acceptable: float = 3.0
    skew_warning: float = 5.0
    skew_poor: float = 8.0

    # 峰度阈值
    kurt_excellent: float = 3.0
    kurt_good: float = 5.0
    kurt_acceptable: float = 8.0
    kurt_warning: float = 12.0
    kurt_poor: float = 20.0


class ScoringConfig:
    """
    评分系统全局配置

    Attributes:
        weights: 评分权重配置实例
        ic_thresholds: IC阈值配置实例
        grade_thresholds: 评级阈值配置实例
        quality_thresholds: 数据质量阈值配置实例
        distribution_thresholds: 分布阈值配置实例
    """

    def __init__(self):
        """初始化评分配置，创建所有阈值和权重实例"""
        self.weights = ScoringWeights()
        self.ic_thresholds = ICThresholds()
        self.grade_thresholds = GradeThresholds()
        self.quality_thresholds = DataQualityThresholds()
        self.distribution_thresholds = DistributionThresholds()

    def to_dict(self) -> Dict:
        """
        转换为字典

        Returns:
            包含所有配置信息的字典
        """
        return {
            'weights': {
                'ic': self.weights.ic,
                'stability': self.weights.stability,
                'data_quality': self.weights.data_quality,
                'distribution': self.weights.distribution,
                'consistency': self.weights.consistency
            },
            'ic_thresholds': self.ic_thresholds.__dict__,
            'grade_thresholds': self.grade_thresholds.__dict__,
            'quality_thresholds': self.quality_thresholds.__dict__,
            'distribution_thresholds': self.distribution_thresholds.__dict__
        }


# 默认配置实例
DEFAULT_CONFIG = ScoringConfig()