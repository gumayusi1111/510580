"""
DAILY_RETURN配置管理模块
处理参数验证、默认配置和因子元信息
"""


class DailyReturnConfig:
    """日收益率因子配置管理"""

    # 默认参数
    DEFAULT_PARAMS = {}

    # 因子元信息
    FACTOR_INFO = {
        'name': 'DAILY_RETURN',
        'description': '日收益率 - 单日价格变化百分比',
        'category': 'return_risk',
        'data_type': 'percentage',
        'calculation_method': 'daily_return',
        'formula': 'DAILY_RETURN = (今收 - 昨收) / 昨收 × 100%',
        'output_columns': ['DAILY_RETURN']
    }

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

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

        if not isinstance(params, dict):
            raise ValueError("params必须是字典类型或None")

        # 日收益率因子无需额外参数，返回空字典
        validated_params = cls.DEFAULT_PARAMS.copy()

        # 如果传入了额外参数，发出警告但不报错
        if params:
            import warnings
            warnings.warn(f"日收益率因子不需要额外参数，忽略: {list(params.keys())}")

        return validated_params

    @classmethod
    def get_required_columns(cls) -> list:
        """获取所需数据列"""
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls) -> dict:
        """获取因子信息"""
        return cls.FACTOR_INFO.copy()

    @classmethod
    def get_expected_output_columns(cls) -> list:
        """获取预期输出列"""
        return cls.FACTOR_INFO['output_columns'].copy()