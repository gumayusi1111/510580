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
            # 1. 设置基础路径
            print("🚀 启动ETF数据管理系统...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.dirname(script_dir)  # 项目根目录

            # 2. Token管理 - 优先验证
            config_path = os.path.join(script_dir, "config", "settings.py")
            token_manager = TokenManager(config_path)
            valid_token = token_manager.ensure_valid_token()

            # 3. 模块化日志系统初始化
            import sys
            sys.path.insert(0, os.path.join(self.base_dir, "logs"))
            from system import get_etf_logger
            self.logger = get_etf_logger()
            
            # 4. 核心组件
            self.api_client = TushareClient(valid_token)
            self.data_processor = DataProcessor()
            
            # 5. 功能组件
            self.discovery = ETFDiscovery(self.data_processor.data_dir)
            self.updater = ETFUpdater(self.api_client, self.data_processor)
            self.updater.logger = self.logger  # 传递智能日志器
            self.operations = ETFOperations(self.discovery, self.updater, self.data_processor)
            self.operations.logger = self.logger  # 传递日志器
            
            # 6. 界面组件
            self.menu = InteractiveMenu(self.operations)

            # 7. 记录启动成功（现在有ETF数量了）
            etf_count = len(self.discovery.get_existing_etfs())
            self.logger.startup(token_valid=True, etf_count=etf_count)
            
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
        """生成智能运行总结"""
        try:
            if hasattr(self, 'logger'):
                self.logger.shutdown()
                paths = self.logger.get_file_paths()
                print(f"\n📊 运行完成")
                print(f"📄 详细日志: {paths['current']}")
                print(f"📋 运行汇总: {paths['summary']}")
                try:
                    if os.path.getsize(paths['errors']) > 0:
                        print(f"⚠️  错误日志: {paths['errors']}")
                except:
                    pass
            else:
                print("\n📊 运行完成")
        except Exception as e:
            print(f"⚠️  生成日志总结时出错: {e}")


def main():
    """主入口函数"""
    manager = ETFManager()
    manager.run()


if __name__ == "__main__":
    main()