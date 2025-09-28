#!/usr/bin/env python3
"""
交互菜单模块 - 负责用户交互界面
职责：显示菜单、获取用户输入、调用相应操作
"""

import sys


class InteractiveMenu:
    """交互菜单 - 单一职责：用户交互"""
    
    def __init__(self, etf_operations):
        """初始化菜单"""
        self.operations = etf_operations
    
    def show_banner(self):
        """显示程序横幅"""
        print("=" * 60)
        print("🚀 ETF数据管理系统")
        print("=" * 60)
        
        # 显示系统摘要
        summary = self.operations.get_summary()
        print(f"📈 当前管理 {summary['etf_count']} 个ETF")
        print(f"📊 总计 {summary['total_records']:,} 条记录")
        if summary['etf_codes']:
            print(f"💼 ETF代码: {', '.join(summary['etf_codes'])}")
        print("=" * 60)
    
    def show_menu(self):
        """显示主菜单"""
        print("\n📋 请选择操作:")
        print("1️⃣  更新所有ETF到最新 (增量更新)")
        print("2️⃣  添加新的ETF代码")
        print("3️⃣  删除ETF数据")
        print("4️⃣  查看所有ETF状态")
        print("0️⃣  退出程序")
        print("-" * 40)
    
    def get_user_choice(self):
        """获取用户选择"""
        try:
            choice = input("👉 请输入选项 (0-4): ").strip()
            return choice
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 程序被用户中断，再见！")
            sys.exit(0)
    
    def handle_update_all(self):
        """处理更新所有ETF"""
        print("\n" + "="*50)
        print("🔄 更新所有ETF到最新")
        print("="*50)
        
        success, total, message = self.operations.update_all_existing()
        
        print(f"\n📊 更新结果:")
        print(f"✅ 成功: {success}/{total}")
        if success < total:
            print(f"❌ 失败: {total - success}/{total}")
        print(f"💬 {message}")
        
        self._pause()
    
    def handle_add_etf(self):
        """处理添加新ETF"""
        print("\n" + "="*50)
        print("➕ 添加新ETF")
        print("="*50)
        
        etf_code = input("请输入ETF代码 (如: 510580 或 510580.SH): ").strip()
        if not etf_code:
            print("❌ ETF代码不能为空")
            self._pause()
            return
        
        success, message = self.operations.add_new_etf(etf_code)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        self._pause()
    
    def handle_delete_etf(self):
        """处理删除ETF"""
        print("\n" + "="*50)
        print("🗑️ 删除ETF数据")
        print("="*50)
        
        # 显示现有ETF
        self.operations.show_all_etf_status()
        
        etf_code = input("\n请输入要删除的ETF代码: ").strip()
        if not etf_code:
            print("❌ ETF代码不能为空")
            self._pause()
            return
        
        success, message = self.operations.delete_etf(etf_code)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        self._pause()
    
    def handle_show_status(self):
        """处理显示状态"""
        print("\n" + "="*50)
        print("📊 ETF状态查看")
        print("="*50)
        
        self.operations.show_all_etf_status()
        self._pause()
    
    def handle_invalid_choice(self, choice):
        """处理无效选择"""
        print(f"❌ 无效选项: {choice}")
        print("💡 请输入 0-4 之间的数字")
        self._pause()
    
    def _pause(self):
        """暂停等待用户按键"""
        input("\n⏸️  按回车键继续...")
    
    def run(self):
        """运行交互菜单主循环"""
        self.show_banner()
        
        while True:
            self.show_menu()
            choice = self.get_user_choice()
            
            if choice == '1':
                self.handle_update_all()
            elif choice == '2':
                self.handle_add_etf()
            elif choice == '3':
                self.handle_delete_etf()
            elif choice == '4':
                self.handle_show_status()
            elif choice == '0':
                print("\n👋 感谢使用ETF数据管理系统，再见！")
                sys.exit(0)
            else:
                self.handle_invalid_choice(choice)