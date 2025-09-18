# ETF因子脚本工具

本目录包含ETF因子计算和系统验证的实用脚本。

## 脚本列表

### 1. run_factors.py - 因子计算脚本

**功能**: 运行所有ETF因子计算，支持完整模式和简化模式

**用法**:
```bash
# 完整模式（默认）- 计算所有因子并保存完整数据集和单个文件
python run_factors.py

# 简化模式 - 仅使用缓存和保存单个因子文件
python run_factors.py --simple

# 自定义路径
python run_factors.py --data-dir ../../data_collection/data/510580 --output-dir ../factor_data
```

**参数说明**:
- `--simple`: 简化模式，使用缓存，仅保存单个因子文件
- `--data-dir`: 数据目录路径（默认: `../../data_collection/data/510580`）
- `--output-dir`: 输出目录路径（默认: `../factor_data`）

### 2. verify_system.py - 系统验证脚本

**功能**: 验证数据路径配置和因子数据质量完整性

**用法**:
```bash
# 完整验证（默认）
python verify_system.py

# 仅验证数据路径
python verify_system.py --skip-quality

# 仅验证因子质量
python verify_system.py --skip-paths

# 自定义路径
python verify_system.py --data-collection ../../data_collection --factor-data ../factor_data
```

**参数说明**:
- `--data-collection`: 数据采集目录路径（默认: `../../data_collection`）
- `--factor-data`: 因子数据目录路径（默认: `../factor_data`）
- `--skip-paths`: 跳过数据路径验证
- `--skip-quality`: 跳过因子质量验证

## 使用示例

### 典型工作流程

1. **首次运行因子计算**:
```bash
cd etf_factor/scripts
python run_factors.py
```

2. **验证系统状态**:
```bash
python verify_system.py
```

3. **后续快速更新**:
```bash
python run_factors.py --simple
```

### 输出说明

**run_factors.py 输出**:
- 因子发现和计算状态
- 执行时间统计
- 保存文件路径
- 性能指标（因子/秒）

**verify_system.py 输出**:
- 数据路径验证结果
- ETF数据文件统计
- 因子数据质量报告
- 数据完整性分析

## 注意事项

1. 确保在运行前已完成数据采集（`data_collection/run.py`）
2. 脚本会自动处理路径依赖和模块导入
3. 使用 `--help` 参数查看完整命令行选项
4. 验证脚本会提供详细的数据质量报告，包括空值、数据范围等统计信息