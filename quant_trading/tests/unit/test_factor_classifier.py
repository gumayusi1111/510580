#!/usr/bin/env python3
"""
测试因子分类器在真实因子上的表现
"""

import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from quant_trading.core.factor_classifier import create_factor_classifier

def test_real_factors():
    """测试真实因子的分类效果"""

    # 从实际CSV报告中提取的因子列表
    real_factors = [
        'SHARE_CHANGE_PCT', 'SHARE_CHANGE', 'VOLUME_RATIO_5', 'WR_14',
        'NAV_MA_20', 'TR', 'DAILY_RETURN', 'HV_60', 'ANNUAL_VOL_60',
        'SHARE_MA_5', 'WMA_5', 'EMA_5', 'SMA_5', 'SMA_10', 'SMA_20',
        'RSI_6', 'RSI_14', 'MACD', 'ATR', 'BOLL_UPPER', 'KDJ_K', 'OBV',
        'PE_PERCENTILE', 'PB_PERCENTILE', 'SHIBOR_1M', 'ROC_5', 'MOM_10'
    ]

    classifier = create_factor_classifier()
    print('🔍 === 真实因子分类测试 ===')
    results = classifier.batch_classify_factors(real_factors)

    print('\n📊 === 分类结果详情 ===')
    category_groups = {}

    for factor, category in results.items():
        periods, primary = classifier.get_adaptive_periods(factor)
        category_name = category.name

        if category_name not in category_groups:
            category_groups[category_name] = []
        category_groups[category_name].append({
            'factor': factor,
            'primary': primary,
            'periods': periods
        })

        print(f'{factor:18s} -> {category_name:15s} 主期:{primary:2d}日 前瞻期:{periods}')

    print('\n🎯 === 按类别汇总 ===')
    for cat_name, factors in category_groups.items():
        print(f'\n{cat_name.upper()}:')
        for item in factors:
            print(f'  • {item["factor"]:15s} (主期: {item["primary"]:2d}日)')

    print('\n✅ === 关键改进验证 ===')
    print('原系统问题: 所有因子统一使用 [1,3,5,10] 前瞻期')
    print('新系统优势:')

    # 展示关键改进
    short_tech = [f for f, c in results.items() if c.name == 'technical_short']
    fundamental = [f for f, c in results.items() if c.name == 'fundamental']
    macro = [f for f, c in results.items() if c.name == 'macro_flow']

    if short_tech:
        periods, primary = classifier.get_adaptive_periods(short_tech[0])
        print(f'  短期技术因子 ({len(short_tech)}个): 使用{periods}前瞻期，主期{primary}日')

    if fundamental:
        periods, primary = classifier.get_adaptive_periods(fundamental[0])
        print(f'  基本面因子 ({len(fundamental)}个): 使用{periods}前瞻期，主期{primary}日')

    if macro:
        periods, primary = classifier.get_adaptive_periods(macro[0])
        print(f'  宏观因子 ({len(macro)}个): 使用{periods}前瞻期，主期{primary}日')

if __name__ == '__main__':
    test_real_factors()