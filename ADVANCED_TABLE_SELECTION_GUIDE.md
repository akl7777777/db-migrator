# 🗃️ 高级表选择功能完全指南

## 概述

您的MySQL到PostgreSQL迁移工具现在支持强大的表选择功能，让您可以精确控制要迁移的表。本指南将详细介绍所有可用的表选择方法和高级功能。

## 🎯 功能特性

### ✨ 核心功能
- **🔍 智能搜索**: 实时搜索表名
- **📊 表信息显示**: 行数、大小、列数、类型
- **🎯 模式匹配**: 通配符批量选择
- **📈 统计分析**: 数据库整体统计
- **💡 表详情**: 双击查看表结构
- **⚡ 快捷操作**: 右键菜单和批量操作

### 🔧 高级功能
- **反选功能**: 一键反转当前选择
- **同类型选择**: 选择相同类型的所有表
- **过滤显示**: 按选择状态、大小、类型过滤
- **实时状态**: 动态显示选择统计信息

## 📱 图形化界面使用方法

### 1. 启动增强版GUI

```bash
cd /Users/takedayuuichi/PycharmProjects/db-migrator
export PYTHONPATH="/opt/homebrew/Cellar/python-tk@3.10/3.10.18/lib/python3.10/site-packages:$PYTHONPATH"
./start_gui.sh
```

### 2. 表选择界面操作

#### 基本操作
- **🔄 刷新表列表**: 获取数据库中所有表的详细信息
- **✅ 全选**: 选择当前显示的所有表
- **❌ 全不选**: 取消所有选择
- **🔍 按模式选择**: 使用通配符批量选择表
- **📊 表统计**: 查看数据库整体统计信息

#### 搜索和过滤
- **搜索框**: 输入关键词实时过滤表名
- **显示过滤器**: 
  - `all`: 显示所有表
  - `selected`: 仅显示已选择的表
  - `unselected`: 仅显示未选择的表
  - `large`: 显示大表（可设置行数阈值）
  - `small`: 显示小表
  - `empty`: 仅显示空表

#### 高级操作
- **双击表名**: 查看表的详细信息和结构
- **右键菜单**: 快捷操作（查看详情、选择/取消选择、选择同类型）
- **实时状态**: 底部状态栏显示选择统计

### 3. 模式选择对话框

点击 **🔍 按模式选择** 按钮打开高级选择对话框：

#### 预设模式
- **用户相关**: `user*` - 选择所有以user开头的表
- **订单相关**: `order*` - 选择所有订单相关表
- **日志表**: `*log*` - 选择所有包含log的表
- **临时表**: `temp*` - 选择所有临时表
- **备份表**: `backup*` - 选择所有备份表
- **配置表**: `*config*` - 选择所有配置表

#### 自定义模式
支持通配符语法：
- `*`: 匹配任意字符
- `?`: 匹配单个字符
- 示例:
  - `user_*`: 匹配 user_profiles, user_settings 等
  - `*_log`: 匹配 access_log, error_log 等
  - `temp_?_*`: 匹配 temp_1_data, temp_2_backup 等

## 💻 命令行工具使用方法

### 1. 交互式表选择

```bash
python -m db_migrator.cli.commands interactive
```

系统会询问是否选择特定表，然后提供交互式选择界面。

### 2. 直接指定表

```bash
python -m db_migrator.cli.commands migrate \
    --source "mysql://root:12345678@127.0.0.1:3306/shellapiminipool" \
    --target "postgresql://takedayuuichi:12345678@127.0.0.1:5432/shellapiminipool" \
    --tables "users,orders,products"
```

### 3. 使用通配符模式

```bash
python -m db_migrator.cli.commands migrate \
    --source "mysql://root:12345678@127.0.0.1:3306/shellapiminipool" \
    --target "postgresql://takedayuuichi:12345678@127.0.0.1:5432/shellapiminipool" \
    --pattern "user_*,order_*"
```

### 4. 排除特定表

```bash
python -m db_migrator.cli.commands migrate \
    --source "mysql://root:12345678@127.0.0.1:3306/shellapiminipool" \
    --target "postgresql://takedayuuichi:12345678@127.0.0.1:5432/shellapiminipool" \
    --exclude "*_log,temp_*,backup_*"
```

## 🚀 快速选择工具

### 1. 表选择器演示程序

```bash
python table_selector.py
```

功能特性：
- **示例数据预载**: 无需连接数据库即可体验功能
- **真实数据连接**: 可连接实际MySQL数据库
- **完整功能演示**: 包含所有高级选择功能
- **右键菜单**: 上下文相关操作
- **表详情查看**: 完整的表信息显示

### 2. 快速迁移脚本

```bash
python select_migrate.py
```

特性：
- **交互式选择**: 支持表名或序号选择
- **批量操作**: 逗号分隔多个选择
- **预览功能**: 迁移前显示选择统计
- **进度显示**: 实时迁移进度

使用示例：
```
请输入：users,orders,products     # 按表名选择
请输入：1,3,5                   # 按序号选择
请输入：all                     # 选择所有表
```

### 3. 配置文件方式

编辑 `selective_migration.yaml`:

```yaml
migration:
  options:
    # 要迁移的特定表
    tables: 
      - "users"
      - "orders" 
      - "products"
    
    # 要排除的表
    exclude_tables: 
      - "log_table"
      - "temp_table"
```

然后运行：
```bash
python -m db_migrator.cli.commands migrate --config selective_migration.yaml
```

## 📊 实用选择策略

### 1. 按业务模块分类迁移

```bash
# 用户模块
user_*, *_profile, *_auth

# 订单模块  
order_*, payment_*, invoice_*

# 商品模块
product_*, category_*, inventory_*

# 日志模块
*_log, *_audit, *_history
```

### 2. 按数据重要性分级迁移

```bash
# 核心数据 (优先迁移)
users, orders, products, payments

# 辅助数据 (次要)
logs, statistics, cache_*

# 临时数据 (可选)
temp_*, backup_*, test_*
```

### 3. 按数据大小策略迁移

```bash
# 小表先迁移 (< 1万行)
config_*, lookup_*, category_*

# 中等表 (1万-100万行)
users, products, orders

# 大表分批迁移 (> 100万行)
logs, analytics_*, history_*
```

## 🔧 高级技巧

### 1. 组合过滤使用

1. 先用搜索框过滤出感兴趣的表
2. 使用显示过滤器进一步筛选
3. 通过模式选择批量选择
4. 右键菜单精确调整

### 2. 预览和验证

1. 选择完表后，点击 **预览迁移** 
2. 查看迁移统计信息
3. 确认表数量和行数正确
4. 检查估算的迁移时间

### 3. 分批迁移策略

1. **第一批**: 配置表和小表
2. **第二批**: 核心业务表
3. **第三批**: 日志和历史数据
4. **最后批**: 临时和测试数据

### 4. 错误恢复

如果选择错误：
- 使用 **❌ 全不选** 重新开始
- 使用 **🔄 反选** 快速调整
- 通过搜索快速定位需要调整的表

## 🎯 最佳实践

### 1. 迁移前准备
- 先用表选择器了解数据库结构
- 查看表统计信息制定迁移策略
- 使用预览功能验证选择

### 2. 分阶段迁移
- 从小表开始测试
- 逐步增加复杂度
- 保留日志表最后迁移

### 3. 验证检查
- 每批迁移后检查数据完整性
- 对比源表和目标表行数
- 验证关键业务数据

## 🚀 总结

现在您的迁移工具提供了完整的表选择解决方案：

✅ **4种使用方式**: GUI、CLI、脚本、配置文件  
✅ **智能搜索过滤**: 快速定位目标表  
✅ **模式批量选择**: 通配符高效选择  
✅ **详细信息显示**: 表结构和统计信息  
✅ **实时状态更新**: 动态选择反馈  
✅ **多种选择策略**: 适应不同迁移需求  

无论是小规模的精确选择，还是大规模的批量迁移，您都可以找到合适的工具和方法！🎉 