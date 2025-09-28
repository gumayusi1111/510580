# ETF日志系统 - 模块化架构

## 🏗️ 架构设计

### 设计原则
- **模块化** - 代码和数据分离，高内聚低耦合
- **专业性** - 企业级日志系统设计
- **精准记录** - 只记录关键信息，避免冗余
- **多文件输出** - 分类存储不同类型的日志

### 目录结构
```
logs/
├── system/                    # 日志系统代码模块
│   ├── core/                  # 核心引擎
│   │   ├── config_manager.py  # 配置管理器
│   │   ├── formatter.py       # 日志格式化器
│   │   └── logger.py          # 主日志器
│   ├── handlers/              # 处理器模块
│   │   ├── file_handler.py    # 文件处理器
│   │   └── summary_handler.py # 汇总处理器
│   ├── config.yaml            # 系统配置文件
│   └── __init__.py            # 统一接口
├── output/                    # 日志输出文件
│   ├── current.log            # 详细运行日志
│   ├── summary.log            # 运行汇总
│   └── errors.log             # 错误专用日志
└── README.md                  # 说明文档
```

## 🔧 使用方法

### 简单用法
```python
from logs.system import get_etf_logger

logger = get_etf_logger()
logger.startup(etf_count=3, token_valid=True)
logger.update_etf('510300', success=True, records=12, duration=2.3)
logger.factor_calculation('510300', success=True, factors=26, duration=4.1)
logger.error('API', 'Token过期')
logger.shutdown()
```

### API接口

#### 系统操作
- `startup(etf_count, token_valid)` - 记录系统启动
- `shutdown()` - 记录系统关闭并生成汇总

#### 业务操作
- `update_etf(etf_code, success, records, duration, error_msg)` - 记录ETF数据更新
- `factor_calculation(etf_code, success, factors, duration, error_msg)` - 记录因子计算
- `error(component, error_msg)` - 记录错误事件

## 📊 日志输出示例

### current.log - 详细运行日志
```
[16:08:51] STARTUP SYSTEM | Token验证通过, 管理3个ETF
[16:08:51] UPDATE ETF | 510300: 获取12条数据, 耗时2.3s
[16:08:51] ERROR ETF | 510580: 周末无交易数据
[16:08:51] FACTOR CALC | 510300: 计算26个因子, 耗时4.1s
[16:08:51] SHUTDOWN SYSTEM | 总耗时14s, 处理1个ETF, 获取12条记录
```

### summary.log - 运行汇总
```
运行时间: 14s
处理ETF: 1个
获取数据: 12条记录
计算因子: 26个
错误数量: 1
ETF列表: 510300
```

### errors.log - 错误专用
```
[16:08:51] ERROR ETF | 510580: 周末无交易数据
[16:08:51] ERROR SYSTEM | API: Token即将过期
```

## ⚙️ 配置管理

### config.yaml 配置文件
```yaml
output:
  directory: "output"           # 输出目录
  clear_on_start: true          # 启动时清空日志

formatting:
  timestamp: "%H:%M:%S"         # 时间格式
  current_template: "[{time}] {level} {module} | {message}"
  summary_template: "{message}"
  error_template: "[{time}] ERROR {module} | {message}"
```

## ✨ 核心特性

### 自动化管理
- **启动清空** - 每次启动自动清空旧日志
- **智能分类** - 自动分类存储不同类型的日志
- **自动汇总** - 运行结束时自动生成统计汇总

### 模块化设计
- **高内聚** - 每个模块职责单一
- **低耦合** - 通过接口和配置解耦
- **可扩展** - 易于添加新的处理器和格式化器

### 性能优化
- **故障容错** - 日志写入失败不影响主程序
- **配置驱动** - 无需修改代码即可调整行为
- **内存高效** - 实时写入，不占用过多内存

## 🎯 设计优势

1. **代码数据分离** - system/ 存放代码，output/ 存放数据
2. **企业级架构** - 参考工业标准的日志系统设计
3. **精准记录** - 只记录关键信息，提高信噪比
4. **维护简单** - 模块化设计，易于理解和维护