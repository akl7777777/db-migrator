# Database Migrator Project

一个支持主流数据库之间互相迁移的工具，支持选择性表迁移、数据类型映射、序列处理等功能。

## 项目结构

```
db-migrator/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   └── config.yaml
├── db_migrator/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_connector.py
│   │   ├── base_migrator.py
│   │   └── type_mapper.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── mysql_connector.py
│   │   ├── postgresql_connector.py
│   │   ├── oracle_connector.py
│   │   ├── sqlserver_connector.py
│   │   └── sqlite_connector.py
│   ├── migrators/
│   │   ├── __init__.py
│   │   ├── mysql_to_postgresql.py
│   │   ├── postgresql_to_mysql.py
│   │   ├── mysql_to_mysql.py
│   │   └── universal_migrator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── progress.py
│   │   └── validators.py
│   └── cli/
│       ├── __init__.py
│       └── commands.py
├── tests/
│   ├── __init__.py
│   ├── test_connectors.py
│   ├── test_migrators.py
│   └── test_type_mapping.py
└── examples/
    ├── basic_migration.py
    └── config_examples/
        ├── mysql_to_pg.yaml
        └── pg_to_mysql.yaml
```

## 核心文件内容

### 1. requirements.txt
```
# 数据库驱动
mysql-connector-python>=8.0.0
psycopg2-binary>=2.9.0
cx-Oracle>=8.0.0
pyodbc>=4.0.0
pymongo>=4.0.0

# 工具库
click>=8.0.0
PyYAML>=6.0
rich>=10.0.0
tqdm>=4.60.0
pandas>=1.3.0
sqlalchemy>=1.4.0

# 开发工具
pytest>=6.0.0
black>=21.0
flake8>=3.9.0
mypy>=0.900
```

### 2. setup.py
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="db-migrator",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A universal database migration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/db-migrator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "psycopg2-binary>=2.9.0",
        "click>=8.0.0",
        "PyYAML>=6.0",
        "rich>=10.0.0",
        "tqdm>=4.60.0",
    ],
    entry_points={
        "console_scripts": [
            "db-migrate=db_migrator.cli.commands:cli",
        ],
    },
)
```

### 3. config/config.yaml
```yaml
# 数据库迁移配置文件示例
migration:
  # 源数据库配置
  source:
    type: mysql  # mysql, postgresql, oracle, sqlserver, sqlite, mongodb
    host: 127.0.0.1
    port: 3306
    username: root
    password: password
    database: source_db
    options:
      charset: utf8mb4
      auth_plugin: caching_sha2_password

  # 目标数据库配置
  target:
    type: postgresql
    host: 127.0.0.1
    port: 5432
    username: postgres
    password: password
    database: target_db
    options:
      sslmode: disable

  # 迁移选项
  options:
    # 要迁移的表（留空表示所有表）
    tables:
      - users
      - orders
      - products
    
    # 要排除的表
    exclude_tables:
      - temp_table
      - log_table
    
    # 批处理大小
    batch_size: 1000
    
    # 并发数
    workers: 4
    
    # 是否删除目标表
    drop_target: true
    
    # 是否迁移索引
    migrate_indexes: true
    
    # 是否迁移外键
    migrate_foreign_keys: true
    
    # 是否迁移触发器
    migrate_triggers: false
    
    # 是否迁移存储过程
    migrate_procedures: false
    
    # 数据过滤条件
    where_clauses:
      users: "created_at > '2023-01-01'"
      orders: "status != 'cancelled'"

  # 类型映射覆盖
  type_mappings:
    # MySQL to PostgreSQL
    mysql_to_postgresql:
      tinyint: smallint
      datetime: timestamp
      enum: varchar(255)
    
    # PostgreSQL to MySQL
    postgresql_to_mysql:
      serial: int auto_increment
      text: longtext
      json: json

  # 日志配置
  logging:
    level: INFO  # DEBUG, INFO, WARNING, ERROR
    file: migration.log
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 4. 使用示例

#### 命令行使用
```bash
# 使用配置文件
db-migrate --config config.yaml

# 交互式迁移
db-migrate interactive

# 指定源和目标
db-migrate --source mysql://user:pass@host/db --target postgresql://user:pass@host/db

# 只迁移特定表
db-migrate --config config.yaml --tables users,orders,products

# 生成迁移报告
db-migrate --config config.yaml --dry-run --report migration_report.html

# 从备份恢复
db-migrate restore --backup migration_backup_20231201.sql
```

#### Python API 使用
```python
from db_migrator import DatabaseMigrator

# 创建迁移器
migrator = DatabaseMigrator(
    source_config={
        'type': 'mysql',
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'source_db'
    },
    target_config={
        'type': 'postgresql',
        'host': 'localhost',
        'user': 'postgres',
        'password': 'password',
        'database': 'target_db'
    }
)

# 选择要迁移的表
migrator.select_tables(['users', 'orders', 'products'])

# 设置迁移选项
migrator.set_options(
    batch_size=5000,
    drop_target=True,
    migrate_indexes=True
)

# 执行迁移
result = migrator.migrate()

# 获取迁移报告
print(result.summary())
```

## 主要功能特性

### 1. 支持的数据库
- MySQL / MariaDB
- PostgreSQL
- Oracle
- SQL Server
- SQLite
- MongoDB (NoSQL to SQL)
- Redis (特定数据结构)

### 2. 核心功能
- **选择性迁移**: 可以选择特定的表、模式或数据库
- **数据类型映射**: 智能转换不同数据库之间的数据类型
- **序列/自增处理**: 自动处理 AUTO_INCREMENT、SERIAL 等
- **索引迁移**: 保留原有索引结构
- **外键约束**: 智能处理外键依赖关系
- **批量处理**: 支持大数据量的批量迁移
- **并行处理**: 多线程/多进程加速迁移
- **断点续传**: 支持中断后继续迁移
- **数据转换**: 支持自定义数据转换函数
- **进度显示**: 实时显示迁移进度
- **回滚功能**: 迁移失败时自动回滚

### 3. 高级功能
- **增量迁移**: 基于时间戳或标记的增量数据迁移
- **数据验证**: 迁移后的数据一致性验证
- **性能优化**: 自动优化迁移策略
- **迁移报告**: 生成详细的迁移报告
- **模式对比**: 比较源和目标数据库结构差异
- **自定义插件**: 支持编写自定义迁移插件

### 4. 配置管理
- YAML/JSON 配置文件
- 环境变量支持
- 配置模板生成
- 配置验证

### 5. 错误处理
- 详细的错误日志
- 自动重试机制
- 错误恢复策略
- 数据一致性保证

## 开发计划

### Phase 1: 基础框架 (1-2 周)
- [ ] 搭建项目结构
- [ ] 实现基础连接器接口
- [ ] 实现 MySQL 和 PostgreSQL 连接器
- [ ] 基础类型映射系统
- [ ] 简单的表结构迁移

### Phase 2: 核心功能 (2-3 周)
- [ ] 数据迁移功能
- [ ] 索引和约束迁移
- [ ] 批量处理优化
- [ ] 进度显示系统
- [ ] 基础 CLI 接口

### Phase 3: 高级功能 (2-3 周)
- [ ] 并行处理
- [ ] 断点续传
- [ ] 增量迁移
- [ ] 数据验证
- [ ] 迁移报告生成

### Phase 4: 扩展支持 (3-4 周)
- [ ] 更多数据库支持
- [ ] 插件系统
- [ ] Web UI
- [ ] API 服务
- [ ] 文档完善

## 技术架构

### 1. 核心设计模式
- **策略模式**: 不同数据库迁移策略
- **工厂模式**: 创建不同的连接器和迁移器
- **适配器模式**: 统一不同数据库的接口
- **观察者模式**: 进度通知和日志系统

### 2. 模块化设计
- 连接器层: 处理数据库连接和基础操作
- 迁移器层: 实现具体的迁移逻辑
- 映射器层: 处理数据类型和结构映射
- 工具层: 提供通用工具函数

### 3. 扩展机制
- 插件接口定义
- 自定义转换器
- 钩子函数支持
- 中间件机制

## 使用场景

1. **数据库升级迁移**
   - 从 MySQL 5.7 迁移到 MySQL 8.0
   - 从 PostgreSQL 12 迁移到 PostgreSQL 15

2. **跨数据库迁移**
   - MySQL 到 PostgreSQL
   - Oracle 到 MySQL
   - SQL Server 到 PostgreSQL

3. **数据同步**
   - 生产环境到测试环境
   - 主从数据库同步
   - 多区域数据复制

4. **数据归档**
   - 历史数据迁移
   - 冷热数据分离
   - 数据备份恢复

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License