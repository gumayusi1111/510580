"""
TR配置管理模块
处理参数验证、默认配置和因子元信息
"""


class TrConfig:
    """真实波幅因子配置管理"""

    # 默认参数（TR无需参数）
    DEFAULT_PARAMS = {}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_high', 'hfq_low', 'hfq_close']

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

        return cls.DEFAULT_PARAMS.copy()

    @classmethod
    def get_required_columns(cls) -> list:
        """获取所需数据列"""
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        """获取因子信息"""
        return {
            'name': 'TR',
            'description': '真实波幅 - 衡量价格波动幅度的指标',
            'category': 'volatility',
            'data_type': 'volatility',
            'calculation_method': 'true_range',
            'formula': 'TR = MAX(高-低, ABS(高-昨收), ABS(低-昨收))',
            'output_columns': ['TR']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        """获取预期输出列"""
        return ['TR']