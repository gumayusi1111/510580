"""
VMA配置管理模块
处理参数验证、默认配置和因子元信息
"""


class VmaConfig:
    """成交量移动均线因子配置管理"""

    # 默认参数
    DEFAULT_PARAMS = {"periods": [5, 10, 20]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'vol']

    # 支持的周期范围
    MIN_PERIOD = 1
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
            'name': 'VMA',
            'description': '成交量移动均线 - 分析量能趋势',
            'category': 'volume',
            'periods': params['periods'],
            'data_type': 'volume',
            'calculation_method': 'volume_moving_average',
            'formula': 'VMA = SMA(成交量, period)',
            'output_columns': [f'VMA_{p}' for p in params['periods']]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        """获取预期输出列"""
        return [f'VMA_{p}' for p in params['periods']]