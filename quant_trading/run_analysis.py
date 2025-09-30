#!/usr/bin/env python3
"""
因子分析主程序
运行完整的因子有效性分析流程
"""

import sys
import logging
from pathlib import Path
from core.data_management import DataManager
from analyzers.factor_evaluation import FactorEvaluator
from utils.reporting import ReportGenerator
from config.window_config import list_available_strategies

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def setup_logging():
    """配置日志"""
    # 确保logs目录存在
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 日志文件路径
    log_file = log_dir / "factor_analysis.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main():
    """主程序"""
    print("🚀 开始ETF因子分析...")

    # 解析命令行参数
    # 用法: python run_analysis.py [strategy_type] [etf_code] [--deduplicate]
    # 示例: python run_analysis.py short_term 510300
    # 示例(带去重): python run_analysis.py short_term 510300 --deduplicate
    import argparse
    parser = argparse.ArgumentParser(description='ETF因子分析')
    parser.add_argument('strategy_type', type=str, nargs='?', default='short_term',
                       help='策略类型 (short_term/ultra_short/medium_term)')
    parser.add_argument('etf_code', type=str, nargs='?', default='510580',
                       help='ETF代码 (例如: 510300)')
    parser.add_argument('--deduplicate', action='store_true',
                       help='启用因子去重分析 (推荐实盘使用)')
    args = parser.parse_args()

    strategy_type = args.strategy_type
    etf_code = args.etf_code
    enable_dedup = args.deduplicate

    # 显示可用策略
    strategies = list_available_strategies()
    print("\n📋 可用策略配置:")
    for strategy, description in strategies.items():
        print(f"   {strategy}: {description}")

    if strategy_type not in strategies:
        print(f"❌ 无效的策略类型: {strategy_type}")
        print(f"可用策略: {list(strategies.keys())}")
        return 1

    print(f"\n🎯 使用策略: {strategy_type}")
    print(f"   描述: {strategies[strategy_type]}")
    print(f"\n📊 分析目标: ETF {etf_code}")
    if enable_dedup:
        print(f"🔄 因子去重: 已启用 (将生成去重报告)")

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # 初始化组件
        print("📊 初始化分析组件...")
        data_manager = DataManager()
        evaluator = FactorEvaluator(data_manager, strategy_type=strategy_type)
        report_generator = ReportGenerator()

        # 数据概览
        print("📋 获取数据概览...")
        data_info = data_manager.get_data_info(etf_code)
        print(f"   - ETF代码: {data_info['etf_code']}")
        print(f"   - 数据形状: {data_info['data_shape']}")
        print(f"   - 因子数量: {data_info['factor_count']}")
        print(
            f"   - 时间范围: {data_info['date_range'][0]} 至 {data_info['date_range'][1]}"
        )
        print(f"   - 缺失数据比例: {data_info['missing_data_ratio']:.2%}")

        # 执行因子评估
        print("🔍 执行因子有效性评估...")
        print(f"   使用策略: {strategy_type} ({strategies[strategy_type]})")
        print(f"   IC分析窗口: {evaluator.window_config.ic_windows}日")
        print(f"   主窗口: {evaluator.window_config.primary_window}日")
        print("   开始评估因子，请耐心等待...")
        evaluation_results = evaluator.evaluate_all_factors(etf_code)

        if not evaluation_results:
            print("❌ 因子评估失败，请检查数据")
            return

        # 显示关键结果
        print("\n📈 分析结果概览:")
        summary = evaluation_results.get("evaluation_summary", {})
        print(f"   - 评估因子数量: {summary.get('evaluated_factors', 0)}")

        if (
            "factor_ranking" in evaluation_results
            and not evaluation_results["factor_ranking"].empty
        ):
            ranking = evaluation_results["factor_ranking"]
            print(f"   - A级因子: {(ranking['grade'] == 'A').sum()}个")
            print(f"   - B级因子: {(ranking['grade'] == 'B').sum()}个")
            print(f"   - C级因子: {(ranking['grade'] == 'C').sum()}个")

            # 显示前5名因子
            print("\n🏆 Top 5 因子:")
            top_5 = ranking.head(5)
            for _, row in top_5.iterrows():
                print(
                    f"   {row['rank']}. {row['factor']} (评级: {row['grade']}, 总分: {row['total_score']:.3f})"
                )

        # 生成报告
        print("\n📄 生成分析报告...")

        # 生成markdown报告
        report_path = report_generator.generate_factor_evaluation_report(
            evaluation_results, etf_code
        )

        # 生成CSV汇总
        csv_paths = report_generator.generate_csv_summary(evaluation_results, etf_code)

        print("✅ 分析完成！")
        if report_path:
            print(f"   - 详细报告: {report_path}")
        else:
            print("   - 详细报告: 生成失败")

        if csv_paths:
            print(f"   - CSV汇总: {csv_paths}")
        else:
            print("   - CSV汇总: 生成失败")

        # 执行因子去重分析
        if enable_dedup:
            print("\n🔄 执行因子去重分析...")
            try:
                from analyzers.redundancy_analyzer import analyze_redundancy
                analyze_redundancy(etf_code, threshold=0.85)
            except Exception as dedup_error:
                logger.warning(f"因子去重分析失败: {dedup_error}")
                print(f"⚠️ 因子去重分析失败: {dedup_error}")

        # 显示使用建议
        if "selection_recommendations" in evaluation_results:
            recommendations = evaluation_results["selection_recommendations"]
            recommended_factors = recommendations.get("recommended_factors", [])
            redundant_factors = recommendations.get("redundant_factors", [])

            print("\n💡 使用建议:")
            print(f"   - 推荐使用因子: {len(recommended_factors)}个")
            print(f"   - 冗余因子: {len(redundant_factors)}个")

            if recommended_factors:
                print(f"   - 推荐因子列表: {', '.join(recommended_factors[:10])}")
                if len(recommended_factors) > 10:
                    print(f"     (共{len(recommended_factors)}个，仅显示前10个)")

    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}")
        print(f"❌ 分析失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
