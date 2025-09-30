# 快速开始指南

## 1. 环境准备

### 1.1 Python环境
- Python 3.8+
- pip包管理器

### 1.2 创建虚拟环境
\`\`\`bash
cd /Users/wenbai/Desktop/singleetfs
python -m venv venv
source venv/bin/activate
\`\`\`

### 1.3 安装依赖
\`\`\`bash
pip install pandas numpy scipy
\`\`\`

## 2. 基础使用

### 2.1 运行因子分析
\`\`\`bash
cd quant_trading
python run_analysis.py short_term 510580
\`\`\`

### 2.2 参数说明
- **策略类型**:
  - `short_term`: 短线(1-4周)  
  - `ultra_short`: 超短线(日内-周)
  - `medium_short`: 中短线(月级别)
  - `medium_term`: 中线(季度)

- **ETF代码**: 如510580(科技ETF)

### 2.3 输出文件
\`\`\`
reports/510580/
├── factor_evaluation_510580_<timestamp>.md  # 详细分析报告
└── factor_ranking_510580_<timestamp>.csv    # 因子排序CSV
\`\`\`

## 3. 编程接口

### 3.1 因子评估
\`\`\`python
from analyzers.factor_evaluation import FactorEvaluator

# 初始化
evaluator = FactorEvaluator(strategy_type='short_term')

# 评估单个因子
result = evaluator.evaluate_single_factor('RSI_3', '510580')
print(f"因子评级: {result['evaluation_score']['grade']}")
print(f"总分: {result['evaluation_score']['total_score']:.3f}")

# 批量评估
all_results = evaluator.evaluate_all_factors('510580')
top_factors = all_results['factor_ranking'].head(10)
print(top_factors)
\`\`\`

### 3.2 IC分析
\`\`\`python
from analyzers.ic import ICAnalyzer
from core.data_management import DataManager

# 加载数据
dm = DataManager()
factor_data = dm.get_factor_data(['RSI_3'], '510580')
returns = dm.get_returns_data('510580')

# IC分析
analyzer = ICAnalyzer(strategy_type='short_term', enable_adaptive=True)
ic_result = analyzer.analyze_factor_ic_adaptive(
    factor_data['RSI_3'], 
    returns
)

print(f"IC均值: {ic_result.statistics['period_1']['ic_mean']:.4f}")
print(f"IC IR: {ic_result.statistics['period_1']['ic_ir']:.4f}")
print(f"推荐前瞻期: {ic_result.primary_period}天")
\`\`\`

### 3.3 相关性分析
\`\`\`python
from analyzers.correlation import CorrelationAnalyzer

analyzer = CorrelationAnalyzer()

# 分析因子相关性
result = analyzer.analyze_correlation_structure(factor_data)

# 查看高相关因子对
high_corr = result['high_correlation_pairs']['pearson']
for factor1, factor2, corr in high_corr[:5]:
    print(f"{factor1} <-> {factor2}: {corr:.3f}")

# 查看冗余因子组
redundant = result['redundant_groups']['pearson']
for group_id, factors in redundant.items():
    print(f"{group_id}: {factors}")
\`\`\`

## 4. 自定义配置

### 4.1 调整评分权重
\`\`\`python
from utils.statistics.scoring import ScoringWeights, ScoringConfig, FactorScoring

# 自定义权重
weights = ScoringWeights(
    ic=0.60,              # 提高IC权重
    stability=0.15,       # 降低稳定性
    data_quality=0.10,
    distribution=0.10,
    consistency=0.05
)

config = ScoringConfig()
config.weights = weights

# 使用自定义配置
scoring = FactorScoring(config)
\`\`\`

### 4.2 修改IC阈值
\`\`\`python
from utils.statistics.scoring import ICThresholds

thresholds = ICThresholds(
    excellent=0.10,      # 提高A级标准
    good=0.06,
    fair=0.04,
    acceptable=0.02,
    weak=0.01
)

config.ic_thresholds = thresholds
\`\`\`

## 5. 常见问题

### 5.1 ModuleNotFoundError
确保已安装scipy:
\`\`\`bash
pip install scipy
\`\`\`

### 5.2 数据加载失败
检查数据路径配置:
\`\`\`python
# 数据应在以下路径
/Users/wenbai/Desktop/singleetfs/etf_factor/factor_data/
\`\`\`

### 5.3 IC值异常高
已修复(2025-09-30): IC计算添加Z-score标准化

## 6. 下一步

- 查看[项目结构](../PROJECT_STRUCTURE.md)了解详细架构
- 阅读[设计文档](../design/)理解核心逻辑
- 参考[API文档](../api/)学习更多接口

---
更新时间: 2025-09-30
