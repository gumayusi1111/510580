# 📚 ETF量化交易系统文档

## 文档结构

```
docs/
├── README.md                              # 文档导航（本文件）
├── PROJECT_STRUCTURE.md                   # 项目目录结构说明
├── ic_system_technical_specification.md   # IC计算系统技术规范
├── system_optimization_plan.md            # 系统优化计划（历史）
├── guides/                                # 使用指南
│   └── QUICK_START.md                     # 快速开始指南
├── design/                                # 设计文档
│   └── system_optimization_recommendations.md
├── api/                                   # API文档（待完善）
└── examples/                              # 示例代码（待完善）
```

## 快速导航

### 🚀 新手入门
- [快速开始](guides/QUICK_START.md) - 5分钟上手指南
- [项目结构](PROJECT_STRUCTURE.md) - 了解代码组织

### 🔬 技术规范
- [IC计算系统](ic_system_technical_specification.md) - 因子IC分析技术文档
- [评分系统](../utils/statistics/scoring/config.py) - 因子评分配置

### 📊 核心功能

#### 1. 因子评估系统
**位置**: `analyzers/factor_evaluation/`

**功能**:
- 单因子评估（IC、稳定性、质量分析）
- 批量因子评估（80+因子并行分析）
- 因子排序和筛选建议

**评分体系** (v3优化版):
```
总分 = IC(40%) + 稳定性(25%) + 质量(10%) + 分布(20%) + 一致性(5%)

权重优化历史:
- v2 (已废弃): IC 50%, Stability 20%, Distribution 15%
- v3 (当前): IC 40%, Stability 25%, Distribution 20%

优化理由: 降低IC权重避免高IC低稳定因子虚高,提高稳定性权重重视可靠性
```

**使用示例**:
```python
from quant_trading.analyzers.factor_evaluation import FactorEvaluator

evaluator = FactorEvaluator(strategy_type='short_term')
result = evaluator.evaluate_all_factors(etf_code='510580')
```

#### 2. IC分析系统
**位置**: `analyzers/ic/`

**功能**:
- 传统IC分析（固定前瞻期）
- 适应性IC分析（自动选择最优前瞻期）
- 批量IC计算和排序

**技术特性**:
- Z-score标准化（避免量纲影响）
- 快速向量化计算（10x加速）
- 滚动IC稳定性分析

#### 3. 相关性分析
**位置**: `analyzers/correlation/`

**功能**:
- 因子相关性矩阵
- 冗余因子识别
- 相关性结构分析

#### 4. 数据管理
**位置**: `core/data_management.py`

**功能**:
- 因子数据加载
- 收益率数据处理
- 完整因子合并

## 🎯 评级标准

### IC值标准（ETF因子）
| 评级 | IC阈值 | 说明 |
|------|--------|------|
| A级 | ≥0.08 | 优秀因子（稀缺） |
| B级 | ≥0.05 | 良好因子（推荐使用） |
| C级 | ≥0.03 | 可用因子（备选） |
| D级 | ≥0.02 | 较弱因子（谨慎使用） |
| F级 | <0.02 | 淘汰因子 |

### 总分评级
| 评级 | 总分阈值 | 建议 |
|------|----------|------|
| A级 | ≥0.80 | 核心因子，优先使用 |
| B级 | ≥0.65 | 良好因子，推荐组合 |
| C级 | ≥0.45 | 备选因子，补充使用 |
| D级 | ≥0.30 | 较弱因子，观察改进 |
| F级 | <0.30 | 淘汰因子，不建议使用 |

## 📁 重要配置文件

### 窗口配置
**文件**: `config/window_config.py`

定义不同策略类型的窗口参数：
- `short_term`: 短线策略（推荐用于ETF）
- `ultra_short`: 超短线策略
- `medium_term`: 中线策略

### 评分配置
**文件**: `utils/statistics/scoring/config.py`

定义评分权重和阈值：
- 权重配置 (`ScoringWeights`)
- IC阈值 (`ICThresholds`)
- 评级阈值 (`GradeThresholds`)

## 🔧 开发指南

### 代码规范
- 模块化设计（单文件<150行）
- 多级目录结构
- 完整的文档字符串
- 类型注解

### 测试建议
```bash
# 运行因子评估（标准模式）
python quant_trading/run_analysis.py short_term 510580

# 运行因子评估（带去重分析，推荐实盘使用）
python quant_trading/run_analysis.py short_term 510580 --deduplicate

# 查看报告
ls reports/510580/
```

### 因子去重功能 (v3新增)
**位置**: `analyzers/redundancy_analyzer.py`

**功能**: 识别冗余因子组（RSI系列、移动均线、MACD系列等），基于总分推荐最佳因子

**效果**:
- 减少因子数量35%（80→52）
- 降低多重共线性
- 保留所有高质量因子

**使用**:
```bash
# 集成到主流程
python quant_trading/run_analysis.py short_term 510300 --deduplicate

# 单独运行
python quant_trading/analyzers/redundancy_analyzer.py 510300
```

## 📝 更新日志

### v3.0 (2025-09-30)
- ✅ 评分权重优化：v2(IC 50%) → v3(IC 40%, Stability 25%, Distribution 20%)
- ✅ 因子去重功能：自动识别7类冗余因子组，减少35%冗余
- ✅ 集成去重到主流程：`--deduplicate` 参数
- ✅ 更新文档：v3权重说明和去重使用指南

### v2.0 (2025-09-30)
- ✅ 完成模块化重构（IC、评估、评分模块）
- ✅ 修复Z-score标准化
- ✅ 优化评分权重（IC 50%）
- ✅ 添加consistency_score到CSV导出
- ✅ 整理文档结构

### v1.0 (历史版本)
- 基础因子评估功能
- IC计算系统
- 报告生成

## 🤝 贡献指南

如需添加新功能或修复bug，请：
1. 遵循现有代码结构
2. 添加完整文档注释
3. 更新相关文档
4. 运行测试验证

## 📧 联系方式

项目位置: `/Users/wenbai/Desktop/singleetfs/quant_trading`
