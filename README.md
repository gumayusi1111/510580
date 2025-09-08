# ETF因子库项目 - 510580.SH

## 📈 项目简介
基于 **510580.SH（中证500ETF易方达）** 的向量化因子计算库，专注于高性能量化因子计算与分析。

## 🏗️ 项目架构

### 核心特性
- **🚀 向量化计算** - 基于NumPy/Pandas，性能提升10-100倍
- **💾 智能缓存** - 内存+磁盘缓存，支持增量更新
- **⚙️ 全局配置** - 统一精度、格式、验证规则
- **📊 25个因子** - 涵盖5大类技术指标
- **🔧 可扩展架构** - 单文件因子，轻松添加新指标

### 目录结构
```
singleetfs/
├── factor/                    # 因子库核心
│   ├── src/                   # 核心框架
│   │   ├── base_factor.py     # 向量化因子基类
│   │   ├── engine.py          # 向量化计算引擎  
│   │   ├── data_loader.py     # 数据加载器
│   │   ├── data_writer.py     # 数据输出器
│   │   ├── cache.py           # 缓存管理器
│   │   └── config.py          # 全局配置管理
│   ├── factors/               # 因子实现 (25个)
│   │   ├── sma.py            # 简单移动均线
│   │   ├── ema.py            # 指数移动均线
│   │   ├── macd.py           # MACD指标
│   │   └── ... (22个更多因子)
│   ├── config/               # 配置文件
│   │   ├── global.yaml       # 全局配置
│   │   ├── factors.yaml      # 因子参数
│   │   └── data.yaml         # 数据配置
│   ├── factor_data/          # 输出目录 (git忽略)
│   │   ├── single_factors/   # 单因子文件
│   │   ├── factor_groups/    # 因子分组
│   │   └── complete/         # 完整数据集
│   ├── utils/                # 工具函数
│   ├── tests/                # 单元测试
│   └── examples/             # 使用示例
├── data/                     # 原始数据 (git忽略)
├── src/                      # 数据获取脚本
└── docs/                     # 项目文档
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
cd src
python etf_data_complete.py
```

### 3. 使用因子库
```python
from factor.src import VectorizedEngine

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

### 量价关系类 (7个)
- **VMA** - 成交量均线 (5,10,20日)
- **VOLUME_RATIO** - 量比 (5日)
- **OBV** - 能量潮
- **KDJ** - 随机指标 (9日)
- **CCI** - 顺势指标 (14日)
- **WR** - 威廉指标 (14日)
- **MFI** - 资金流量指数 (14日)

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
factor_data/
├── single_factors/           # 每个因子一个文件
│   ├── SMA_510580_SH.csv    # SMA因子所有周期
│   ├── EMA_510580_SH.csv    # EMA因子所有周期
│   └── ...
├── factor_groups/           # 按类别分组
│   ├── moving_average_510580_SH.csv
│   └── ...
└── complete/                # 完整数据集
    └── all_factors_510580_SH.csv
```

## 🛠️ 开发指南

### 添加新因子
1. 在 `factor/factors/` 创建新的.py文件
2. 继承 `BaseFactor` 基类
3. 实现 `calculate_vectorized()` 方法
4. 使用向量化计算，禁止循环

```python
from src.base_factor import BaseFactor

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