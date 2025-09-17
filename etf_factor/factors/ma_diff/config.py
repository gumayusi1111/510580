"""
MA_DIFF配置管理模块
处理参数验证、默认配置和因子元信息
"""


class MaDiffConfig:
    """移动均线差值因子配置管理"""

    # 默认参数 - 基于ETF优化的MA_DIFF参数
    DEFAULT_PARAMS = {"pairs": [(5, 10), (5, 20), (10, 20), (10, 60)]}

    # 所需数据列
    REQUIRED_COLUMNS = ['ts_code', 'trade_date', 'hfq_close']

    # 支持的参数范围
    MIN_PERIOD = 2
    MAX_PERIOD = 252  # 一年交易日数

    @classmethod
    def validate_params(cls, params=None) -> dict:
        if params is None:
            return cls.DEFAULT_PARAMS.copy()

        if isinstance(params, dict):
            pairs = params.get("pairs", cls.DEFAULT_PARAMS["pairs"])
        elif isinstance(params, list):
            pairs = params
        else:
            pairs = cls.DEFAULT_PARAMS["pairs"]

        validated_pairs = cls._validate_pairs(pairs)

        return {"pairs": validated_pairs}

    @classmethod
    def _validate_pairs(cls, pairs) -> list:
        if not isinstance(pairs, list) or len(pairs) == 0:
            raise ValueError("pairs必须是非空列表")

        validated = []
        for pair in pairs:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError("每个pair必须是包含2个元素的元组或列表")

            short, long = pair

            # 转换为整数
            if not isinstance(short, int):
                try:
                    short = int(short)
                except (ValueError, TypeError):
                    raise ValueError(f"短周期必须是整数: {short}")

            if not isinstance(long, int):
                try:
                    long = int(long)
                except (ValueError, TypeError):
                    raise ValueError(f"长周期必须是整数: {long}")

            # 验证周期范围
            if short < cls.MIN_PERIOD:
                raise ValueError(f"短周期不能小于{cls.MIN_PERIOD}: {short}")

            if short > cls.MAX_PERIOD:
                raise ValueError(f"短周期不能大于{cls.MAX_PERIOD}: {short}")

            if long < cls.MIN_PERIOD:
                raise ValueError(f"长周期不能小于{cls.MIN_PERIOD}: {long}")

            if long > cls.MAX_PERIOD:
                raise ValueError(f"长周期不能大于{cls.MAX_PERIOD}: {long}")

            # 短周期必须小于长周期
            if short >= long:
                raise ValueError(f"短周期({short})必须小于长周期({long})")

            validated.append((short, long))

        # 去重（保持顺序）
        seen = set()
        unique_pairs = []
        for pair in validated:
            if pair not in seen:
                unique_pairs.append(pair)
                seen.add(pair)

        return unique_pairs

    @classmethod
    def get_required_columns(cls) -> list:
        return cls.REQUIRED_COLUMNS.copy()

    @classmethod
    def get_factor_info(cls, params: dict) -> dict:
        pairs = params['pairs']
        return {
            'name': 'MA_DIFF',
            'description': '移动均线差值 - 不同周期均线间的差值',
            'category': 'moving_average',
            'pairs': pairs,
            'data_type': 'price_diff',
            'calculation_method': 'moving_average_difference',
            'formula': 'MA_DIFF = 短周期MA - 长周期MA',
            'output_columns': [f'MA_DIFF_{p[0]}_{p[1]}' for p in pairs]
        }

    @classmethod
    def get_expected_output_columns(cls, params: dict) -> list:
        pairs = params['pairs']
        return [f'MA_DIFF_{p[0]}_{p[1]}' for p in pairs]