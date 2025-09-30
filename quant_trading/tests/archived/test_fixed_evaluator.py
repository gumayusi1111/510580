#!/usr/bin/env python3
"""
测试修复后的智能评级系统
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from quant_trading.analyzers.factor_evaluation.evaluator import FactorEvaluator


def test_fixed_evaluator():
    """测试修复后的评估器"""
    print("🔧 === 测试修复后的智能评级系统 ===")

    try:
        # 创建评估器
        evaluator = FactorEvaluator(strategy_type='short_term')
        print("✅ 智能评估器创建成功")

        # 测试单个因子评估
        print("\n🧪 测试单因子评估...")
        result = evaluator.evaluate_single_factor("RSI_14", "510300")

        if 'error' not in result:
            print("✅ 单因子评估成功")

            # 检查适应性IC结果
            ic_analysis = result.get('ic_analysis')
            if hasattr(ic_analysis, 'factor_category'):
                print(f"📊 因子分类: {ic_analysis.factor_category}")
                print(f"🎯 适应性前瞻期: {ic_analysis.adaptive_periods}")
                print(f"📈 主要前瞻期: {ic_analysis.primary_period}")

            # 检查评分
            eval_score = result.get('evaluation_score', {})
            print(f"🏆 评分等级: {eval_score.get('grade', 'N/A')}")
            print(f"💯 总分: {eval_score.get('total_score', 0):.3f}")

            if eval_score.get('total_score', 0) > 0:
                print("🎉 评分系统工作正常！")
                return True
            else:
                print("⚠️ 评分为0，可能还有问题")
                return False
        else:
            print(f"❌ 单因子评估失败: {result.get('details', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_fixed_evaluator()