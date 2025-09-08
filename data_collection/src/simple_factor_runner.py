#!/usr/bin/env python3
"""
简化的因子计算执行器
直接调用因子计算引擎
"""

import os
import sys

def run_simple_factor_calculation():
    """简化的因子计算执行"""
    try:
        # 切换到因子系统目录
        original_cwd = os.getcwd()
        etf_factor_dir = os.path.join(original_cwd, "etf_factor")
        
        if not os.path.exists(etf_factor_dir):
            print(f"❌ 因子系统目录不存在: {etf_factor_dir}")
            return False
            
        os.chdir(etf_factor_dir)
        
        # 添加路径
        sys.path.insert(0, '.')
        
        print("🔄 开始因子计算...")
        
        # 导入并执行
        from src.engine import VectorizedEngine
        
        # 创建引擎
        engine = VectorizedEngine(
            data_dir="../data_collection/data/510580",
            output_dir="factor_data"
        )
        
        print("📊 计算所有因子...")
        results = engine.batch_calculate_all()
        
        print(f"✅ 因子计算完成: {len(results)} 个因子")
        
        return True
        
    except Exception as e:
        print(f"❌ 因子计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢复工作目录
        os.chdir(original_cwd)

if __name__ == "__main__":
    success = run_simple_factor_calculation()
    if success:
        print("🎉 因子计算成功！")
    else:
        print("💥 因子计算失败！")