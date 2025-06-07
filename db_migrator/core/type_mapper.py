"""
core/type_mapper.py - 数据类型映射系统
处理不同数据库之间的数据类型转换
"""

from typing import Dict, Optional, Tuple, Any
import re


class TypeMapper:
    """数据类型映射器"""

    def __init__(self):
        # 定义类型映射规则
        self.type_mappings = {
            # MySQL to PostgreSQL
            ('mysql', 'postgresql'): {
                # 整数类型
                'tinyint': 'smallint',
                'smallint': 'smallint',
                'mediumint': 'integer',
                'int': 'integer',
                'integer': 'integer',
                'bigint': 'bigint',

                # 浮点类型
                'float': 'real',
                'double': 'double precision',
                'decimal': 'decimal',
                'numeric': 'numeric',

                # 字符串类型
                'varchar': 'varchar',
                'char': 'char',
                'text': 'text',
                'tinytext': 'text',
                'mediumtext': 'text',
                'longtext': 'text',

                # 日期时间类型
                'datetime': 'timestamp',
                'timestamp': 'timestamp',
                'date': 'date',
                'time': 'time',
                'year': 'integer',

                # 二进制类型
                'blob': 'bytea',
                'tinyblob': 'bytea',
                'mediumblob': 'bytea',
                'longblob': 'bytea',
                'binary': 'bytea',
                'varbinary': 'bytea',

                # 其他类型
                'boolean': 'boolean',
                'bool': 'boolean',
                'json': 'json',
                'enum': 'varchar(255)',
                'set': 'varchar(255)',
            },

            # PostgreSQL to MySQL
            ('postgresql', 'mysql'): {
                # 整数类型
                'smallint': 'smallint',
                'integer': 'int',
                'bigint': 'bigint',
                'serial': 'int auto_increment',
                'bigserial': 'bigint auto_increment',

                # 浮点类型
                'real': 'float',
                'double precision': 'double',
                'decimal': 'decimal',
                'numeric': 'decimal',

                # 字符串类型
                'varchar': 'varchar',
                'char': 'char',
                'text': 'text',

                # 日期时间类型
                'timestamp': 'datetime',
                'timestamptz': 'datetime',
                'date': 'date',
                'time': 'time',
                'timetz': 'time',
                'interval': 'varchar(100)',

                # 二进制类型
                'bytea': 'longblob',

                # 其他类型
                'boolean': 'tinyint(1)',
                'json': 'json',
                'jsonb': 'json',
                'uuid': 'varchar(36)',
                'xml': 'text',
                'money': 'decimal(19,2)',
            },

            # MySQL to Oracle
            ('mysql', 'oracle'): {
                # 整数类型
                'tinyint': 'number(3)',
                'smallint': 'number(5)',
                'mediumint': 'number(7)',
                'int': 'number(10)',
                'integer': 'number(10)',
                'bigint': 'number(19)',

                # 浮点类型
                'float': 'binary_float',
                'double': 'binary_double',
                'decimal': 'number',
                'numeric': 'number',

                # 字符串类型
                'varchar': 'varchar2',
                'char': 'char',
                'text': 'clob',
                'tinytext': 'varchar2(255)',
                'mediumtext': 'clob',
                'longtext': 'clob',

                # 日期时间类型
                'datetime': 'timestamp',
                'timestamp': 'timestamp',
                'date': 'date',
                'time': 'varchar2(8)',
                'year': 'number(4)',

                # 二进制类型
                'blob': 'blob',
                'tinyblob': 'raw(255)',
                'mediumblob': 'blob',
                'longblob': 'blob',

                # 其他类型
                'boolean': 'number(1)',
                'json': 'clob',
                'enum': 'varchar2(255)',
            },

            # Oracle to MySQL
            ('oracle', 'mysql'): {
                # 数字类型
                'number': 'decimal',
                'binary_float': 'float',
                'binary_double': 'double',

                # 字符串类型
                'varchar2': 'varchar',
                'nvarchar2': 'varchar',
                'char': 'char',
                'nchar': 'char',
                'clob': 'longtext',
                'nclob': 'longtext',

                # 日期时间类型
                'date': 'datetime',
                'timestamp': 'timestamp',

                # 二进制类型
                'blob': 'longblob',
                'raw': 'varbinary',
                'long raw': 'longblob',

                # 其他类型
                'rowid': 'varchar(18)',
                'urowid': 'varchar(4000)',
            },

            # MySQL to SQL Server
            ('mysql', 'sqlserver'): {
                # 整数类型
                'tinyint': 'tinyint',
                'smallint': 'smallint',
                'mediumint': 'int',
                'int': 'int',
                'integer': 'int',
                'bigint': 'bigint',

                # 浮点类型
                'float': 'float',
                'double': 'float',
                'decimal': 'decimal',
                'numeric': 'numeric',

                # 字符串类型
                'varchar': 'nvarchar',
                'char': 'nchar',
                'text': 'nvarchar(max)',
                'tinytext': 'nvarchar(255)',
                'mediumtext': 'nvarchar(max)',
                'longtext': 'nvarchar(max)',

                # 日期时间类型
                'datetime': 'datetime2',
                'timestamp': 'datetime2',
                'date': 'date',
                'time': 'time',
                'year': 'int',

                # 二进制类型
                'blob': 'varbinary(max)',
                'tinyblob': 'varbinary(255)',
                'mediumblob': 'varbinary(max)',
                'longblob': 'varbinary(max)',

                # 其他类型
                'boolean': 'bit',
                'json': 'nvarchar(max)',
                'enum': 'nvarchar(255)',
            },
        }

        # 特殊处理规则
        self.special_rules = {
            # AUTO_INCREMENT 处理
            'auto_increment': {
                'mysql': 'auto_increment',
                'postgresql': 'serial',
                'oracle': 'generated always as identity',
                'sqlserver': 'identity(1,1)',
            },

            # CURRENT_TIMESTAMP 处理
            'current_timestamp': {
                'mysql': 'current_timestamp',
                'postgresql': 'current_timestamp',
                'oracle': 'systimestamp',
                'sqlserver': 'getdate()',
            }
        }

    def map_type(self, source_type: str, source_db: str, target_db: str,
                 length: Optional[int] = None, precision: Optional[int] = None,
                 scale: Optional[int] = None) -> str:
        """
        映射数据类型

        Args:
            source_type: 源数据类型
            source_db: 源数据库类型
            target_db: 目标数据库类型
            length: 长度
            precision: 精度
            scale: 小数位数

        Returns:
            目标数据类型
        """
        # 标准化类型名称
        source_type = source_type.lower().strip()

        # 获取映射表
        mapping_key = (source_db.lower(), target_db.lower())
        mapping = self.type_mappings.get(mapping_key, {})

        # 提取基本类型（去除长度等信息）
        base_type = self._extract_base_type(source_type)

        # 查找映射
        target_type = mapping.get(base_type, source_type)

        # 处理带长度的类型
        if target_type in ['varchar', 'char', 'nvarchar', 'nchar', 'varchar2']:
            if length:
                target_type = f"{target_type}({length})"
        elif target_type in ['decimal', 'numeric', 'number']:
            if precision and scale:
                target_type = f"{target_type}({precision},{scale})"
            elif precision:
                target_type = f"{target_type}({precision})"

        return target_type

    def map_column(self, column_info: Dict[str, Any], source_db: str,
                   target_db: str) -> Dict[str, Any]:
        """
        映射列定义

        Args:
            column_info: 列信息
            source_db: 源数据库类型
            target_db: 目标数据库类型

        Returns:
            映射后的列定义
        """
        # 映射数据类型
        target_type = self.map_type(
            column_info['data_type'],
            source_db,
            target_db,
            column_info.get('max_length'),
            column_info.get('numeric_precision'),
            column_info.get('numeric_scale')
        )

        # 构建列定义
        column_def = {
            'name': column_info['name'],
            'type': target_type,
            'nullable': column_info.get('is_nullable', True),
            'default': self._map_default_value(
                column_info.get('default_value'),
                source_db,
                target_db
            )
        }

        # 处理自增
        if column_info.get('is_auto_increment'):
            column_def['auto_increment'] = True

        # 处理主键
        if column_info.get('is_primary_key'):
            column_def['primary_key'] = True

        # 处理唯一约束
        if column_info.get('is_unique'):
            column_def['unique'] = True

        return column_def

    def generate_create_table_sql(self, table_name: str, columns: list,
                                  target_db: str) -> str:
        """
        生成创建表的 SQL 语句

        Args:
            table_name: 表名
            columns: 列定义列表
            target_db: 目标数据库类型

        Returns:
            CREATE TABLE SQL 语句
        """
        if target_db.lower() == 'mysql':
            return self._generate_mysql_create_table(table_name, columns)
        elif target_db.lower() == 'postgresql':
            return self._generate_postgresql_create_table(table_name, columns)
        elif target_db.lower() == 'oracle':
            return self._generate_oracle_create_table(table_name, columns)
        elif target_db.lower() == 'sqlserver':
            return self._generate_sqlserver_create_table(table_name, columns)
        else:
            raise ValueError(f"Unsupported database type: {target_db}")

    def _extract_base_type(self, type_str: str) -> str:
        """提取基本类型名称"""
        # 移除括号内的内容
        base = re.sub(r'\([^)]*\)', '', type_str)
        # 移除 unsigned 等修饰符
        base = re.sub(r'\s+(unsigned|signed|zerofill)', '', base)
        return base.strip().lower()

    def _map_default_value(self, default_value: Any, source_db: str,
                           target_db: str) -> Any:
        """映射默认值"""
        if default_value is None:
            return None

        # 处理特殊默认值
        default_str = str(default_value).lower()

        # CURRENT_TIMESTAMP
        if 'current_timestamp' in default_str or 'now()' in default_str:
            return self.special_rules['current_timestamp'].get(target_db, default_value)

        # NULL
        if default_str == 'null':
            return None

        # 布尔值
        if default_str in ('true', 'false'):
            if target_db == 'mysql':
                return '1' if default_str == 'true' else '0'
            elif target_db == 'postgresql':
                return 'TRUE' if default_str == 'true' else 'FALSE'

        return default_value

    def _generate_mysql_create_table(self, table_name: str, columns: list) -> str:
        """生成 MySQL CREATE TABLE 语句"""
        sql = f"CREATE TABLE `{table_name}` (\n"

        column_defs = []
        primary_keys = []

        for col in columns:
            col_def = f"  `{col['name']}` {col['type']}"

            # 处理自增
            if col.get('auto_increment'):
                col_def = col_def.replace('int', 'INT').replace('bigint', 'BIGINT')
                col_def += ' AUTO_INCREMENT'

            # 处理 NULL
            if not col.get('nullable', True):
                col_def += ' NOT NULL'

            # 处理默认值
            if col.get('default') is not None:
                col_def += f" DEFAULT {col['default']}"

            column_defs.append(col_def)

            # 记录主键
            if col.get('primary_key'):
                primary_keys.append(f"`{col['name']}`")

        sql += ',\n'.join(column_defs)

        # 添加主键
        if primary_keys:
            sql += f",\n  PRIMARY KEY ({', '.join(primary_keys)})"

        sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"

        return sql

    def _generate_postgresql_create_table(self, table_name: str, columns: list) -> str:
        """生成 PostgreSQL CREATE TABLE 语句"""
        sql = f'CREATE TABLE "{table_name}" (\n'

        column_defs = []
        primary_keys = []

        for col in columns:
            # 处理自增
            if col.get('auto_increment'):
                if 'int' in col['type'].lower():
                    col['type'] = 'SERIAL' if 'big' not in col['type'].lower() else 'BIGSERIAL'

            col_def = f'  "{col["name"]}" {col["type"]}'

            # 处理 NULL
            if not col.get('nullable', True):
                col_def += ' NOT NULL'

            # 处理默认值
            if col.get('default') is not None and not col.get('auto_increment'):
                col_def += f" DEFAULT {col['default']}"

            # 处理唯一约束
            if col.get('unique') and not col.get('primary_key'):
                col_def += ' UNIQUE'

            column_defs.append(col_def)

            # 记录主键
            if col.get('primary_key'):
                primary_keys.append(f'"{col["name"]}"')

        sql += ',\n'.join(column_defs)

        # 添加主键
        if primary_keys:
            sql += f",\n  PRIMARY KEY ({', '.join(primary_keys)})"

        sql += "\n);"

        return sql

    def _generate_oracle_create_table(self, table_name: str, columns: list) -> str:
        """生成 Oracle CREATE TABLE 语句"""
        sql = f'CREATE TABLE "{table_name.upper()}" (\n'

        column_defs = []
        primary_keys = []

        for col in columns:
            col_def = f'  "{col["name"].upper()}" {col["type"].upper()}'

            # 处理自增
            if col.get('auto_increment'):
                col_def += ' GENERATED ALWAYS AS IDENTITY'

            # 处理 NULL
            if not col.get('nullable', True):
                col_def += ' NOT NULL'

            # 处理默认值
            if col.get('default') is not None and not col.get('auto_increment'):
                col_def += f" DEFAULT {col['default']}"

            column_defs.append(col_def)

            # 记录主键
            if col.get('primary_key'):
                primary_keys.append(f'"{col["name"].upper()}"')

        sql += ',\n'.join(column_defs)

        # 添加主键
        if primary_keys:
            sql += f",\n  CONSTRAINT PK_{table_name.upper()} PRIMARY KEY ({', '.join(primary_keys)})"

        sql += "\n);"

        return sql

    def _generate_sqlserver_create_table(self, table_name: str, columns: list) -> str:
        """生成 SQL Server CREATE TABLE 语句"""
        sql = f"CREATE TABLE [{table_name}] (\n"

        column_defs = []
        primary_keys = []

        for col in columns:
            col_def = f"  [{col['name']}] {col['type']}"

            # 处理自增
            if col.get('auto_increment'):
                col_def += ' IDENTITY(1,1)'

            # 处理 NULL
            if not col.get('nullable', True):
                col_def += ' NOT NULL'
            else:
                col_def += ' NULL'

            # 处理默认值
            if col.get('default') is not None and not col.get('auto_increment'):
                col_def += f" DEFAULT {col['default']}"

            column_defs.append(col_def)

            # 记录主键
            if col.get('primary_key'):
                primary_keys.append(f"[{col['name']}]")

        sql += ',\n'.join(column_defs)

        # 添加主键
        if primary_keys:
            sql += f",\n  CONSTRAINT PK_{table_name} PRIMARY KEY ({', '.join(primary_keys)})"

        sql += "\n);"

        return sql