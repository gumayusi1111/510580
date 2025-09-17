"""
DC配置管理模块
处理参数验证、默认配置和因子元信息
"""


class DcConfig:
    """唐奇安通道因子配置管理"""

    # 默认参数 - 基于ETF优化的DC参数
    DEFAULT_PARAMS = {"period": 20}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low']

    # 支持的参数范围
    MIN_PERIOD = 3
    MAX_PERIOD = 252  # 一年交易日数

    @classmethod
    def validate_params(cls, params=None) -> dict:
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if isinstance(params, dict):
            period = params.get("period", cls.DEFAULT_PARAMS["period"])
        else:
            raise ValueError("params必须是字典或None")

        validated_period = cls._validate_period(period)

        return {"period": validated_period}

    @classmethod
    def _validate_period(cls, period) -> int:
        if not isinstance(period, int):
            try:
                period = int(period)
            except (ValueError, TypeError):
                raise ValueError(f"周期值必须是整数: {period}")

        if period < cls.MIN_PERIOD:
            raise ValueError(f"周期不能小于{cls.MIN_PERIOD}: {period}")

        if period > cls.MAX_PERIOD:
            raise ValueError(f"周期不能大于{cls.MAX_PERIOD}: {period}")

        return period

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        period = params['period']
        return {
            'name': 'DC',
            'description': '唐奇安通道 - 基于N日最高/最低价的突破系统',
            'category': 'volatility',
            'period': period,
            'data_type': 'channel_breakout',
            'calculation_method': 'rolling_max_min',
            'formula': 'DC_UPPER = MAX(HIGH, N), DC_LOWER = MIN(LOW, N)',
            'output_columns': [f'DC_UPPER_{period}', f'DC_LOWER_{period}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        period = params['period']
        return [f'DC_UPPER_{period}', f'DC_LOWER_{period}']