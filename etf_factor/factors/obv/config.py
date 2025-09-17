"""
OBV配置管理模块
处理参数验证、默认配置和因子元信息
"""


class ObvConfig:
    """OBV能量潮指标因子配置管理"""

    # 默认参数 - OBV无需参数
    DEFAULT_PARAMS = {}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close', 'vol']

    @classmethod
    def validate_params(cls, params=None) -> dict:
        # OBV因子无需参数，直接返回空字典
        return cls.DEFAULT_PARAMS.copy()

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        return {
            'name': 'OBV',
            'description': '能量潮指标 - 累计成交量指标，反映资金流向',
            'category': 'volume_price',
            'data_type': 'volume',
            'calculation_method': 'on_balance_volume',
            'formula': 'OBV = 累计(价格方向 × 成交量)',
            'output_columns': ['OBV']
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        return ['OBV']