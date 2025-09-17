"""
ATR_PCT配置管理模块
处理参数验证、默认配置和因子元信息
"""


class AtrPctConfig:
    """ATR百分比因子配置管理"""

    # 默认参数
    DEFAULT_PARAMS = {"periods": [14]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

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

        if isinstance(params, dict):
            periods = params.get("periods", cls.DEFAULT_PARAMS["periods"])
        elif isinstance(params, list):
            periods = params
        else:
            raise ValueError("params必须是字典、列表或None")

        # 验证周期列表
        validated_periods = cls._validate_periods(periods)

        return {"periods": validated_periods}

    @classmethod
    def _validate_periods(cls, periods) -> list:
        """验证周期参数"""
        if not isinstance(periods, list):
            raise ValueError("periods必须是列表类型")

        if len(periods) == 0:
            raise ValueError("periods不能为空列表")

        # 检查每个周期
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

        # 去重并排序
        validated_periods = sorted(list(set(validated_periods)))

        return validated_periods

    @classmethod
    def get_required_columns(cls) -> list:
        """获取所需数据列"""
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        """获取因子信息"""
        return {
            'name': 'ATR_PCT',
            'description': 'ATR百分比 - ATR相对于价格的百分比',
            'category': 'volatility',
            'periods': params['periods'],
            'data_type': 'percentage',
            'calculation_method': 'atr_percentage',
            'formula': 'ATR_PCT = ATR / 收盘价 × 100%',
            'output_columns': [f'ATR_PCT_{p}' for p in params['periods']]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        """获取预期输出列"""
        return [f'ATR_PCT_{p}' for p in params['periods']]