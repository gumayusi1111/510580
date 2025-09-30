"""
基础策略类
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """基础策略抽象类"""

    def __init__(self, name: str):
        """
        初始化策略

        Args:
            name: 策略名称
        """
        self.name = name
        self.signals = pd.Series(dtype=float)
        self.positions = pd.Series(dtype=float)

    @abstractmethod
    def generate_signals(self, factor_data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        Args:
            factor_data: 因子数据

        Returns:
            交易信号序列 (1: 买入, -1: 卖出, 0: 持有)
        """
        pass

    @abstractmethod
    def calculate_positions(self, signals: pd.Series) -> pd.Series:
        """
        根据信号计算仓位

        Args:
            signals: 交易信号序列

        Returns:
            仓位序列
        """
        pass

    def backtest(self, factor_data: pd.DataFrame, returns: pd.Series) -> Dict:
        """
        策略回测

        Args:
            factor_data: 因子数据
            returns: 收益率数据

        Returns:
            回测结果
        """
        # 生成信号
        self.signals = self.generate_signals(factor_data)

        # 计算仓位
        self.positions = self.calculate_positions(self.signals)

        # 计算策略收益
        strategy_returns = self.positions.shift(1) * returns

        # 计算绩效指标
        performance = self._calculate_performance(strategy_returns, returns)

        return {
            'strategy_name': self.name,
            'signals': self.signals,
            'positions': self.positions,
            'strategy_returns': strategy_returns,
            'performance': performance
        }

    def _calculate_performance(self, strategy_returns: pd.Series,
                             benchmark_returns: pd.Series) -> Dict:
        """
        计算策略绩效指标

        Args:
            strategy_returns: 策略收益率
            benchmark_returns: 基准收益率

        Returns:
            绩效指标字典
        """
        # 基本统计
        total_return = (1 + strategy_returns).prod() - 1
        annual_return = (1 + strategy_returns).prod() ** (252 / len(strategy_returns)) - 1
        volatility = strategy_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # 最大回撤
        cumulative_returns = (1 + strategy_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = cumulative_returns / running_max - 1
        max_drawdown = drawdown.min()

        # 基准比较
        benchmark_total = (1 + benchmark_returns).prod() - 1
        excess_return = total_return - benchmark_total

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'benchmark_return': benchmark_total,
            'excess_return': excess_return
        }