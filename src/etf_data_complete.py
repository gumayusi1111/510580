#!/usr/bin/env python3
"""
ETF完整数据获取脚本 - 510580.SH 中证500ETF易方达
获取基金日线数据、复权因子，并计算前复权和后复权价格
"""

import os
import sys
import traceback
from datetime import datetime, timedelta
import pandas as pd
import tushare as ts  # cspell:ignore tushare


def setup_tushare_token():  # cspell:ignore tushare
    """设置tushare token"""  # cspell:ignore tushare
    # TODO: 请在这里设置你的tushare token  # cspell:ignore tushare
    token = "d27a688495ac9b1eef8534011f5d39282fb516d71095c2e976d6b1f7"
    if not token or token == "your_token_here":
        print("错误: 请先在脚本中设置有效的tushare token")  # cspell:ignore tushare
        sys.exit(1)

    ts.set_token(token)
    return ts.pro_api()


def get_data_file_path(filename):
    """获取数据文件的绝对路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data")

    # 确保data目录存在
    os.makedirs(data_dir, exist_ok=True)

    return os.path.join(data_dir, filename)


def fetch_etf_data(pro, etf_code, start_date, end_date):
    """获取ETF基金数据和复权因子"""
    print(f"获取 {etf_code} 数据...")
    print(f"时间范围: {start_date} 到 {end_date}")

    try:
        # 获取基金复权因子
        print("\n1. 获取基金复权因子...")
        adj_data = pro.fund_adj(
            ts_code=etf_code, start_date=start_date, end_date=end_date
        )
        print(f"获取到 {len(adj_data)} 条复权因子数据")

        if len(adj_data) == 0:
            print("警告: 未获取到复权因子数据")
            return None, None

        # 获取基金日线数据
        print("\n2. 获取基金日线数据...")
        daily_data = pro.fund_daily(
            ts_code=etf_code, start_date=start_date, end_date=end_date
        )
        print(f"获取到 {len(daily_data)} 条日线数据")

        if len(daily_data) == 0:
            print("警告: 未获取到日线数据")
            return adj_data, None

        return adj_data, daily_data

    except Exception as e:
        print(f"获取数据时出错: {e}")
        traceback.print_exc()
        return None, None


def calculate_adjusted_prices(merged_data):
    """计算前复权和后复权价格"""
    print("\n3. 计算复权价格...")

    # 获取最新复权因子（用于前复权计算）
    latest_adj_factor = merged_data.iloc[0]["adj_factor"]
    print(f"最新复权因子: {latest_adj_factor}")

    # 后复权计算: 价格 × 当日复权因子
    merged_data["hfq_open"] = merged_data["open"] * merged_data["adj_factor"]
    merged_data["hfq_high"] = merged_data["high"] * merged_data["adj_factor"]
    merged_data["hfq_low"] = merged_data["low"] * merged_data["adj_factor"]
    merged_data["hfq_close"] = merged_data["close"] * merged_data["adj_factor"]

    # 前复权计算: 价格 ÷ 最新复权因子
    merged_data["qfq_open"] = merged_data["open"] / latest_adj_factor
    merged_data["qfq_high"] = merged_data["high"] / latest_adj_factor
    merged_data["qfq_low"] = merged_data["low"] / latest_adj_factor
    merged_data["qfq_close"] = merged_data["close"] / latest_adj_factor

    print("复权价格计算完成")
    print("- hfq_*: 后复权价格 (价格 × 当日复权因子)")
    print("- qfq_*: 前复权价格 (价格 ÷ 最新复权因子)")

    return merged_data


def organize_final_data(merged_data):
    """整理最终数据列顺序"""
    column_order = [
        # 基础信息
        "ts_code",
        "trade_date",
        # 原始价格数据
        "pre_close",
        "open",
        "high",
        "low",
        "close",
        "change",
        "pct_chg",
        "vol",
        "amount",
        # 复权因子
        "adj_factor",
        # 后复权价格
        "hfq_open",
        "hfq_high",
        "hfq_low",
        "hfq_close",
        # 前复权价格
        "qfq_open",
        "qfq_high",
        "qfq_low",
        "qfq_close",
    ]

    return merged_data[column_order]


def save_separate_files(merged_data, etf_code):
    """保存4个独立的数据文件"""
    code_name = etf_code.replace(".", "_")

    print("\n=== 生成4个专门数据文件 ===")

    # 1. 基础数据文件（包含复权因子，用于计算）
    basic_cols = [
        "ts_code",
        "trade_date",
        "pre_close",
        "open",
        "high",
        "low",
        "close",
        "change",
        "pct_chg",
        "vol",
        "amount",
        "adj_factor",
    ]
    basic_data = merged_data[basic_cols]
    basic_file = get_data_file_path(f"{code_name}_basic_data.csv")
    basic_data.to_csv(basic_file, index=False)
    print(f"✅ 基础数据: {basic_file}")

    # 2. 除权数据文件（原始交易数据，无复权调整）
    raw_cols = [
        "ts_code",
        "trade_date",
        "pre_close",
        "open",
        "high",
        "low",
        "close",
        "change",
        "pct_chg",
        "vol",
        "amount",
    ]
    raw_data = merged_data[raw_cols]
    raw_file = get_data_file_path(f"{code_name}_raw_data.csv")
    raw_data.to_csv(raw_file, index=False)
    print(f"✅ 除权数据: {raw_file}")

    # 3. 后复权数据文件（用于量化回测）
    hfq_cols = [
        "ts_code",
        "trade_date",
        "hfq_open",
        "hfq_high",
        "hfq_low",
        "hfq_close",
        "vol",
        "amount",
    ]
    hfq_data = merged_data[hfq_cols]
    hfq_file = get_data_file_path(f"{code_name}_hfq_data.csv")
    hfq_data.to_csv(hfq_file, index=False)
    print(f"✅ 后复权数据: {hfq_file}")

    # 4. 前复权数据文件（用于当前价位分析）
    qfq_cols = [
        "ts_code",
        "trade_date",
        "qfq_open",
        "qfq_high",
        "qfq_low",
        "qfq_close",
        "vol",
        "amount",
    ]
    qfq_data = merged_data[qfq_cols]
    qfq_file = get_data_file_path(f"{code_name}_qfq_data.csv")
    qfq_data.to_csv(qfq_file, index=False)
    print(f"✅ 前复权数据: {qfq_file}")

    return basic_data, raw_data, hfq_data, qfq_data


def show_data_summary(merged_data):
    """显示数据汇总信息"""
    print("\n=== 数据概览 ===")
    print(f"记录数: {len(merged_data)}")
    print(
        f"时间范围: {merged_data['trade_date'].min()} 到 {merged_data['trade_date'].max()}"
    )

    # 显示复权因子统计
    unique_factors = merged_data["adj_factor"].unique()
    print(f"复权因子范围: {unique_factors.min():.3f} - {unique_factors.max():.3f}")
    print(f"复权因子唯一值数量: {len(unique_factors)}")

    # 显示样例数据对比
    print("\n=== 价格对比样例 (最近3天) ===")
    sample_data = merged_data.head(3)
    for _, row in sample_data.iterrows():
        print(f"\n日期: {row['trade_date']}")
        print(f"  除权收盘: {row['close']:.3f}")
        print(f"  后复权收盘: {row['hfq_close']:.3f} (×{row['adj_factor']:.2f})")
        print(f"  前复权收盘: {row['qfq_close']:.3f} (÷{row['adj_factor']:.2f})")

    print("\n=== 文件用途说明 ===")
    print("📊 basic_data.csv   - 基础数据 + 复权因子（完整信息）")
    print("📈 raw_data.csv     - 除权数据（原始交易价格）")
    print("🎯 hfq_data.csv     - 后复权数据（量化回测推荐）")
    print("💡 qfq_data.csv     - 前复权数据（当前价位分析）")


def main():
    """主函数"""
    print("=" * 50)
    print("ETF完整数据获取脚本")
    print("=" * 50)

    # 配置参数
    etf_code = "510580.SH"  # 中证500ETF易方达
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=7 * 365)).strftime("%Y%m%d")

    try:
        # 1. 设置tushare
        pro = setup_tushare_token()

        # 2. 获取数据
        adj_data, daily_data = fetch_etf_data(pro, etf_code, start_date, end_date)

        if adj_data is None or daily_data is None:
            print("错误: 无法获取必要数据")
            sys.exit(1)

        # 3. 合并数据
        print("\n合并数据...")
        merged_data = pd.merge(
            daily_data, adj_data, on=["ts_code", "trade_date"], how="inner"
        )
        print(f"合并后数据行数: {len(merged_data)}")

        # 4. 计算复权价格
        merged_data = calculate_adjusted_prices(merged_data)

        # 5. 整理数据格式
        final_data = organize_final_data(merged_data)

        # 6. 保存4个独立数据文件
        save_separate_files(final_data, etf_code)

        # 7. 显示数据汇总
        show_data_summary(final_data)

        print("\n✅ 数据获取完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
