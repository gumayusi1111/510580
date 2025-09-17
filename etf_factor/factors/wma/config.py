"""
WMA配置管理模块
处理参数验证、默认配置和因子元信息
"""


class WmaConfig:
    """加权移动均线因子配置管理"""

    # 默认参数 - 基于ETF优化的WMA参数
    DEFAULT_PARAMS = {"periods": [5, 10, 20, 60]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

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
            'name': 'WMA',
            'description': '加权移动均线 - 线性递减权重，最近价格权重最高',
            'category': 'moving_average',
            'periods': params['periods'],
            'data_type': 'price',
            'calculation_method': 'linear_weighted_average',
            'formula': 'WMA = Σ(价格 × [1,2,3...N]) / Σ[1,2,3...N]',
            'output_columns': [f'WMA_{p}' for p in params['periods']]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        return [f'WMA_{p}' for p in params['periods']]