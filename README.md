# 数据库迁移工具 (Database Migrator)

一个功能强大的数据库迁移工具，支持MySQL到PostgreSQL的数据迁移，包含图形界面和命令行两种使用方式。

## ✨ 主要特性

- 🔄 **完整的数据迁移**: 支持表结构、数据、索引的完整迁移
- 🎯 **智能类型转换**: 自动处理MySQL到PostgreSQL的数据类型映射
- 🔢 **序列自动更新**: 自动处理AUTO_INCREMENT到SERIAL的转换
- 📊 **进度监控**: 实时显示迁移进度和详细日志
- 🖥️ **图形界面**: 现代化的GUI界面，操作简单直观
- ⚡ **批量处理**: 支持大数据量的分批迁移
- 🔍 **预览功能**: 迁移前可预览表结构和数据量
- 💾 **配置保存**: 支持数据库配置的保存和加载
- 🛡️ **错误处理**: 完善的错误处理和恢复机制

![image](https://github.com/user-attachments/assets/443c074b-c43c-4021-8c99-c9c843562515)

![image](https://github.com/user-attachments/assets/d6a19880-eb2b-44b5-ae4c-e6c1d61b83d5)


## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 方式一：图形界面（推荐）

启动图形界面：

```bash
python run_gui.py
```

![GUI界面预览](docs/gui_preview.png)

### 方式二：命令行示例

运行命令行示例：

```bash
python run_example.py
```

或者直接运行示例：

```bash
python examples/mysql_to_postgresql_example.py
```

## 📖 使用说明

### 图形界面使用

1. **数据库配置**
   - 填写MySQL源数据库连接信息
   - 填写PostgreSQL目标数据库连接信息
   - 点击"测试连接"验证配置

2. **迁移设置**
   - 设置批处理大小（默认1000）
   - 选择是否包含索引迁移
   - 刷新并选择要迁移的表

3. **执行迁移**
   - 点击"预览迁移"查看迁移概况
   - 点击"开始迁移"执行迁移
   - 在"迁移日志"标签页查看实时进度

### 命令行使用

```python
from db_migrator.migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator

# 配置数据库连接
mysql_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'username': 'root',
    'password': 'password',
    'database': 'source_db'
}

postgresql_config = {
    'host': '127.0.0.1',
    'port': 5432,
    'username': 'postgres',
    'password': 'password',
    'database': 'target_db'
}

# 创建迁移器
migrator = MySQLToPostgreSQLMigrator(mysql_config, postgresql_config)

# 测试连接
connections = migrator.test_connections()
if all(connections.values()):
    # 执行迁移
    results = migrator.migrate()
    print(f"迁移完成: {results['migrated_tables']}/{results['total_tables']} 个表")
```

## 🏗️ 项目结构

```
db-migrator/
├── README.md                           # 项目说明
├── requirements.txt                    # 依赖包列表
├── setup.py                           # 安装配置
├── run_gui.py                         # GUI启动脚本
├── run_example.py                     # 命令行示例启动脚本
├── config/
│   └── config.yaml                    # 配置文件示例
├── db_migrator/                       # 主要代码目录
│   ├── __init__.py
│   ├── core/                          # 核心模块
│   │   ├── base_connector.py          # 数据库连接器基类
│   │   └── type_mapper.py             # 数据类型映射
│   ├── connectors/                    # 数据库连接器
│   │   ├── mysql_connector.py         # MySQL连接器
│   │   └── postgresql_connector.py    # PostgreSQL连接器
│   ├── migrators/                     # 迁移器
│   │   └── mysql_to_postgresql.py     # MySQL到PostgreSQL迁移器
│   ├── gui/                           # 图形界面
│   │   ├── __init__.py
│   │   └── main_window.py             # 主窗口
│   └── cli/                           # 命令行界面
│       └── commands.py                # 命令行命令
├── examples/                          # 示例代码
│   └── mysql_to_postgresql_example.py # 完整迁移示例
└── tests/                             # 测试代码
    ├── test_connectors.py
    └── test_migrators.py
```

## 🔧 配置说明

### MySQL配置项

```python
mysql_config = {
    'host': '127.0.0.1',           # 服务器地址
    'port': 3306,                  # 端口号
    'username': 'root',            # 用户名
    'password': 'password',        # 密码
    'database': 'source_db',       # 数据库名
    'options': {                   # 可选参数
        'charset': 'utf8mb4',
        'auth_plugin': 'caching_sha2_password'
    }
}
```

### PostgreSQL配置项

```python
postgresql_config = {
    'host': '127.0.0.1',           # 服务器地址
    'port': 5432,                  # 端口号
    'username': 'postgres',        # 用户名
    'password': 'password',        # 密码
    'database': 'target_db',       # 数据库名
    'options': {                   # 可选参数
        'sslmode': 'disable'
    }
}
```

## 📊 数据类型映射

| MySQL类型 | PostgreSQL类型 | 说明 |
|-----------|----------------|------|
| INT | INTEGER | 整数类型 |
| BIGINT | BIGINT | 大整数 |
| VARCHAR(n) | VARCHAR(n) | 可变长字符串 |
| TEXT | TEXT | 文本类型 |
| DATETIME | TIMESTAMP | 日期时间 |
| DECIMAL(p,s) | DECIMAL(p,s) | 定点数 |
| JSON | JSON | JSON类型 |
| BLOB | BYTEA | 二进制数据 |
| AUTO_INCREMENT | SERIAL | 自增序列 |

## 🌟 高级功能

### 选择性表迁移

```python
# 只迁移指定的表
results = migrator.migrate(tables=['users', 'orders', 'products'])
```

### 自定义批处理大小

```python
# 设置较大的批处理大小以提高性能
results = migrator.migrate(batch_size=5000)
```

### 跳过索引迁移

```python
# 只迁移数据，跳过索引创建
results = migrator.migrate(include_indexes=False)
```

### 进度监控

```python
def progress_callback(message, current=0, total=0):
    if total > 0:
        print(f"进度: {current}/{total} - {message}")
    else:
        print(f"状态: {message}")

migrator.set_progress_callback(progress_callback)
```

## 🐛 常见问题

### 1. 连接数据库失败

- 检查数据库服务是否启动
- 验证主机地址、端口、用户名、密码是否正确
- 确认防火墙设置允许连接

### 2. 权限不足

确保数据库用户具有以下权限：

**MySQL用户权限：**
```sql
GRANT SELECT ON source_database.* TO 'username'@'%';
```

**PostgreSQL用户权限：**
```sql
GRANT CREATE, CONNECT ON DATABASE target_database TO username;
GRANT CREATE ON SCHEMA public TO username;
```

### 3. 内存不足

对于大型数据库，可以：
- 减小批处理大小
- 选择性迁移表
- 增加系统内存

### 4. 字符编码问题

确保：
- MySQL使用UTF-8编码
- PostgreSQL数据库编码为UTF-8

## 📝 日志记录

程序会自动生成详细的日志文件：

- GUI模式：`logs/gui.log`
- 命令行模式：`migration_YYYYMMDD_HHMMSS.log`

日志包含：
- 迁移进度信息
- 错误和警告消息
- 性能统计信息

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## 🙏 致谢

- [MySQL Connector Python](https://pypi.org/project/mysql-connector-python/)
- [psycopg2](https://pypi.org/project/psycopg2/)
- [CustomTkinter](https://pypi.org/project/customtkinter/)

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/db-migrator/issues)
- 发送邮件到 contact@dbmigrator.com

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
