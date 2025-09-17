"""
BB_WIDTH配置管理模块
处理参数验证、默认配置和因子元信息
"""


class BbWidthConfig:
    """布林带宽度因子配置管理"""

    # 默认参数 - 基于ETF优化的BB_WIDTH参数
    DEFAULT_PARAMS = {"period": 20, "std_dev": 2}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

    # 支持的参数范围
    MIN_PERIOD = 3
    MAX_PERIOD = 252  # 一年交易日数
    MIN_STD_DEV = 0.1
    MAX_STD_DEV = 10

    @classmethod
    def validate_params(cls, params=None) -> dict:
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if isinstance(params, dict):
            period = params.get("period", cls.DEFAULT_PARAMS["period"])
            std_dev = params.get("std_dev", cls.DEFAULT_PARAMS["std_dev"])
        else:
            period = cls.DEFAULT_PARAMS["period"]
            std_dev = cls.DEFAULT_PARAMS["std_dev"]

        validated_period = cls._validate_period(period)
        validated_std_dev = cls._validate_std_dev(std_dev)

        return {"period": validated_period, "std_dev": validated_std_dev}

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
    def _validate_std_dev(cls, std_dev) -> float:
        if not isinstance(std_dev, (int, float)):
            try:
                std_dev = float(std_dev)
            except (ValueError, TypeError):
                raise ValueError(f"标准差倍数必须是数字: {std_dev}")

        if std_dev < cls.MIN_STD_DEV:
            raise ValueError(f"标准差倍数不能小于{cls.MIN_STD_DEV}: {std_dev}")

        if std_dev > cls.MAX_STD_DEV:
            raise ValueError(f"标准差倍数不能大于{cls.MAX_STD_DEV}: {std_dev}")

        return float(std_dev)

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        period = params['period']
        std_dev = params['std_dev']
        return {
            'name': 'BB_WIDTH',
            'description': '布林带宽度 - 衡量价格波动率的相对指标',
            'category': 'volatility',
            'period': period,
            'std_dev': std_dev,
            'data_type': 'volatility_ratio',
            'calculation_method': 'bollinger_band_width',
            'formula': 'BB_WIDTH = (UPPER - LOWER) / MID × 100%',
            'output_columns': [f'BB_WIDTH_{period}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        period = params['period']
        return [f'BB_WIDTH_{period}']