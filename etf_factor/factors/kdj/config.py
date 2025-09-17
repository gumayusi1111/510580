"""
KDJ配置管理模块
处理参数验证、默认配置和因子元信息
"""


class KdjConfig:
    """KDJ随机指标因子配置管理"""

    # 默认参数 - 基于ETF优化的KDJ参数
    DEFAULT_PARAMS = {"period": 9}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

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
            period = cls.DEFAULT_PARAMS["period"]

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
            'name': 'KDJ',
            'description': 'KDJ随机指标 - 包含K、D、J三条线的随机指标',
            'category': 'volume_price',
            'period': period,
            'data_type': 'stochastic_kdj',
            'calculation_method': 'kdj_stochastic',
            'formula': 'K=2/3*K_prev+1/3*RSV, D=2/3*D_prev+1/3*K, J=3*K-2*D',
            'output_columns': [f'KDJ_K_{period}', f'KDJ_D_{period}', f'KDJ_J_{period}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        period = params['period']
        return [f'KDJ_K_{period}', f'KDJ_D_{period}', f'KDJ_J_{period}']