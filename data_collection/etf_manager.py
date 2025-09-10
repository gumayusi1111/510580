#!/usr/bin/env python3
"""
ETF管理系统主程序 - 编排器模式
职责：组装各个模块，启动交互式界面
"""

import os
import sys
import traceback
from src import (
    TushareClient, DataProcessor, ETFDiscovery, 
    ETFUpdater, ETFOperations, InteractiveMenu, TokenManager
)


class ETFManager:
    """ETF管理器 - 单一职责：组装和编排各个模块"""
    
    def __init__(self):
        """初始化管理器 - 组装所有组件"""
        try:
            # 1. Token管理 - 优先验证
            print("🚀 启动ETF数据管理系统...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "config", "settings.py")
            token_manager = TokenManager(config_path)
            valid_token = token_manager.ensure_valid_token()
            
            # 2. 日志系统初始化和自动清理
            from src.logger import get_etf_logger
            logger = get_etf_logger()
            logger.log_system_event("SYSTEM_STARTUP", "ETF数据管理系统启动", "info")
            logger.auto_cleanup_on_startup()  # 自动检查并清理日志
            
            # 3. 核心组件
            self.api_client = TushareClient(valid_token)
            self.data_processor = DataProcessor()
            
            # 4. 功能组件
            self.discovery = ETFDiscovery(self.data_processor.data_dir)
            self.updater = ETFUpdater(self.api_client, self.data_processor)
            self.operations = ETFOperations(self.discovery, self.updater, self.data_processor)
            
            # 5. 界面组件
            self.menu = InteractiveMenu(self.operations)
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            print("💡 请检查配置和网络连接")
            traceback.print_exc()
            sys.exit(1)
    
    def run(self):
        """启动ETF管理系统"""
        try:
            self.menu.run()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断程序")
            self._generate_smart_report()
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 系统运行出错: {e}")
            traceback.print_exc()
            self._generate_smart_report()
            sys.exit(1)
        finally:
            # 正常退出时也生成报告
            self._generate_smart_report()
    
    def _generate_smart_report(self):
        """生成智能报告"""
        try:
            from src.logger import get_etf_logger
            logger = get_etf_logger()
            print("\n📊 正在生成今日运行报告...")
            logger.generate_smart_report()
        except Exception as e:
            print(f"⚠️  生成报告时出错: {e}")


def main():
    """主入口函数"""
    manager = ETFManager()
    manager.run()


if __name__ == "__main__":
    main()