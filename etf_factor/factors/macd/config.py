"""
MACD配置管理模块
处理参数验证、默认配置和因子元信息
"""


class MacdConfig:
    """MACD指标因子配置管理"""

    # 默认参数
    DEFAULT_PARAMS = {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    }

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

    # 支持的周期范围
    MIN_PERIOD = 2
    MAX_PERIOD = 252  # 一年交易日数

    @classmethod
    def validate_params(cls, params=None) -> dict:
        """
        验证和标准化参数

        Args:
            params: 输入参数字典

        Returns:
            验证后的参数字典

        Raises:
            ValueError: 当参数不符合要求时
        """
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if not isinstance(params, dict):
            raise ValueError("params必须是字典类型或None")

        # 获取参数值，使用默认值填充缺失项
        fast_period = params.get("fast_period", cls.DEFAULT_PARAMS["fast_period"])
        slow_period = params.get("slow_period", cls.DEFAULT_PARAMS["slow_period"])
        signal_period = params.get("signal_period", cls.DEFAULT_PARAMS["signal_period"])

        # 验证参数
        validated_params = cls._validate_periods(fast_period, slow_period, signal_period)

        return validated_params

    @classmethod
    def _validate_periods(cls, fast_period, slow_period, signal_period) -> dict:
        """验证MACD周期参数"""
        # 检查数据类型并转换
        periods = [fast_period, slow_period, signal_period]
        period_names = ["fast_period", "slow_period", "signal_period"]

        validated_periods = []
        for period, name in zip(periods, period_names):
            if not isinstance(period, int):
                try:
                    period = int(period)
                except (ValueError, TypeError):
                    raise ValueError(f"{name}必须是整数: {period}")

            if period < cls.MIN_PERIOD:
                raise ValueError(f"{name}不能小于{cls.MIN_PERIOD}: {period}")

            if period > cls.MAX_PERIOD:
                raise ValueError(f"{name}不能大于{cls.MAX_PERIOD}: {period}")

            validated_periods.append(period)

        fast, slow, signal = validated_periods

        # 验证MACD特有的逻辑关系
        if fast >= slow:
            raise ValueError(f"快线周期({fast})必须小于慢线周期({slow})")

        # 信号线周期通常比快线小，但不是强制要求
        if signal > slow:
            import warnings
            warnings.warn(f"信号线周期({signal})大于慢线周期({slow})，这可能不是常见的MACD配置")

        return {
            "fast_period": fast,
            "slow_period": slow,
            "signal_period": signal
        }

    @classmethod
    def get_required_columns(cls) -> list:
        """获取所需数据列"""
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        """获取因子信息"""
        return {
            'name': 'MACD',
            'description': 'MACD指标 - 经典趋势动量指标',
            'category': 'trend_momentum',
            'fast_period': params['fast_period'],
            'slow_period': params['slow_period'],
            'signal_period': params['signal_period'],
            'data_type': 'momentum',
            'calculation_method': 'exponential_moving_average_convergence_divergence',
            'formula': 'DIF=EMA_fast-EMA_slow, DEA=EMA(DIF), HIST=DIF-DEA',
            'output_columns': ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        """获取预期输出列"""
        return ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']