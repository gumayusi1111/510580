# ETF量化交易系统

## 📈 项目简介
多ETF量化交易系统，支持自动化数据采集、技术因子计算、基本面分析和量化策略开发。

## 🏗️ 项目架构

### 核心特性
- **🚀 向量化计算** - 基于NumPy/Pandas，性能提升10-100倍
- **💾 智能缓存** - 内存+磁盘缓存，支持增量更新
- **⚙️ 全局配置** - 统一精度、格式、验证规则
- **📊 26+技术因子** - 涵盖5大类技术指标
- **💼 基本面数据** - ETF净值、份额、指数估值
- **🌍 宏观数据** - 利率、经济指标
- **🔧 可扩展架构** - 模块化因子，轻松添加新指标
- **📈 多ETF支持** - 510300.SH、510580.SH、513180.SH
- **🔄 自动更新** - 一键更新所有数据类型

### 目录结构
```
singleetfs/
├── data_collection/          # 数据采集系统 ✅
│   ├── src/                  # 核心采集模块（模块化重构）
│   │   ├── api/              # API管理模块
│   │   │   ├── api_client.py     # Tushare API客户端
│   │   │   └── token_manager.py  # Token管理器
│   │   ├── core/             # 核心业务模块
│   │   │   ├── data_processor.py # 数据处理器
│   │   │   ├── etf_updater.py    # ETF数据更新器
│   │   │   └── etf_operations.py # ETF操作管理器
│   │   ├── fundamental/      # 基本面数据模块
│   │   │   ├── get_etf_fundamental_data.py # 基本面数据获取
│   │   │   └── fundamental_data_manager.py # 基本面数据管理
│   │   ├── integration/      # 集成模块
│   │   │   ├── etf_discovery.py      # ETF发现服务
│   │   │   └── factor_calculator.py  # 因子计算集成
│   │   └── ui/               # 用户界面模块
│   │       └── interactive_menu.py   # 交互式菜单
│   ├── config/               # 采集配置
│   │   ├── settings.py       # 系统设置
│   │   └── __init__.py
│   ├── data/                 # 采集数据存储
│   │   ├── 510300/           # 沪深300ETF数据
│   │   ├── 510580/           # 中证500ETF数据
│   │   └── 513180/           # 纳指100ETF数据
│   ├── etf_manager.py        # ETF管理器
│   └── run.py                # 主运行程序
├── etf_factor/               # 因子计算引擎 ✅
│   ├── src/                  # 核心框架
│   │   ├── base_factor.py    # 向量化因子基类
│   │   ├── engine.py         # 向量化计算引擎
│   │   ├── data_loader.py    # 数据加载器
│   │   ├── data_writer.py    # 数据输出器
│   │   ├── cache.py          # 缓存管理器
│   │   └── config.py         # 配置管理
│   ├── factors/              # 因子实现 (26个模块) ✅
│   │   ├── sma/              # 简单移动均线
│   │   ├── ema/              # 指数移动均线
│   │   ├── wma/              # 加权移动均线
│   │   ├── ma_diff/          # 均线差值
│   │   ├── ma_slope/         # 均线斜率
│   │   ├── macd/             # MACD指标
│   │   ├── rsi/              # RSI指标
│   │   ├── roc/              # 变动率
│   │   ├── mom/              # 动量指标
│   │   ├── tr/               # 真实波幅
│   │   ├── atr/              # 平均真实波幅
│   │   ├── atr_pct/          # ATR百分比
│   │   ├── hv/               # 历史波动率
│   │   ├── boll/             # 布林带
│   │   ├── dc/               # 唐奇安通道
│   │   ├── bb_width/         # 布林带宽度
│   │   ├── stoch/            # 随机震荡器
│   │   ├── vma/              # 成交量均线
│   │   ├── volume_ratio/     # 量比
│   │   ├── obv/              # 能量潮
│   │   ├── kdj/              # KDJ指标
│   │   ├── cci/              # CCI指标
│   │   ├── wr/               # 威廉指标
│   │   ├── daily_return/     # 日收益率
│   │   ├── cum_return/       # 累计收益率
│   │   ├── annual_vol/       # 年化波动率
│   │   └── max_dd/           # 最大回撤
│   ├── factor_data/          # 因子数据输出目录 ✅
│   │   ├── technical/        # 技术因子数据
│   │   │   ├── 510300/           # 沪深300ETF技术因子
│   │   │   ├── 510580/           # 中证500ETF技术因子
│   │   │   ├── 513180/           # 纳指100ETF技术因子
│   │   │   └── complete/         # 完整技术因子数据集
│   │   ├── fundamental/      # 基本面数据
│   │   │   ├── 510300/           # 沪深300ETF基本面
│   │   │   │   ├── ETF_NAV.csv       # ETF净值数据
│   │   │   │   ├── ETF_SHARE.csv     # ETF份额数据
│   │   │   │   └── INDEX_VALUATION.csv # 指数估值数据
│   │   │   ├── 510580/           # 中证500ETF基本面
│   │   │   └── 513180/           # 纳指100ETF基本面
│   │   ├── macro/            # 宏观经济数据
│   │   │   └── SHIBOR_RATES.csv  # 银行间同业拆放利率
│   │   └── cache/            # 缓存文件
│   ├── config/               # 配置文件
│   │   ├── global.yaml       # 全局配置
│   │   ├── factors.yaml      # 因子配置
│   │   ├── data.yaml         # 数据配置
│   │   ├── cache.yaml        # 缓存配置
│   │   └── integration.yaml  # 集成配置
│   ├── scripts/              # 执行脚本
│   │   ├── run_factors.py    # 因子计算脚本
│   │   └── verify_system.py  # 系统验证脚本
│   ├── utils/                # 工具函数
│   ├── docs/                 # 文档
│   └── examples/             # 使用示例
└── logs/                     # 系统日志 ✅
    ├── etf_operations/       # ETF操作日志
    ├── factor_calculations/  # 因子计算日志
    ├── system/               # 系统日志
    └── manage_logs.py        # 日志管理
```

## 🚀 快速开始

### 1. 环境配置
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install PyYAML  # 配置文件支持
```

### 2. 配置Tushare Token
在 `data_collection/config/settings.py` 中配置你的Tushare Token

### 3. 数据采集和更新
```bash
# 启动数据采集系统（交互式菜单）
cd data_collection
python run.py

# 选择菜单选项：
# 1️⃣ 更新所有ETF到最新 (增量更新) - 自动更新所有数据+计算因子
# 2️⃣ 添加新的ETF代码
# 3️⃣ 删除ETF数据
# 4️⃣ 查看所有ETF状态
```

### 4. 使用因子库
```python
from etf_factor.src import VectorizedEngine

# 创建引擎
engine = VectorizedEngine()

# 计算单个因子
sma_result = engine.calculate_single_factor("SMA")

# 批量计算
factors = ["SMA", "EMA", "MACD", "RSI"]
results = engine.calculate_batch_factors(factors)

# 保存结果
engine.save_factor_results(results, output_type="single")
```

### 5. 手动计算因子（可选）
```bash
# 计算指定ETF的所有因子
python etf_factor/run_factors.py factor_data output 510300.SH

# 计算所有ETF的因子
python etf_factor/run_factors.py factor_data output
```

## 📊 因子清单

### 移动均线类 (5个)
- **SMA** - 简单移动均线 (5,10,20,60日)
- **EMA** - 指数移动均线 (5,10,20,60日) 
- **WMA** - 加权移动均线 (5,10,20,60日)
- **MA_DIFF** - 均线差值
- **MA_SLOPE** - 均线斜率

### 趋势动量类 (4个)
- **MACD** - 指数平滑移动平均线
- **RSI** - 相对强弱指标 (6,14,24日)
- **ROC** - 变动率 (5,10,20日)
- **MOM** - 动量指标 (5,10,20日)

### 波动率类 (8个)
- **TR** - 真实波幅
- **ATR** - 平均真实波幅 (14日)
- **ATR_PCT** - ATR百分比 (14日)
- **HV** - 历史波动率 (20,60日)
- **BOLL** - 布林带 (20日,2倍标准差)
- **DC** - 唐奇安通道 (20日)
- **BB_WIDTH** - 布林带宽度
- **STOCH** - 随机震荡器 (9日)

### 量价关系类 (6个)
- **VMA** - 成交量均线 (5,10,20日)
- **VOLUME_RATIO** - 量比 (5日)
- **OBV** - 能量潮
- **KDJ** - 随机指标 (9日)
- **CCI** - 顺势指标 (14日)
- **WR** - 威廉指标 (14日)

### 收益风险类 (4个)
- **DAILY_RETURN** - 日收益率
- **CUM_RETURN** - 累计收益率 (5,20,60日)
- **ANNUAL_VOL** - 年化波动率 (20,60日)
- **MAX_DD** - 最大回撤 (20,60日)

## ⚙️ 全局配置

### 精度控制
- 价格精度: 6位小数
- 百分比精度: 4位小数
- 指标精度: 4位小数
- 统计量精度: 6位小数

### 数据验证
- 价格范围: 0.001 - 10000.0
- 成交量范围: 0 - 1e10
- 百分比范围: -100% - 1000%

## 📈 支持的ETF

### 当前支持的ETF
- **510300.SH** - 沪深300ETF (华泰柏瑞)
- **510580.SH** - 中证500ETF (易方达)
- **513180.SH** - 纳指100ETF (国泰)

### 数据类型
1. **基础价格数据** - 开高低收、成交量、复权因子
2. **技术因子数据** - 26+个技术指标
3. **基本面数据** - ETF净值、份额、指数估值
4. **宏观经济数据** - 利率、经济指标

### 数据格式
- **复权处理**: 后复权用于技术因子计算，前复权用于当前价位分析
- **日期格式**: YYYYMMDD
- **精度控制**: 价格6位小数，指标4位小数
- **数据验证**: 完整的数据范围和格式验证

### 输出文件结构
```
etf_factor/factor_data/
├── technical/               # 技术因子数据
│   ├── 510300/                  # ETF代码分组
│   │   ├── SMA.csv                  # SMA因子所有周期
│   │   ├── EMA.csv                  # EMA因子所有周期
│   │   └── ... (其他因子)
│   └── complete/                # 完整技术因子数据集
├── fundamental/             # 基本面数据
│   └── {etf_code}/              # 按ETF分组的基本面数据
├── macro/                   # 宏观经济数据
└── cache/                   # 缓存文件
```

## 🛠️ 开发指南

### 添加新因子
1. 在 `etf_factor/factors/` 创建新的模块文件夹
2. 继承 `BaseFactor` 基类
3. 实现 `calculate_vectorized()` 方法
4. 使用向量化计算，禁止循环

```python
from etf_factor.src.base_factor import BaseFactor

class MyFactor(BaseFactor):
    def calculate_vectorized(self, data):
        # 向量化计算逻辑
        pass

    def get_required_columns(self):
        return ['hfq_close', 'vol']
```

### 性能优化
- 使用NumPy/Pandas向量化操作
- 启用智能缓存避免重复计算
- 批量计算多个因子提高效率

## 🎯 项目路线图

### 当前状态 ✅
- **26个因子计算完成** - 包含1697条历史数据记录
- **向量化计算引擎** - 高性能因子计算框架
- **完整数据集** - 2018-2025年7年历史数据

### 下一阶段：ETF择时短线策略开发 🚧

#### 第一阶段：因子分析与筛选
- [ ] **因子有效性分析**
  - IC值分析（信息系数）
  - 因子衰减测试
  - 因子稳定性验证
- [ ] **因子筛选与组合**
  - 去除高相关因子
  - 构建因子评分体系
  - 多因子组合权重优化

#### 第二阶段：择时信号系统
- [ ] **信号生成逻辑**
  - 多因子综合评分模型
  - 动态阈值设定机制
  - 买入/卖出信号规则
- [ ] **风控机制设计**
  - 止损止盈策略
  - 仓位管理规则
  - 最大回撤控制

#### 第三阶段：策略回测验证
- [ ] **历史数据回测**
  - 策略收益率测试
  - 风险指标计算（夏普比率、最大回撤等）
  - 参数敏感性分析
- [ ] **策略优化调参**
  - 参数网格搜索
  - 策略组合测试
  - 适应性改进

#### 第四阶段：模拟交易实盘
- [ ] **实时信号系统**
  - 实时数据接入
  - 信号生成与推送
  - 交易执行模拟
- [ ] **业绩跟踪分析**
  - 实盘表现监控
  - 策略效果评估
  - 持续优化迭代

### 技术栈规划
- **因子分析**: IC分析、相关性矩阵、PCA降维
- **信号系统**: 多因子评分、动态阈值、规则引擎
- **回测框架**: Vectorbt/Backtrader集成
- **实盘接口**: 券商API对接、实时数据流

## 📋 注意事项

- **数据安全**: 原始数据不上传到Git
- **计算结果**: factor_data目录被Git忽略
- **代码规范**: 每个文件<200行，单一职责
- **向量化**: 禁止使用Python循环，必须向量化

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目仅用于学习和研究目的。

---

**⚠️ 免责声明**: 本项目仅供学习研究使用，不构成投资建议。投资有风险，入市需谨慎。