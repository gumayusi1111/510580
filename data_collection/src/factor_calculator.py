#!/usr/bin/env python3
"""
因子计算集成模块
职责：在ETF数据更新后自动计算技术因子
"""

import os
import sys
import subprocess
import pandas as pd
from typing import List, Optional


class FactorCalculator:
    """因子计算器 - 集成etf_factor系统"""
    
    def __init__(self, etf_factor_dir=None):
        """初始化因子计算器"""
        self.data_collection_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if etf_factor_dir is None:
            # 默认使用项目根目录下的etf_factor
            project_root = os.path.dirname(self.data_collection_dir)
            self.etf_factor_dir = os.path.join(project_root, "etf_factor")
        else:
            self.etf_factor_dir = etf_factor_dir
        
    def should_calculate_factors(self, etf_code: str) -> bool:
        """判断是否需要计算因子"""
        # 检查是否存在新的数据更新
        data_dir = os.path.join(self.data_collection_dir, "data", etf_code.split('.')[0])
        hfq_file = os.path.join(data_dir, "hfq_data.csv")
        
        if not os.path.exists(hfq_file):
            print(f"⚠️  未找到数据文件: {hfq_file}")
            return False
            
        return True
    
    def get_latest_data_date(self, etf_code: str) -> Optional[str]:
        """获取最新数据日期"""
        try:
            data_dir = os.path.join(self.data_collection_dir, "data", etf_code.split('.')[0])
            hfq_file = os.path.join(data_dir, "hfq_data.csv")
            
            if os.path.exists(hfq_file):
                df = pd.read_csv(hfq_file)
                if len(df) > 0:
                    df['trade_date'] = df['trade_date'].astype(str)
                    return df['trade_date'].max()
        except Exception as e:
            print(f"❌ 获取最新数据日期失败: {e}")
        return None
        
    def get_factor_latest_date(self, etf_code: str) -> Optional[str]:
        """获取因子数据的最新日期"""
        try:
            factor_data_dir = os.path.join(self.etf_factor_dir, "factor_data/single_factors")
            if not os.path.exists(factor_data_dir):
                return None
                
            # 找任意一个因子文件检查最新日期
            etf_code_suffix = etf_code.replace('.', '_')
            for file in os.listdir(factor_data_dir):
                if file.endswith(f"_{etf_code_suffix}.csv"):
                    file_path = os.path.join(factor_data_dir, file)
                    df = pd.read_csv(file_path)
                    if len(df) > 0:
                        df['trade_date'] = df['trade_date'].astype(str)
                        return df['trade_date'].max()
                    break
        except Exception as e:
            print(f"❌ 获取因子最新日期失败: {e}")
        return None
    
    def needs_factor_update(self, etf_code: str) -> bool:
        """判断是否需要更新因子"""
        latest_data_date = self.get_latest_data_date(etf_code)
        latest_factor_date = self.get_factor_latest_date(etf_code)
        
        if latest_data_date is None:
            print("❌ 无法获取数据最新日期")
            return False
            
        if latest_factor_date is None:
            print("💡 因子数据不存在，需要首次计算")
            return True
            
        print(f"📊 数据最新日期: {latest_data_date}")
        print(f"📈 因子最新日期: {latest_factor_date}")
        
        return latest_data_date > latest_factor_date
    
    def calculate_factors(self, etf_code: str, incremental: bool = True) -> bool:
        """计算因子数据"""
        if not self.should_calculate_factors(etf_code):
            return False
            
        if not self.needs_factor_update(etf_code):
            print("✅ 因子数据已是最新，无需计算")
            return True
            
        print(f"\n🔄 开始计算 {etf_code} 的技术因子...")
        
        try:
            # 准备因子计算环境
            original_cwd = os.getcwd()
            etf_factor_abs_dir = os.path.abspath(self.etf_factor_dir)
            
            # 切换到因子计算目录
            os.chdir(etf_factor_abs_dir)
            
            # 更新配置中的数据源路径
            self._update_factor_config(etf_code)
            
            # 直接使用etf_factor引擎
            print("📈 执行因子计算...")
            
            # 添加etf_factor路径到sys.path
            if self.etf_factor_dir not in sys.path:
                sys.path.insert(0, self.etf_factor_dir)
            
            # 使用importlib强制导入，避免缓存问题
            import importlib
            import importlib.util
            
            # 清除可能的模块缓存
            engine_module_name = 'src.engine'
            if engine_module_name in sys.modules:
                del sys.modules[engine_module_name]
            
            try:
                # 方法1：尝试正常导入
                from src.engine import VectorizedEngine
                print("✅ 使用正常导入成功")
            except ImportError as e:
                print(f"⚠️  正常导入失败: {e}")
                try:
                    # 方法2：使用importlib直接导入整个src包
                    import importlib.util
                    
                    # 先导入src包的__init__.py
                    src_init_path = os.path.join(self.etf_factor_dir, 'src', '__init__.py')
                    spec = importlib.util.spec_from_file_location("src", src_init_path)
                    src_module = importlib.util.module_from_spec(spec)
                    sys.modules['src'] = src_module
                    spec.loader.exec_module(src_module)
                    
                    # 再导入engine模块
                    engine_path = os.path.join(self.etf_factor_dir, 'src', 'engine.py')
                    spec = importlib.util.spec_from_file_location("src.engine", engine_path)
                    engine_module = importlib.util.module_from_spec(spec)
                    sys.modules['src.engine'] = engine_module
                    spec.loader.exec_module(engine_module)
                    
                    VectorizedEngine = engine_module.VectorizedEngine
                    print("✅ 使用importlib包导入成功")
                    
                except Exception as e2:
                    print(f"❌ importlib包导入也失败: {e2}")
                    # 方法3：最后的fallback，修改工作目录
                    original_cwd = os.getcwd()
                    try:
                        os.chdir(self.etf_factor_dir)
                        from src.engine import VectorizedEngine
                        print("✅ 通过修改工作目录导入成功")
                    finally:
                        os.chdir(original_cwd)
            
            # 创建引擎并计算因子
            data_dir = os.path.join(self.data_collection_dir, "data", etf_code.replace(".SH", "").replace(".SZ", ""))
            engine = VectorizedEngine(data_dir=data_dir, output_dir=os.path.join(self.etf_factor_dir, "factor_data"))
            
            print(f"📂 数据目录: {data_dir}")
            print(f"📈 注册因子: {len(engine.factors)} 个")
            
            # 计算所有因子
            results = engine.calculate_all_factors(use_cache=False)
            success = len(results) > 0
            
            if success and results:
                # 保存因子结果
                saved_files = engine.save_factor_results(results, output_type='single')
                print(f"💾 保存了 {len(saved_files)} 个因子文件")
            
            print(f"✅ 因子计算完成: {len(results)} 个因子")
            
            if success:
                # 构造成功的subprocess结果
                class MockResult:
                    def __init__(self):
                        self.returncode = 0
                        self.stdout = "因子计算成功"
                        self.stderr = ""
                result = MockResult()
            else:
                class MockResult:
                    def __init__(self):
                        self.returncode = 1
                        self.stdout = ""
                        self.stderr = "因子计算失败"
                result = MockResult()
            
            # 恢复原工作目录
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print("✅ 因子计算完成")
                print(result.stdout)
                return True
            else:
                print("❌ 因子计算失败")
                print(f"错误输出: {result.stderr}")
                if result.stdout:
                    print(f"标准输出: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 因子计算超时")
            os.chdir(original_cwd)
            return False
        except Exception as e:
            print(f"❌ 因子计算出错: {e}")
            os.chdir(original_cwd)
            return False
    
    def _update_factor_config(self, etf_code: str):
        """更新因子计算配置"""
        try:
            config_file = os.path.join(self.etf_factor_dir, "config/data.yaml")
            if os.path.exists(config_file):
                # 可以更新配置文件中的数据源路径
                # 这里简化处理，假设配置已正确设置
                pass
        except Exception as e:
            print(f"⚠️  更新因子配置失败: {e}")
    
    def get_factor_summary(self, etf_code: str) -> dict:
        """获取因子计算摘要"""
        summary = {
            "etf_code": etf_code,
            "factor_files": 0,
            "latest_date": None,
            "available_factors": []
        }
        
        try:
            # 使用按ETF代码分组的目录结构：factor_data/510300/
            etf_code_clean = etf_code.replace(".SH", "").replace(".SZ", "")
            factor_data_dir = os.path.join(self.etf_factor_dir, "factor_data", etf_code_clean)
            if not os.path.exists(factor_data_dir):
                return summary
                
            # 统计CSV因子文件
            factor_files = [f for f in os.listdir(factor_data_dir) if f.endswith('.csv')]
            summary["factor_files"] = len(factor_files)
            summary["available_factors"] = [f.replace('.csv', '') for f in factor_files]
            
            # 获取最新日期（从任意一个因子文件中）
            if factor_files:
                try:
                    import pandas as pd
                    first_file = os.path.join(factor_data_dir, factor_files[0])
                    df = pd.read_csv(first_file)
                    if 'trade_date' in df.columns and len(df) > 0:
                        summary["latest_date"] = df['trade_date'].astype(str).max()
                except:
                    pass
            
        except Exception as e:
            print(f"❌ 获取因子摘要失败: {e}")
        
        return summary
    
    def cleanup_factor_data(self, etf_code: str) -> bool:
        """清理指定ETF的因子数据"""
        print(f"🧹 清理 {etf_code} 的因子数据...")
        
        try:
            factor_data_dir = os.path.join(self.etf_factor_dir, "factor_data")
            etf_code_clean = etf_code.split('.')[0] if '.' in etf_code else etf_code
            etf_factor_dir = os.path.join(factor_data_dir, etf_code_clean)
            
            if os.path.exists(etf_factor_dir):
                # 统计文件数量
                factor_files = [f for f in os.listdir(etf_factor_dir) if f.endswith('.csv')]
                file_count = len(factor_files)
                
                # 删除整个ETF因子目录
                import shutil
                shutil.rmtree(etf_factor_dir)
                print(f"✅ 已删除 {file_count} 个因子文件: {etf_factor_dir}")
                return True
            else:
                print(f"⚠️  因子目录不存在: {etf_factor_dir}")
                return True  # 目录不存在也算成功
                
        except Exception as e:
            print(f"❌ 清理因子数据失败: {e}")
            return False