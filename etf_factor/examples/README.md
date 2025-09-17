# Examples Directory

## 📂 使用示例

这个目录提供ETF因子库的使用参考和最佳实践指南。

### 🛠️ 快速开始

#### 1. 基础因子计算
```python
from etf_factor.src.engine import VectorizedEngine

# 创建引擎
engine = VectorizedEngine()

# 计算单个因子
sma_result = engine.calculate_single_factor("SMA")

# 批量计算
results = engine.calculate_batch_factors(["SMA", "EMA", "MACD"])

# 保存结果
engine.save_factor_results(results, output_type="single")
```

#### 2. 性能优化使用
```python
# 启用缓存加速
result = engine.calculate_single_factor("SMA", use_cache=True)

# 批量计算提高效率
factors = ["SMA", "EMA", "MACD", "RSI", "ATR"]
results = engine.calculate_batch_factors(factors)

# 查看引擎信息
info = engine.get_engine_info()
print(f"发现 {info['factor_count']} 个因子")
```

### 📊 性能说明

- **向量化计算**: 比循环实现快10-100倍
- **智能缓存**: 二次计算接近0耗时
- **批量处理**: 一次性计算多个因子
- **内存优化**: 支持大数据量处理

### 🔗 相关资源

1. **系统测试**: `../tests/test_system_validation.py`
2. **架构文档**: `../docs/architecture.md`
3. **因子清单**: `../docs/factor_list.md`
4. **核心引擎**: `../src/engine.py`

### 💡 使用建议

1. **开发环境**: 查看系统测试了解完整功能
2. **生产环境**: 启用缓存机制提升性能
3. **大数据量**: 使用批量计算减少IO开销
4. **调试问题**: 查看日志和数据质量报告

---
*ETF因子库使用指南和最佳实践*