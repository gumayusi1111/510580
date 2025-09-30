quant_trading/                    # 量化交易分析系统
├── analyzers/                    # 分析器模块(核心)
│   ├── ic/                      # IC分析
│   │   ├── core.py             # IC计算核心
│   │   ├── fast_core.py        # 快速IC计算(向量化)
│   │   └── analyzer.py         # IC分析器(智能适应性)
│   ├── correlation/            # 相关性分析
│   │   ├── core.py            # 相关性计算与冗余检测
│   │   ├── analyzer.py        # 相关性分析器
│   │   └── selection.py       # 因子筛选(v3支持total_score选择)
│   ├── factor_evaluation/     # 因子评估(v3.0)
│   │   ├── evaluator.py       # 主评估器
│   │   └── evaluation/        # 评估子模块
│   │       ├── single_evaluation.py    # 单因子评估
│   │       ├── batch_evaluation.py     # 批量评估
│   │       ├── ranking.py              # 因子排序
│   │       └── selection.py            # 筛选建议
│   └── redundancy_analyzer.py  # 因子去重分析器(v3.0新增)
│
├── core/                        # 核心数据模块
│   ├── data_management/        # 数据管理
│   │   ├── manager.py         # 数据管理器
│   │   └── cache.py           # 缓存管理
│   ├── loading/               # 数据加载
│   │   ├── loader.py          # 基础加载器
│   │   ├── technical.py       # 技术因子
│   │   ├── fundamental.py     # 基本面因子
│   │   └── macro.py           # 宏观因子
│   ├── processing/            # 数据处理
│   │   ├── cleaner.py         # 数据清洗
│   │   ├── transformer.py     # 数据转换
│   │   └── calculator.py      # 计算器
│   ├── validation/            # 数据验证
│   │   ├── validator.py       # 验证器
│   │   ├── structure.py       # 结构验证
│   │   ├── continuity.py      # 连续性验证
│   │   └── quality.py         # 质量验证
│   └── factor_classifier.py   # 因子分类器
│
├── utils/                       # 工具模块
│   ├── statistics/             # 统计工具
│   │   ├── scoring/           # 评分系统(v3.0)
│   │   │   ├── config.py      # v3权重配置
│   │   │   ├── ic_scorer.py   # IC评分
│   │   │   ├── stability_scorer.py  # 稳定性评分
│   │   │   ├── quality_scorer.py    # 质量评分
│   │   │   └── grading.py     # 评级系统
│   │   ├── scorer.py          # 向后兼容接口
│   │   ├── calculator.py      # 统计计算
│   │   └── analyzer.py        # 统计分析
│   └── reporting/             # 报告生成
│       ├── generator.py       # Markdown报告生成器
│       ├── formatter.py       # 格式化工具
│       └── templates.py       # 报告模板
│
├── config/                      # 配置模块
│   └── window_config.py        # 窗口配置
│
├── validation/                  # 验证模块
│   └── cross_validator.py      # 交叉验证器
│
├── strategies/                  # 策略模块(待开发)
│   ├── base_strategy.py        # 基础策略
│   └── signal_generation/      # 信号生成
│
├── tests/                       # 测试模块
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── archived/               # 归档测试
│
├── docs/                        # 文档
│   ├── design/                 # 设计文档
│   ├── api/                    # API文档
│   ├── guides/                 # 使用指南
│   └── examples/               # 示例代码
│
├── reports/                     # 输出目录
│   ├── <etf_code>/             # 各ETF分析报告
│   ├── _archive/               # 历史报告归档
│   ├── .logs/                  # 运行日志
│   └── .cache/                 # 临时缓存
│
├── scripts/                     # 脚本工具
│   ├── analysis/               # 分析脚本
│   ├── data/                   # 数据处理脚本
│   └── utils/                  # 工具脚本
│
├── run_analysis.py             # 主运行脚本
├── README.md                   # 项目说明
└── .gitignore                  # Git忽略配置

关键文件说明:
- **core/**: 数据加载、处理、验证的核心逻辑
- **analyzers/**: IC分析、相关性分析、因子评估、去重分析
- **utils/statistics/**: 统计工具和v3.0评分系统
- **config/**: 策略配置和窗口参数
- **validation/**: 样本外验证和交叉验证
- **run_analysis.py**: 主运行脚本,支持--deduplicate参数

v3.0核心改进:
- ✅ 评分权重优化 (IC 40%, 稳定性 25%, 分布 20%)
- ✅ 因子去重系统 (35%冗余识别)
- ✅ 系统细节修复 (Numpy警告、时间显示)
- ✅ 文档完善更新
