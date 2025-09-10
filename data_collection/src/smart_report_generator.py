#!/usr/bin/env python3
"""
智能报告生成器 - 分析日志并生成简洁易懂的报告
"""

import os
import re
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Any


class SmartReportGenerator:
    """智能报告生成器"""
    
    def __init__(self, logs_dir: str = "../logs"):
        """初始化报告生成器"""
        self.logs_dir = os.path.abspath(logs_dir)
        self.report_file = os.path.join(self.logs_dir, "report.txt")
        self.today = datetime.now().strftime("%Y-%m-%d")
        
    def cleanup_old_logs(self):
        """清理旧日志，只保留今天的"""
        print("🧹 清理旧日志文件...")
        
        today_str = datetime.now().strftime("%Y%m%d")
        cleaned_count = 0
        
        # 遍历所有日志子目录
        for subdir in ["etf_operations", "factor_calculations", "system"]:
            subdir_path = os.path.join(self.logs_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
                
            # 删除不是今天的日志文件
            for log_file in glob.glob(os.path.join(subdir_path, "*.log")):
                filename = os.path.basename(log_file)
                if today_str not in filename:
                    try:
                        os.remove(log_file)
                        cleaned_count += 1
                    except Exception as e:
                        print(f"⚠️  删除日志失败 {log_file}: {e}")
        
        print(f"✅ 清理了 {cleaned_count} 个旧日志文件")
        
    def analyze_logs(self) -> Dict[str, Any]:
        """分析今天的日志并提取关键信息"""
        analysis = {
            "date": self.today,
            "summary": "系统运行正常",
            "etf_operations": [],
            "factor_calculations": [],
            "errors": [],
            "warnings": [],
            "success_count": 0,
            "error_count": 0,
            "total_records": 0
        }
        
        # 分析ETF操作日志
        self._analyze_etf_operations(analysis)
        
        # 分析因子计算日志  
        self._analyze_factor_calculations(analysis)
        
        # 分析系统日志
        self._analyze_system_logs(analysis)
        
        # 生成总体状态
        self._generate_overall_status(analysis)
        
        return analysis
        
    def _analyze_etf_operations(self, analysis: Dict):
        """分析ETF操作日志"""
        etf_logs_dir = os.path.join(self.logs_dir, "etf_operations")
        if not os.path.exists(etf_logs_dir):
            return
            
        today_str = datetime.now().strftime("%Y%m%d")
        log_files = glob.glob(os.path.join(etf_logs_dir, f"*{today_str}.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取ETF操作信息
                if "增量更新成功" in content:
                    matches = re.findall(r'(\d{6}): 增量更新成功: 成功获取 (\d+) 条记录', content)
                    for etf_code, record_count in matches:
                        analysis["etf_operations"].append(f"✅ {etf_code} 增量更新: +{record_count}条")
                        analysis["success_count"] += 1
                        analysis["total_records"] += int(record_count)
                        
                if "全量更新成功" in content:
                    matches = re.findall(r'(\d{6}): 全量更新成功: 成功获取 (\d+) 条记录', content)
                    for etf_code, record_count in matches:
                        analysis["etf_operations"].append(f"🔄 {etf_code} 全量更新: {record_count}条")
                        analysis["success_count"] += 1
                        analysis["total_records"] += int(record_count)
                        
                # 提取错误信息
                if "ERROR" in content or "失败" in content:
                    error_lines = [line.strip() for line in content.split('\n') 
                                 if 'ERROR' in line or '失败' in line]
                    analysis["errors"].extend(error_lines[:3])  # 只取前3个错误
                    analysis["error_count"] += len(error_lines)
                    
            except Exception as e:
                analysis["warnings"].append(f"读取日志失败: {log_file}")
                
    def _analyze_factor_calculations(self, analysis: Dict):
        """分析因子计算日志"""
        factor_logs_dir = os.path.join(self.logs_dir, "factor_calculations")
        if not os.path.exists(factor_logs_dir):
            return
            
        today_str = datetime.now().strftime("%Y%m%d")
        log_files = glob.glob(os.path.join(factor_logs_dir, f"*{today_str}.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取因子计算成功信息
                if "成功" in content and "ALL_FACTORS" in content:
                    matches = re.findall(r'(\d{6}\.SH)\s+\|\s+ALL_FACTORS\s+\|\s+成功', content)
                    for etf_code in matches:
                        analysis["factor_calculations"].append(f"📊 {etf_code} 因子计算完成")
                        analysis["success_count"] += 1
                        
                # 提取失败信息
                if "失败" in content:
                    matches = re.findall(r'(\d{6}\.SH)\s+.*失败', content)
                    for match in matches:
                        analysis["factor_calculations"].append(f"❌ {match} 因子计算失败")
                        analysis["error_count"] += 1
                        
            except Exception as e:
                analysis["warnings"].append(f"读取因子日志失败: {log_file}")
                
    def _analyze_system_logs(self, analysis: Dict):
        """分析系统日志"""
        system_logs_dir = os.path.join(self.logs_dir, "system")
        if not os.path.exists(system_logs_dir):
            return
            
        today_str = datetime.now().strftime("%Y%m%d")
        log_files = glob.glob(os.path.join(system_logs_dir, f"*{today_str}.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取系统启动信息
                if "SYSTEM_STARTUP" in content:
                    analysis["etf_operations"].append("🚀 系统启动")
                    
            except Exception as e:
                analysis["warnings"].append(f"读取系统日志失败: {log_file}")
                
    def _generate_overall_status(self, analysis: Dict):
        """生成总体状态摘要"""
        if analysis["error_count"] == 0:
            if analysis["success_count"] > 0:
                analysis["summary"] = "✅ 系统运行完美，所有操作成功"
            else:
                analysis["summary"] = "😴 系统运行正常，今日暂无操作"
        elif analysis["error_count"] < analysis["success_count"]:
            analysis["summary"] = f"⚠️  系统基本正常，有{analysis['error_count']}个小问题"
        else:
            analysis["summary"] = f"❌ 系统有问题，{analysis['error_count']}个错误需要关注"
            
    def generate_report(self) -> str:
        """生成简洁易懂的报告"""
        print("📊 生成智能分析报告...")
        
        # 清理旧日志
        self.cleanup_old_logs()
        
        # 分析日志
        analysis = self.analyze_logs()
        
        # 生成报告内容
        report_lines = [
            "=" * 60,
            f"🚀 ETF数据管理系统 - 每日运行报告",
            "=" * 60,
            f"📅 日期: {analysis['date']}",
            f"🔍 状态: {analysis['summary']}",
            f"📊 操作统计: 成功 {analysis['success_count']} 次，错误 {analysis['error_count']} 次",
            ""
        ]
        
        # ETF操作部分
        if analysis["etf_operations"]:
            report_lines.append("💼 ETF数据操作:")
            for op in analysis["etf_operations"]:
                report_lines.append(f"   {op}")
            report_lines.append("")
            
        # 因子计算部分
        if analysis["factor_calculations"]:
            report_lines.append("🧮 因子计算:")
            for calc in analysis["factor_calculations"]:
                report_lines.append(f"   {calc}")
            report_lines.append("")
            
        # 数据统计
        if analysis["total_records"] > 0:
            report_lines.extend([
                "📈 数据统计:",
                f"   本日获取数据记录: {analysis['total_records']:,} 条",
                ""
            ])
            
        # 错误和警告
        if analysis["errors"]:
            report_lines.append("⚠️  错误信息:")
            for error in analysis["errors"][:3]:  # 只显示前3个
                report_lines.append(f"   {error}")
            report_lines.append("")
            
        if analysis["warnings"]:
            report_lines.append("⚠️  警告信息:")
            for warning in analysis["warnings"][:3]:
                report_lines.append(f"   {warning}")
            report_lines.append("")
            
        # 结尾
        report_lines.extend([
            "=" * 60,
            f"📝 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"🗂️  详细日志位置: {self.logs_dir}",
            "=" * 60
        ])
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ 报告已生成: {self.report_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            
        return report_content


def main():
    """主函数 - 用于测试"""
    generator = SmartReportGenerator()
    report = generator.generate_report()
    print("\n" + "="*60)
    print("生成的报告内容:")
    print("="*60)
    print(report)


if __name__ == "__main__":
    main()