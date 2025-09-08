# ETF系统日志管理

本目录包含ETF数据管理系统的日志文件和管理工具。

## 目录结构

```
logs/
├── README.md                # 本说明文件
├── manage_logs.py          # 日志管理脚本
├── etf_operations/         # ETF操作日志
├── factor_calculations/    # 因子计算日志
├── system/                 # 系统事件日志
└── archives/              # 归档压缩文件
```

## 日志管理脚本

### 使用方法

```bash
cd logs
python manage_logs.py [选项]
```

### 命令选项

| 命令 | 说明 |
|-----|------|
| `--action status` | 查看日志系统状态（默认） |
| `--action clean` | 手动清理旧日志 |
| `--action archive` | 归档超期日志 |
| `--weeks N` | 清理时保留N周日志（默认2周） |
| `--days N` | 归档N天前的日志（默认30天） |
| `--force` | 强制执行，跳过确认提示 |

### 使用示例

```bash
# 查看日志状态
python manage_logs.py --action status

# 清理3周前的日志
python manage_logs.py --action clean --weeks 3

# 强制清理，无需确认
python manage_logs.py --action clean --force
```

## 自动清理机制

系统启动时会自动检查并执行每周清理：

- **检查频率**：每7天检查一次
- **保留策略**：默认保留最近2周的日志
- **归档方式**：旧日志压缩为ZIP文件保存到archives目录
- **压缩效果**：通常可压缩50-60%的存储空间

## 日志文件命名规则

### 操作日志
- `etf_{ETF代码}_{YYYYMMDD}.log` - 单个ETF操作日志
- `etf_operations_{YYYYMMDD}.log` - 通用操作日志

### 因子计算日志
- `factors_{ETF代码}_{YYYYMMDD}.log` - 单个ETF因子计算
- `factor_calculations_{YYYYMMDD}.log` - 通用因子计算

### 系统日志
- `system_{YYYYMMDD}.log` - 系统事件和错误日志

### 归档文件
- `logs_archive_{YYYYMMDD_HHMMSS}.zip` - 压缩归档文件

## 日志级别说明

| 级别 | 说明 | 关键词 |
|-----|------|--------|
| INFO | 正常操作 | 成功、完成、success、completed |
| WARNING | 警告信息 | 警告、warn、warning |
| ERROR | 错误事件 | 失败、错误、error、failed |

## 系统集成

日志功能已集成到ETF管理系统中：

1. **自动记录**：所有ETF操作和因子计算自动记录
2. **启动清理**：系统启动时自动检查清理需求
3. **状态监控**：可通过管理脚本随时查看日志状态

## 维护建议

- 定期检查归档目录大小
- 根据存储需求调整保留周数
- 监控系统日志中的ERROR级别事件
- 必要时手动执行清理操作