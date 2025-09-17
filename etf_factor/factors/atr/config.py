"""
ATR配置管理模块
处理参数验证、默认配置和因子元信息
"""


class AtrConfig:
    """ATR平均真实波幅因子配置管理"""

    # 默认参数 - 基于ETF优化的ATR参数
    DEFAULT_PARAMS = {"periods": [14]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

    # 支持的周期范围
    MIN_PERIOD = 1
    MAX_PERIOD = 252  # 一年交易日数

    @classmethod
    def validate_params(cls, params=None) -> dict:
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if isinstance(params, dict):
            periods = params.get("periods", cls.DEFAULT_PARAMS["periods"])
        elif isinstance(params, list):
            periods = params
        else:
            raise ValueError("params必须是字典、列表或None")

        validated_periods = cls._validate_periods(periods)
        return {"periods": validated_periods}

    @classmethod
    def _validate_periods(cls, periods) -> list:
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")

        validated_periods = []
        for period in periods:
            if not isinstance(period, int):
                try:
                    period = int(period)
                except (ValueError, TypeError):
                    raise ValueError(f"周期值必须是整数: {period}")

            if period < cls.MIN_PERIOD:
                raise ValueError(f"周期不能小于{cls.MIN_PERIOD}: {period}")

            if period > cls.MAX_PERIOD:
                raise ValueError(f"周期不能大于{cls.MAX_PERIOD}: {period}")

            validated_periods.append(period)

        return sorted(list(set(validated_periods)))

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        return {
            'name': 'ATR',
            'description': '平均真实波幅 - TR的移动平均，衡量波动性',
            'category': 'volatility',
            'periods': params['periods'],
            'data_type': 'volatility',
            'calculation_method': 'average_true_range',
            'formula': 'ATR = EMA(TR, period)',
            'output_columns': [f'ATR_{p}' for p in params['periods']]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        return [f'ATR_{p}' for p in params['periods']]