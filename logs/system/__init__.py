"""
ETF日志系统 - 统一入口
提供简洁的导入接口

使用方法:
    from logs.system import get_etf_logger

    logger = get_etf_logger()
    logger.startup(etf_count=3, token_valid=True)
    logger.update_etf('510300', success=True, records=12, duration=2.3)
    logger.factor_calculation('510300', success=True, factors=26, duration=4.1)
    logger.error('API', 'Token过期')
    logger.shutdown()
"""

from .core.logger import get_etf_logger, ETFLogger

__all__ = ['get_etf_logger', 'ETFLogger']

# 版本信息
__version__ = '1.0.0'
__author__ = 'ETF System'