"""
CCI配置管理模块
处理参数验证、默认配置和因子元信息
"""


class CciConfig:
    """CCI顺势指标因子配置管理"""

    # 默认参数 - 基于ETF优化的CCI参数
    DEFAULT_PARAMS = {"period": 14}

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
        return {
            'name': 'CCI',
            'description': 'CCI顺势指标 - 衡量价格偏离平均价格的程度',
            'category': 'volume_price',
            'period': params['period'],
            'data_type': 'momentum_oscillator',
            'calculation_method': 'commodity_channel_index',
            'formula': 'CCI = (TP - MA(TP)) / (0.015 × MD)',
            'output_columns': [f'CCI_{params["period"]}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        return [f'CCI_{params["period"]}']