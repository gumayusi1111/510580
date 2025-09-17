"""
HV配置管理模块
处理参数验证、默认配置和因子元信息
"""


class HvConfig:
    """历史波动率因子配置管理"""

    # 默认参数 - 基于ETF优化的HV参数
    DEFAULT_PARAMS = {"periods": [20, 60]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

    # 支持的参数范围
    MIN_PERIOD = 2
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
            periods = cls.DEFAULT_PARAMS["periods"]

        validated_periods = cls._validate_periods(periods)

        return {"periods": validated_periods}

    @classmethod
    def _validate_periods(cls, periods) -> list:
        if not isinstance(periods, list) or len(periods) == 0:
            raise ValueError("periods必须是非空列表")

        validated = []
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

            validated.append(period)

        # 去重并排序
        validated = sorted(list(set(validated)))
        return validated

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        periods = params['periods']
        return {
            'name': 'HV',
            'description': '历史波动率 - 基于价格收益率标准差的年化波动率',
            'category': 'volatility',
            'periods': periods,
            'data_type': 'percentage',
            'calculation_method': 'historical_volatility',
            'formula': 'HV = STD(日收益率) × √252 × 100%',
            'output_columns': [f'HV_{p}' for p in periods]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        periods = params['periods']
        return [f'HV_{p}' for p in periods]