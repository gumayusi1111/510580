# ETF因子库项目 - 510580.SH

## 📈 项目简介
基于 **510580.SH（中证500ETF易方达）** 的向量化因子计算库，专注于高性能量化因子计算与分析。

## 🏗️ 项目架构

### 核心特性
- **🚀 向量化计算** - 基于NumPy/Pandas，性能提升10-100倍
- **💾 智能缓存** - 内存+磁盘缓存，支持增量更新
- **⚙️ 全局配置** - 统一精度、格式、验证规则
- **📊 26个因子** - 涵盖5大类技术指标
- **🔧 可扩展架构** - 模块化因子，轻松添加新指标

### 目录结构
```
singleetfs/
├── data_collection/          # 数据采集系统
│   ├── src/                  # 核心采集模块
│   │   ├── api_client.py     # API客户端
│   │   ├── etf_operations.py # ETF操作管理
│   │   ├── data_processor.py # 数据处理器
│   │   └── token_manager.py  # Token管理
│   ├── config/               # 采集配置
│   ├── data/                 # 采集数据存储
│   └── run.py                # 主运行程序
├── etf_factor/               # 因子计算引擎
│   ├── src/                  # 核心框架
│   │   ├── base_factor.py    # 向量化因子基类
│   │   ├── engine.py         # 向量化计算引擎
│   │   ├── data_loader.py    # 数据加载器
│   │   ├── data_writer.py    # 数据输出器
│   │   └── cache.py          # 缓存管理器
│   ├── factors/              # 因子实现 (26个模块)
│   │   ├── sma/              # 简单移动均线模块
│   │   ├── ema/              # 指数移动均线模块
│   │   ├── macd/             # MACD指标模块
│   │   └── ... (23个更多因子模块)
│   ├── factor_data/          # 输出目录 (git忽略)
│   │   ├── single/           # 单因子文件
│   │   ├── complete/         # 完整数据集
│   │   └── cache/            # 缓存文件
│   ├── utils/                # 工具函数
│   ├── tests/                # 单元测试
│   └── examples/             # 使用示例
├── quant_trading/            # 量化分析框架
│   ├── core/                 # 核心数据管理
│   ├── analyzers/            # 分析器模块
│   │   ├── ic/               # IC分析
│   │   ├── correlation/      # 相关性分析
│   │   └── layering/         # 分层回测
│   ├── reports/              # 分析报告
│   └── config/               # 分析配置
└── logs/                     # 系统日志
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

### 2. 获取数据
```bash
cd data_collection
python run.py
```

### 3. 使用因子库
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

## 📈 数据说明

### ETF基础信息
- **标的**: 510580.SH (中证500ETF易方达)
- **数据范围**: 2018-09-10 至 2025-09-05
- **记录数**: ~1695条交易记录
- **复权处理**: 后复权用于计算，前复权用于展示

### 输出文件
```
etf_factor/factor_data/
├── 510580/                  # ETF代码分组
│   ├── SMA_510580.csv       # SMA因子所有周期
│   ├── EMA_510580.csv       # EMA因子所有周期
│   └── ... (其他因子)
├── single/                  # 单因子文件
├── complete/                # 完整数据集
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