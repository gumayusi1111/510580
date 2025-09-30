"""
窗口配置模块
为不同交易策略提供优化的窗口参数
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class WindowConfig:
    """窗口配置类"""

    # IC分析窗口配置
    ic_windows: List[int]

    # 稳定性分析窗口
    stability_window: int

    # 主要分析窗口（用于排序和评级）
    primary_window: int

    # 策略描述
    description: str


# 预定义的策略窗口配置
STRATEGY_WINDOWS = {
    # 短线策略配置 - 推荐用于ETF择时
    'short_term': WindowConfig(
        ic_windows=[10, 20, 30],  # 多窗口IC分析
        stability_window=20,       # 20日稳定性分析
        primary_window=20,         # 主力窗口20日
        description="短线策略：适合1-4周交易周期，快速响应市场变化"
    ),

    # 超短线策略配置
    'ultra_short': WindowConfig(
        ic_windows=[5, 10, 15],
        stability_window=15,
        primary_window=10,
        description="超短线策略：适合日内到周级别交易，高敏感度"
    ),

    # 中短线策略配置
    'medium_short': WindowConfig(
        ic_windows=[15, 30, 45],
        stability_window=30,
        primary_window=30,
        description="中短线策略：平衡敏感性和稳定性，适合月级别交易"
    ),

    # 传统中线策略配置
    'medium_term': WindowConfig(
        ic_windows=[30, 60, 90],
        stability_window=60,
        primary_window=60,
        description="中线策略：传统60日窗口，适合季度级别交易"
    ),

    # 多时间框架综合配置
    'multi_timeframe': WindowConfig(
        ic_windows=[10, 20, 30, 60],  # 全时间框架
        stability_window=30,
        primary_window=20,
        description="多时间框架：综合短中长期信号，全面分析"
    )
}


def get_window_config(strategy_type: str = 'short_term') -> WindowConfig:
    """
    获取指定策略的窗口配置

    Args:
        strategy_type: 策略类型
            - 'short_term': 短线策略（推荐）
            - 'ultra_short': 超短线策略
            - 'medium_short': 中短线策略
            - 'medium_term': 传统中线策略
            - 'multi_timeframe': 多时间框架

    Returns:
        WindowConfig: 窗口配置对象
    """
    if strategy_type not in STRATEGY_WINDOWS:
        raise ValueError(f"未知的策略类型: {strategy_type}")

    return STRATEGY_WINDOWS[strategy_type]


def list_available_strategies() -> Dict[str, str]:
    """
    列出所有可用的策略配置

    Returns:
        Dict[str, str]: 策略名称和描述的映射
    """
    return {
        strategy: config.description
        for strategy, config in STRATEGY_WINDOWS.items()
    }


def validate_windows(windows: List[int], min_window: int = 5) -> bool:
    """
    验证窗口配置的合理性

    Args:
        windows: 窗口列表
        min_window: 最小窗口大小

    Returns:
        bool: 配置是否合理
    """
    if not windows:
        return False

    # 检查最小窗口大小
    if min(windows) < min_window:
        return False

    # 检查窗口是否按升序排列
    if windows != sorted(windows):
        return False

    return True