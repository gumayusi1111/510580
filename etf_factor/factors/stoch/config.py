"""
STOCH配置管理模块
处理参数验证、默认配置和因子元信息
"""


class StochConfig:
    """随机震荡器因子配置管理"""

    # 默认参数 - 基于ETF优化的随机震荡器参数
    DEFAULT_PARAMS = {"k_period": 9, "d_period": 3}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

    # 支持的参数范围
    MIN_K_PERIOD = 3
    MAX_K_PERIOD = 252  # 一年交易日数
    MIN_D_PERIOD = 1
    MAX_D_PERIOD = 50

    @classmethod
    def validate_params(cls, params=None) -> dict:
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if isinstance(params, dict):
            k_period = params.get("k_period", cls.DEFAULT_PARAMS["k_period"])
            d_period = params.get("d_period", cls.DEFAULT_PARAMS["d_period"])
        else:
            raise ValueError("params必须是字典或None")

        validated_k_period = cls._validate_k_period(k_period)
        validated_d_period = cls._validate_d_period(d_period)

        return {"k_period": validated_k_period, "d_period": validated_d_period}

    @classmethod
    def _validate_k_period(cls, k_period) -> int:
        if not isinstance(k_period, int):
            try:
                k_period = int(k_period)
            except (ValueError, TypeError):
                raise ValueError(f"k_period必须是整数: {k_period}")

        if k_period < cls.MIN_K_PERIOD:
            raise ValueError(f"k_period不能小于{cls.MIN_K_PERIOD}: {k_period}")

        if k_period > cls.MAX_K_PERIOD:
            raise ValueError(f"k_period不能大于{cls.MAX_K_PERIOD}: {k_period}")

        return k_period

    @classmethod
    def _validate_d_period(cls, d_period) -> int:
        if not isinstance(d_period, int):
            try:
                d_period = int(d_period)
            except (ValueError, TypeError):
                raise ValueError(f"d_period必须是整数: {d_period}")

        if d_period < cls.MIN_D_PERIOD:
            raise ValueError(f"d_period不能小于{cls.MIN_D_PERIOD}: {d_period}")

        if d_period > cls.MAX_D_PERIOD:
            raise ValueError(f"d_period不能大于{cls.MAX_D_PERIOD}: {d_period}")

        return d_period

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        return {
            'name': 'STOCH',
            'description': '随机震荡器 - 反映价格在一定周期内的相对位置',
            'category': 'volatility',
            'k_period': params['k_period'],
            'd_period': params['d_period'],
            'data_type': 'momentum_oscillator',
            'calculation_method': 'stochastic_oscillator',
            'formula': '%K = (C-LLV)/(HHV-LLV)×100, %D = SMA(%K)',
            'output_columns': [f'STOCH_K_{params["k_period"]}', f'STOCH_D_{params["d_period"]}']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        return [f'STOCH_K_{params["k_period"]}', f'STOCH_D_{params["d_period"]}']