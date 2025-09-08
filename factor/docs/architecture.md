# ETF因子库架构设计

## 🎯 设计目标

### 核心要求
- **向量化计算**: 基于NumPy/Pandas向量化，避免循环
- **文件限制**: 每个代码文件不超过200行
- **缓存机制**: 支持增量更新，避免重复计算
- **高性能**: 批量计算25个因子，支持大数据量
- **可扩展**: 轻松添加新因子，无需修改核心代码  
- **可维护**: 代码结构清晰，单一职责原则

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                 Vectorized Factor Library               │
├─────────────────────────────────────────────────────────┤
│  🚀 Vectorized Engine (向量化引擎)                       │
│  ├── NumPy/Pandas 向量化计算                             │
│  ├── 批量因子计算管道                                     │
│  └── 内存优化处理                                        │
├─────────────────────────────────────────────────────────┤
│  💾 Cache Layer (缓存层)                                 │
│  ├── Redis/Memory Cache: 因子结果缓存                    │
│  ├── Incremental Update: 增量更新机制                    │
│  └── Cache Strategy: 缓存策略管理                        │
├─────────────────────────────────────────────────────────┤
│  📊 Factor Layer (因子层)                                │
│  ├── Single File per Factor: 每因子一个.py文件(<200行)   │
│  ├── Vectorized Implementation: 向量化实现               │
│  └── Standardized Interface: 标准化接口                  │
├─────────────────────────────────────────────────────────┤
│  📁 Data & Utils (数据工具层)                            │
│  ├── DataLoader: 数据加载                               │
│  ├── Vectorized Utils: 向量化工具                        │
│  └── Performance Monitor: 性能监控                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 目录结构设计

```
factor/
├── src/                          # 核心源码 (每个文件<200行)
│   ├── __init__.py
│   ├── engine.py                 # 向量化计算引擎 (<200行)
│   ├── cache.py                  # 缓存管理器 (<200行)
│   ├── data_loader.py            # 数据加载器 (<200行)
│   ├── data_writer.py            # 数据输出器 (<200行)
│   └── base_factor.py            # 因子基类 (<200行)
├── factors/                      # 因子实现 (每因子一个.py文件)
│   ├── __init__.py
│   # 移动均线类 (5个文件)
│   ├── sma.py                    # 简单移动均线 (<200行)
│   ├── ema.py                    # 指数移动均线 (<200行)
│   ├── wma.py                    # 加权移动均线 (<200行)
│   ├── ma_diff.py                # 均线差值 (<200行)
│   ├── ma_slope.py               # 均线斜率 (<200行)
│   # 趋势动量类 (4个文件)  
│   ├── macd.py                   # MACD (<200行)
│   ├── rsi.py                    # RSI (<200行)
│   ├── roc.py                    # ROC (<200行)
│   ├── mom.py                    # 动量 (<200行)
│   # 波动率类 (8个文件)
│   ├── tr.py                     # 真实波幅 (<200行)
│   ├── atr.py                    # ATR (<200行)
│   ├── atr_pct.py                # ATR百分比 (<200行)
│   ├── hv.py                     # 历史波动率 (<200行)
│   ├── boll.py                   # 布林带 (<200行)
│   ├── dc.py                     # 唐奇安通道 (<200行)
│   ├── bb_width.py               # 布林带宽度 (<200行)
│   ├── stoch.py                  # 随机震荡器 (<200行)
│   # 量价关系类 (7个文件)
│   ├── vma.py                    # 成交量均线 (<200行)
│   ├── volume_ratio.py           # 量比 (<200行)
│   ├── obv.py                    # OBV (<200行)
│   ├── kdj.py                    # KDJ (<200行)
│   ├── cci.py                    # CCI (<200行)
│   ├── wr.py                     # WR (<200行)
│   ├── mfi.py                    # MFI (<200行)
│   # 收益风险类 (4个文件)
│   ├── daily_return.py           # 日收益率 (<200行)
│   ├── cum_return.py             # 累计收益率 (<200行)
│   ├── annual_vol.py             # 年化波动率 (<200行)
│   └── max_dd.py                 # 最大回撤 (<200行)
├── utils/                        # 工具模块 (每个文件<200行)
│   ├── __init__.py
│   ├── vectorized.py             # 向量化计算工具 (<200行)
│   ├── performance.py            # 性能监控 (<200行)
│   └── validation.py             # 数据验证 (<200行)
├── config/                       # 配置文件
│   ├── factors.yaml              # 因子配置
│   ├── cache.yaml                # 缓存配置
│   └── data.yaml                 # 数据配置
├── tests/                        # 测试 (每个文件<200行)
│   ├── test_engine.py
│   ├── test_cache.py
│   └── test_factors.py
├── factor_data/                 # 因子输出目录  
│   ├── single_factors/          # 单因子文件 (推荐方式)
│   │   ├── SMA_510580_SH.csv   # 包含SMA_5, SMA_10, SMA_20, SMA_60
│   │   ├── EMA_510580_SH.csv   # 包含EMA_5, EMA_10, EMA_20, EMA_60
│   │   ├── MACD_510580_SH.csv  # 包含MACD_DIF, MACD_DEA, MACD_HIST
│   │   ├── RSI_510580_SH.csv   # 包含RSI_6, RSI_14, RSI_24
│   │   └── ... (25个单因子文件)
│   ├── factor_groups/           # 因子组合文件 (可选)
│   │   ├── moving_average_510580_SH.csv    # 移动均线类5个因子合并
│   │   ├── trend_momentum_510580_SH.csv    # 趋势动量类4个因子合并
│   │   └── ... (5个分组文件)
│   ├── complete/                # 完整因子数据 (可选)
│   │   └── all_factors_510580_SH.csv      # 全部25个因子合并
│   └── cache/                   # 缓存文件
│       ├── factor_cache.pkl     # 因子缓存
│       └── metadata.json        # 元数据
├── examples/                     # 使用示例
│   ├── basic_usage.py
│   ├── incremental_update.py
│   └── performance_test.py
└── docs/                         # 文档
    ├── factor_list.md
    ├── architecture.md
    └── vectorization_guide.md
```

---

## 🔧 核心组件设计

### 1. BaseFactor (向量化因子基类) - 50行
```python
class BaseFactor(ABC):
    """向量化因子基类 - 每个子类<200行"""
    
    def __init__(self, params: dict = None):
        self.params = params or {}
        self.name = self.__class__.__name__
        self.cache_key = None
    
    @abstractmethod  
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """向量化计算 - 必须使用NumPy/Pandas向量化操作"""
        pass
    
    def get_cache_key(self, data_hash: str) -> str:
        """生成缓存键"""
        return f"{self.name}_{data_hash}_{hash(str(self.params))}"
```

### 2. VectorizedEngine (向量化引擎) - 180行
```python
class VectorizedEngine:
    """向量化计算引擎"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.data_loader = DataLoader()
        self.factors = self._discover_factors()
    
    def calculate_batch_vectorized(self, factor_names: list, 
                                  data: pd.DataFrame) -> pd.DataFrame:
        """批量向量化计算"""
        # 1. 检查缓存
        # 2. 批量向量化计算未缓存因子  
        # 3. 合并结果
        # 4. 更新缓存
        pass
    
    def calculate_incremental(self, new_data: pd.DataFrame):
        """增量更新计算"""
        pass
```

### 3. CacheManager (缓存管理器) - 150行  
```python
class CacheManager:
    """缓存管理器 - 支持增量更新"""
    
    def __init__(self, cache_dir="factor_data/cache"):
        self.cache_dir = cache_dir
        self.memory_cache = {}
        self.cache_file = f"{cache_dir}/factor_cache.pkl"
        self.metadata_file = f"{cache_dir}/metadata.json"
    
    def get_cached_factor(self, cache_key: str) -> pd.DataFrame:
        """获取缓存的因子"""
        pass
    
    def cache_factor(self, cache_key: str, result: pd.DataFrame):
        """缓存因子结果到内存和磁盘"""
        pass
    
    def save_cache_to_disk(self):
        """保存缓存到磁盘"""
        pass
    
    def load_cache_from_disk(self):
        """从磁盘加载缓存"""
        pass
```

### 4. DataWriter (数据输出器) - 180行
```python
class DataWriter:
    """数据输出管理器"""
    
    def __init__(self, output_dir="factor_data"):
        self.output_dir = output_dir
        self.ensure_directories()
    
    def save_single_factor(self, factor_name: str, data: pd.DataFrame, 
                          symbol="510580_SH"):
        """保存单个因子到 single_factors/"""
        file_path = f"{self.output_dir}/single_factors/{factor_name}_{symbol}.csv"
        data.to_csv(file_path, index=False)
    
    def save_factor_group(self, group_name: str, data: pd.DataFrame,
                         symbol="510580_SH"):
        """保存因子组到 factor_groups/"""
        file_path = f"{self.output_dir}/factor_groups/{group_name}_{symbol}.csv"
        data.to_csv(file_path, index=False)
    
    def save_complete_factors(self, data: pd.DataFrame, symbol="510580_SH"):
        """保存完整因子数据到 complete/"""
        file_path = f"{self.output_dir}/complete/all_factors_{symbol}.csv"
        data.to_csv(file_path, index=False)
    
    def ensure_directories(self):
        """创建输出目录结构"""
        dirs = ["single_factors", "factor_groups", "complete", "cache"]
        for dir_name in dirs:
            os.makedirs(f"{self.output_dir}/{dir_name}", exist_ok=True)
```

### 5. 单文件因子示例 (SMA) - 120行
```python  
import numpy as np
import pandas as pd
from src.base_factor import BaseFactor

class SMA(BaseFactor):
    """简单移动均线 - 向量化实现"""
    
    def __init__(self, periods=[5, 10, 20, 60]):
        super().__init__({"periods": periods})
        
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """向量化计算SMA"""
        result = data[['ts_code', 'trade_date']].copy()
        
        # 向量化计算所有周期的SMA
        for period in self.params["periods"]:
            col_name = f'SMA_{period}'
            result[col_name] = data['hfq_close'].rolling(
                window=period, min_periods=1
            ).mean()
        
        return result
    
    def get_required_columns(self) -> list:
        return ['ts_code', 'trade_date', 'hfq_close']
```

---

## 🌊 数据流设计

```
1. 数据输入 (../data/)
   ├── 510580_SH_basic_data.csv     → 基础数据 + 复权因子
   ├── 510580_SH_raw_data.csv       → 原始交易数据  
   ├── 510580_SH_hfq_data.csv       → 后复权数据
   └── 510580_SH_qfq_data.csv       → 前复权数据
                    ↓
2. 数据预处理 (DataLoader)
   ├── 数据类型转换 (date, float)
   ├── 数据质量检查 (缺失值, 异常值)
   ├── 数据排序 (按日期)
   └── 列名标准化
                    ↓
3. 缓存检查 (CacheManager)  
   ├── 检查因子是否已缓存
   ├── 验证数据一致性
   └── 确定需要计算的因子
                    ↓
4. 向量化因子计算 (VectorizedEngine)
   ├── 移动均线类  → 使用 hfq_* 字段
   ├── 趋势动量类  → 使用 hfq_* 字段  
   ├── 波动率类    → 使用 hfq_* 字段
   ├── 量价关系类  → 使用 vol, amount 字段
   └── 收益风险类  → 使用 hfq_* 字段
                    ↓
5. 结果缓存 (CacheManager)
   ├── 内存缓存更新
   ├── 磁盘缓存保存
   └── 元数据更新
                    ↓
6. 数据输出 (DataWriter → factor_data/)
   ├── single_factors/    → SMA_510580_SH.csv (一个因子一个文件)
   │                        EMA_510580_SH.csv (一个因子一个文件)  
   │                        MACD_510580_SH.csv (一个因子一个文件)
   │                        ... (25个独立文件)
   ├── factor_groups/     → moving_average_510580_SH.csv (可选分组)
   ├── complete/          → all_factors_510580_SH.csv (可选全量)
   └── cache/             → factor_cache.pkl (缓存文件)
```

---

## ⚙️ 配置管理设计

### factor_config.yaml
```yaml
# 因子参数配置
moving_average:
  SMA:
    periods: [5, 10, 20, 60]
    data_type: "hfq"
  EMA:
    periods: [5, 10, 20, 60]
    data_type: "hfq"

trend_momentum:
  MACD:
    fast: 12
    slow: 26
    signal: 9
    data_type: "hfq"
  RSI:
    periods: [6, 14, 24]
    data_type: "hfq"
```

### data_config.yaml  
```yaml
# 数据源配置
data_sources:
  basic_data: "../data/510580_SH_basic_data.csv"
  raw_data: "../data/510580_SH_raw_data.csv" 
  hfq_data: "../data/510580_SH_hfq_data.csv"
  qfq_data: "../data/510580_SH_qfq_data.csv"

data_columns:
  basic: ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount", "adj_factor"]
  hfq: ["ts_code", "trade_date", "hfq_open", "hfq_high", "hfq_low", "hfq_close", "vol", "amount"]
  qfq: ["ts_code", "trade_date", "qfq_open", "qfq_high", "qfq_low", "qfq_close", "vol", "amount"]
```

---

## 🚀 使用示例设计

### 向量化批量计算
```python
from factor.src import VectorizedEngine

# 1. 创建向量化引擎
engine = VectorizedEngine()

# 2. 批量向量化计算 (利用缓存)
factors = ["SMA", "EMA", "MACD", "RSI"]
result = engine.calculate_batch_vectorized(factors, use_cache=True)

# 3. 增量更新 (只计算新数据)
new_data = engine.load_incremental_data("2025-09-06")
engine.calculate_incremental(new_data)
```

### 单文件因子开发 (<200行)
```python
# factors/custom_factor.py
import numpy as np
import pandas as pd
from src.base_factor import BaseFactor

class CustomFactor(BaseFactor):
    """自定义因子 - 向量化实现 <200行"""
    
    def __init__(self, param1=10, param2=20):
        super().__init__({"param1": param1, "param2": param2})
    
    def calculate_vectorized(self, data: pd.DataFrame) -> pd.DataFrame:
        """必须使用向量化计算 - 禁用循环"""
        result = data[['ts_code', 'trade_date']].copy()
        
        # 向量化计算示例
        result['CUSTOM'] = (
            data['hfq_close'].rolling(self.params['param1']).mean() /
            data['hfq_close'].rolling(self.params['param2']).mean()
        )
        
        return result
```

### 缓存和增量更新
```python
# 首次计算 - 全量计算并缓存+输出
result = engine.calculate_batch_vectorized(["SMA", "EMA"])
engine.save_factors(result, output_type="single")  # 保存到factor_data/

# 后续计算 - 从缓存加载
cached_result = engine.calculate_batch_vectorized(["SMA", "EMA"])  # 极速

# 新数据到达 - 增量更新+输出
engine.add_new_data("2025-09-06", new_row_data)
updated_result = engine.get_latest_factors(["SMA", "EMA"])
engine.save_incremental_update(updated_result)  # 增量保存

# 批量输出所有因子
all_factors = engine.calculate_all_factors()
engine.save_complete_dataset(all_factors)  # 保存到factor_data/complete/
```

---

## 🔄 扩展性设计

### 1. 新增因子流程
1. 在对应分类目录创建因子文件
2. 继承BaseFactor基类
3. 实现calculate方法
4. 使用@FactorFactory.register装饰器注册
5. 更新配置文件

### 2. 新增数据源
1. 在DataLoader中添加新的数据加载方法
2. 更新data_config.yaml配置
3. 添加数据验证逻辑

### 3. 性能优化点
- 数据缓存机制
- 并行计算支持
- 增量更新支持
- 内存优化 (分块处理)

---

## 📋 开发计划

### Phase 1: 向量化核心框架 (1-2天)
- [ ] BaseFactor向量化基类 (<50行)
- [ ] VectorizedEngine计算引擎 (<180行) 
- [ ] CacheManager缓存管理器 (<150行)
- [ ] DataLoader数据加载器 (<200行)
- [ ] DataWriter数据输出器 (<180行)
- [ ] 向量化工具函数 (<200行)

### Phase 2: 25个因子实现 (3-4天，每个文件<200行)
- [ ] 移动均线类: sma.py, ema.py, wma.py, ma_diff.py, ma_slope.py
- [ ] 趋势动量类: macd.py, rsi.py, roc.py, mom.py  
- [ ] 波动率类: tr.py, atr.py, atr_pct.py, hv.py, boll.py, dc.py, bb_width.py, stoch.py
- [ ] 量价关系类: vma.py, volume_ratio.py, obv.py, kdj.py, cci.py, wr.py, mfi.py
- [ ] 收益风险类: daily_return.py, cum_return.py, annual_vol.py, max_dd.py

### Phase 3: 性能优化和测试 (1-2天)
- [ ] 向量化性能测试
- [ ] 缓存效率测试
- [ ] 增量更新测试  
- [ ] 内存使用优化

---

## ✅ 架构总结

### 核心特点
1. **向量化计算**: 全部使用NumPy/Pandas向量化操作
2. **文件限制**: 每个文件严格<200行，单一职责
3. **缓存机制**: 支持增量更新，避免重复计算
4. **单文件因子**: 每个因子一个.py文件，便于维护
5. **标准化接口**: 统一的BaseFactor基类

### 回答您的问题
**Q: 每一个因子就一个py够吗还是需要一个文件夹？**
**A: 一个.py文件够了！**
- 每个因子功能单一，<200行完全够用
- 文件夹会增加复杂度，单文件更简洁
- 25个因子 = 25个.py文件，清晰明了

### 性能优势  
- **向量化**: 比循环快10-100倍
- **缓存**: 二次计算接近0耗时
- **增量**: 新数据只计算增量部分
- **批量**: 一次性计算多个因子

*向量化因子库架构 v2.0 | 25个单文件因子 | 缓存+增量更新*