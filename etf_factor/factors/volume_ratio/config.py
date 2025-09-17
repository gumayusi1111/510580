"""
VOLUME_RATIO配置管理模块
处理参数验证、默认配置和因子元信息
"""


class VolumeRatioConfig:
    """量比因子配置管理"""

    # 默认参数 - 基于ETF优化的VOLUME_RATIO参数
    DEFAULT_PARAMS = {"period": 5}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'vol']

    # 支持的参数范围
    MIN_PERIOD = 2
    MAX_PERIOD = 60  # 通常量比不需要太长周期

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
            'name': 'VOLUME_RATIO',
            'description': '量比 - 当日成交量与前N日平均成交量的比值',
            'category': 'volume_price',
            'period': period,
            'data_type': 'volume_activity',
            'calculation_method': 'volume_ratio',
            'formula': 'VOLUME_RATIO = 当日成交量 / 前N日平均成交量',
            'output_columns': [f'VOLUME_RATIO_{period}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        period = params['period']
        return [f'VOLUME_RATIO_{period}']