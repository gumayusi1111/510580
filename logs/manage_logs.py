#!/usr/bin/env python3
"""
日志管理脚本
手动管理ETF系统的日志文件
"""

import sys
import os
import argparse
from datetime import datetime

# 直接从logger模块导入，避免复杂的依赖
logger_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_collection', 'src')
sys.path.insert(0, logger_path)

def main():
    parser = argparse.ArgumentParser(description='ETF系统日志管理工具')
    parser.add_argument('--action', choices=['clean', 'status', 'archive'], 
                       default='status', help='操作类型')
    parser.add_argument('--weeks', type=int, default=2, 
                       help='保留的周数 (默认: 2周)')
    parser.add_argument('--days', type=int, default=30,
                       help='归档天数阈值 (默认: 30天)')
    parser.add_argument('--force', action='store_true',
                       help='强制执行，不询问确认')
    
    args = parser.parse_args()
    
    from logger import get_etf_logger
    logger = get_etf_logger()
    
    print("🗂️ ETF系统日志管理工具")
    print("=" * 50)
    
    if args.action == 'status':
        show_log_status(logger)
    
    elif args.action == 'clean':
        clean_logs(logger, args.weeks, args.force)
    
    elif args.action == 'archive':
        archive_logs(logger, args.days, args.force)

def show_log_status(logger):
    """显示日志状态"""
    print("📊 日志系统状态:")
    
    # 获取摘要
    summary = logger.get_log_summary()
    print("\n📋 总体统计:")
    print(f"   📄 总文件数: {summary['total_files']}")
    print(f"   💾 总大小: {summary['total_size_mb']:.2f} MB")
    
    # 各目录详情
    print("\n📁 目录详情:")
    for dir_info in summary['log_directories']:
        print(f"   📂 {dir_info['name']}:")
        print(f"      文件数: {dir_info['file_count']}")
        print(f"      大小: {dir_info['size_mb']:.2f} MB")
    
    # 检查清理状态
    cleanup_marker = os.path.join(logger.logs_dir, ".last_cleanup")
    if os.path.exists(cleanup_marker):
        try:
            with open(cleanup_marker, 'r') as f:
                last_cleanup = datetime.fromisoformat(f.read().strip())
            days_ago = (datetime.now() - last_cleanup).days
            print(f"\n🕐 上次清理: {last_cleanup.strftime('%Y-%m-%d %H:%M')} ({days_ago}天前)")
        except Exception:
            print("\n🕐 上次清理: 无记录")
    else:
        print("\n🕐 上次清理: 从未清理")
    
    # 显示最近的日志
    print("\n📜 最近的系统日志 (最新5条):")
    recent_logs = logger.get_recent_logs("system", lines=5)
    for log_line in recent_logs:
        print(f"   {log_line.strip()}")

def clean_logs(logger, weeks, force):
    """清理日志"""
    print(f"🧹 日志清理 (保留 {weeks} 周)")
    
    if not force:
        print("\n⚠️  此操作将:")
        print(f"   - 删除超过 {weeks} 周的日志文件")
        print("   - 将删除的文件压缩保存到 archives/ 目录")
        print(f"   - 保留最近 {weeks} 周的日志文件")
        
        confirm = input("\n确认执行清理? (y/N): ").lower().strip()
        if confirm != 'y':
            print("❌ 用户取消操作")
            return
    
    # 执行清理
    print("\n🔄 开始清理...")
    cleaned_count, archive_path = logger.clean_weekly_logs(weeks)
    
    if cleaned_count > 0:
        print("\n✅ 清理完成:")
        print(f"   清理文件数: {cleaned_count}")
        if archive_path:
            print(f"   归档位置: {archive_path}")
    else:
        print("\n✅ 无需清理")

def archive_logs(logger, days, force):
    """归档旧日志"""
    print(f"📦 日志归档 (超过 {days} 天的文件)")
    
    if not force:
        confirm = input(f"\n确认归档超过 {days} 天的日志文件? (y/N): ").lower().strip()
        if confirm != 'y':
            print("❌ 用户取消操作")
            return
    
    # 执行归档
    print("\n🔄 开始归档...")
    archived_count = logger.archive_old_logs(days)
    
    if archived_count > 0:
        print(f"✅ 归档完成: {archived_count} 个文件")
    else:
        print("✅ 无需归档的文件")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()