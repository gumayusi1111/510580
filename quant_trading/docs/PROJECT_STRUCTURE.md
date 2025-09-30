quant_trading/                    # 量化交易分析系统
├── analyzers/                    # 分析器模块(核心)
│   ├── ic/                      # IC分析
│   │   ├── core.py             # IC计算核心(175行,已优化)
│   │   ├── fast_core.py        # 快速IC计算(205行)
│   │   └── analyzer.py         # IC分析器(508行,待重构→4模块)
│   ├── correlation/            # 相关性分析
│   │   ├── core.py            # 相关性计算(241行,待重构→2模块)
│   │   ├── analyzer.py        # 分析器(203行)
│   │   └── selection.py       # 因子筛选(181行)
│   └── factor_evaluation/     # 因子评估
│       └── evaluator.py       # 评估器(410行,待重构→4模块)
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
│   │   ├── scoring/           # 评分系统(已重构✅)
│   │   │   ├── config.py      # 配置(119行)
│   │   │   ├── ic_scorer.py   # IC评分(128行)
│   │   │   ├── stability_scorer.py  # 稳定性(55行)
│   │   │   ├── quality_scorer.py    # 质量(140行)
│   │   │   └── grading.py     # 评级(103行)
│   │   ├── scorer.py          # 向后兼容接口(54行)
│   │   ├── calculator.py      # 统计计算(172行)
│   │   └── analyzer.py        # 统计分析(153行)
│   └── reporting/             # 报告生成
│       ├── generator.py       # 报告生成器
│       ├── formatter.py       # 格式化
│       └── templates.py       # 模板
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
- core/: 数据加载、处理、验证的核心逻辑
- analyzers/: IC分析、相关性分析、因子评估
- utils/statistics/: 统计工具和评分系统(已模块化✅)
- config/: 策略配置和窗口参数
- validation/: 样本外验证和交叉验证

待重构模块(Phase 2):
1. analyzers/ic/analyzer.py (508行 → 4模块)
2. analyzers/factor_evaluation/evaluator.py (410行 → 4模块)
3. analyzers/correlation/core.py (241行 → 2模块)
