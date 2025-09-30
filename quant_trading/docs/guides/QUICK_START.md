# 快速开始指南 (v3.0)

## 1. 环境准备

### 1.1 Python环境
- Python 3.8+
- pip包管理器

### 1.2 创建虚拟环境
```bash
cd /Users/wenbai/Desktop/singleetfs
python -m venv venv
source venv/bin/activate
```

### 1.3 安装依赖
```bash
pip install pandas numpy scipy tushare
```

## 2. 基础使用

### 2.1 运行因子分析
```bash
cd quant_trading

# 标准模式（完整80因子分析）
python run_analysis.py short_term 510580

# 推荐模式（带去重，实盘使用）✅
python run_analysis.py short_term 510580 --deduplicate
```

### 2.2 参数说明
- **策略类型**:
  - `short_term`: 短线(1-4周) - **推荐用于ETF**
  - `ultra_short`: 超短线(日内-周)
  - `medium_short`: 中短线(月级别)
  - `medium_term`: 中线(季度)
  - `multi_timeframe`: 多时间框架

- **ETF代码**:
  - 510300 (沪深300ETF)
  - 510580 (科创50ETF)
  - 513180 (纳指ETF)

- **可选参数**:
  - `--deduplicate`: 启用因子去重分析（推荐）

### 2.3 输出文件
```
reports/510580/
├── factor_evaluation_510580_<timestamp>.md  # 详细分析报告
├── factor_ranking_510580_<timestamp>.csv    # 因子排序CSV
└── (去重分析输出，如果使用--deduplicate)
```

## 3. 编程接口

### 3.1 因子评估
```python
from analyzers.factor_evaluation import FactorEvaluator
from core.data_management import DataManager

# 初始化
data_manager = DataManager()
evaluator = FactorEvaluator(data_manager, strategy_type='short_term')

# 评估单个因子
result = evaluator.evaluate_single_factor('RSI_3', '510580')
print(f"因子评级: {result['evaluation_score']['grade']}")
print(f"总分: {result['evaluation_score']['total_score']:.3f}")
print(f"IC分: {result['evaluation_score']['ic_score']:.3f}")
print(f"稳定性分: {result['evaluation_score']['stability_score']:.3f}")

# 批量评估
all_results = evaluator.evaluate_all_factors('510580')
top_factors = all_results['factor_ranking'].head(10)
print(top_factors)
```

### 3.2 IC分析
```python
from analyzers.ic import ICAnalyzer
from core.data_management import DataManager

# 加载数据
dm = DataManager()
factor_data, returns = dm.get_factor_and_returns(['RSI_3'], '510580')

# IC分析（适应性）
analyzer = ICAnalyzer(strategy_type='short_term', enable_adaptive=True)
ic_result = analyzer.analyze_factor_ic_adaptive(
    factor_data['RSI_3'],
    returns['DAILY_RETURN']
)

print(f"IC均值: {ic_result.statistics['period_1']['ic_mean']:.4f}")
print(f"IC_IR: {ic_result.statistics['period_1']['ic_ir']:.4f}")
print(f"推荐前瞻期: {ic_result.primary_period}天")
print(f"IC胜率: {ic_result.statistics['period_1']['ic_positive_ratio']:.2%}")
```

### 3.3 因子去重分析
```python
from analyzers.redundancy_analyzer import analyze_redundancy

# 运行去重分析
analyze_redundancy('510300', threshold=0.85)

# 输出结果：
# - 识别冗余组（RSI/STOCH/KDJ/MA/MACD/VOL/BOLL）
# - 推荐保留因子
# - 建议移除因子
```

### 3.4 相关性分析
```python
from analyzers.correlation.core import RedundancyDetector
from analyzers.correlation.selection import FactorSelector

detector = RedundancyDetector()

# 计算相关性矩阵
corr_matrix = detector.calculate_correlation_matrix(factor_data, method='pearson')

# 识别冗余组
redundant_groups = detector.identify_redundant_groups(corr_matrix, threshold=0.85)

# 选择最佳因子
from analyzers.correlation.selection import FactorSelector
best_factor = FactorSelector.select_by_total_score(factors, ranking_data)
```

## 4. 自定义配置

### 4.1 评分权重配置 (v3.0)
```python
from utils.statistics.scoring import ScoringWeights, ScoringConfig, FactorScoring

# v3.0默认权重
weights = ScoringWeights(
    ic=0.40,              # IC表现 (40%)
    stability=0.25,       # 稳定性 (25%)
    data_quality=0.10,    # 数据质量 (10%)
    distribution=0.20,    # 分布合理性 (20%)
    consistency=0.05      # 一致性 (5%)
)

# 自定义权重（不推荐修改，除非有充分理由）
custom_weights = ScoringWeights(
    ic=0.50,              # 如果非常重视预测能力
    stability=0.20,
    data_quality=0.10,
    distribution=0.15,
    consistency=0.05
)

config = ScoringConfig(weights=custom_weights)
scoring = FactorScoring(config)
```

### 4.2 修改IC阈值
```python
from utils.statistics.scoring import ICThresholds

# ETF因子IC阈值（默认）
thresholds = ICThresholds(
    excellent=0.08,      # A级: ≥8%
    good=0.05,           # B级: 5-8%
    fair=0.03,           # C级: 3-5%
    acceptable=0.02,     # D级: 2-3%
    weak=0.01            # F级: <2%
)

config.ic_thresholds = thresholds
```

### 4.3 窗口参数配置
```python
from config.window_config import WindowConfig

# 自定义窗口（短线策略）
config = WindowConfig(
    strategy_type='short_term',
    ic_windows=[10, 20, 30],        # IC分析窗口
    primary_window=20,              # 主窗口
    stability_window=60,            # 稳定性分析窗口
    adaptive_periods=[1, 3, 5]      # 适应性前瞻期
)
```

## 5. 常见问题

### 5.1 ModuleNotFoundError
确保已安装所有依赖:
```bash
pip install pandas numpy scipy tushare
```

### 5.2 数据加载失败
检查数据路径:
```python
# 技术因子数据路径
/Users/wenbai/Desktop/singleetfs/etf_factor/factor_data/technical/

# 基础数据路径
/Users/wenbai/Desktop/singleetfs/etf_factor/factor_data/fundamental/<etf_code>/
```

### 5.3 Numpy RuntimeWarning
已修复(v3.0): 所有相关性计算已添加警告抑制

### 5.4 报告时间显示异常
已修复(v3.0): 时间范围现在显示为日期字符串而非索引值

### 5.5 NAV因子IC为0
正常现象: NAV因子本质平滑，预测性弱，不适合作为ETF交易因子

## 6. 评级解读

### 6.1 因子评级标准
| 评级 | 总分 | IC | 稳定性 | 建议 |
|-----|------|-----|--------|------|
| A级 | ≥0.80 | ≥8% | 高 | 核心因子，优先使用 |
| B级 | 0.65-0.80 | 5-8% | 中-高 | 良好因子，推荐组合 |
| C级 | 0.45-0.65 | 3-5% | 中 | 备选因子，补充使用 |
| D级 | 0.30-0.45 | 2-3% | 低-中 | 较弱因子，谨慎使用 |
| F级 | <0.30 | <2% | 低 | 淘汰因子 |

### 6.2 典型A级因子
- **RSI系列** (RSI_3/4/5/6): 相对强弱指标
- **WR_14**: 威廉指标
- **STOCH_K_9**: 随机指标
- **KDJ_J_9**: KDJ指标
- **SMA_5/10**: 短期均线

## 7. 下一步

### 7.1 深入学习
- 查看 [项目结构](../PROJECT_STRUCTURE.md) 了解详细架构
- 阅读 [IC系统规范](../ic_system_technical_specification.md) 理解核心逻辑
- 参考 [优化建议](../design/system_optimization_recommendations.md) 了解系统演进

### 7.2 进入第二阶段
v3.0已完成**第一阶段：因子分析与筛选**，下一步是：
- 实现多因子择时策略
- 信号生成系统
- 回测框架

查看 [文档导航](../README.md) 了解完整开发路线。

---

**版本**: v3.0
**更新时间**: 2025-09-30
**当前阶段**: 第一阶段完成