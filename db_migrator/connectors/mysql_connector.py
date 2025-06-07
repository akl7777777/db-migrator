"""
mysql_connector.py - MySQL 数据库连接器实现
"""

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
import logging
from ..core.base_connector import BaseConnector, TableInfo, ColumnInfo


class MySQLConnector(BaseConnector):
    """MySQL 数据库连接器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection_params = {
            'host': config.get('host', 'localhost'),
            'port': config.get('port', 3306),
            'user': config.get('user') or config.get('username'),
            'password': config.get('password'),
            'database': config.get('database'),
        }

        # 处理额外的连接选项
        options = config.get('options', {})
        if 'charset' in options:
            self.connection_params['charset'] = options['charset']
        if 'auth_plugin' in options:
            self.connection_params['auth_plugin'] = options['auth_plugin']

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(**self.connection_params)
            self.logger.info(f"Connected to MySQL database: {self.config.get('database')}")
            return True
        except Error as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            return False

    def disconnect(self) -> None:
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("Disconnected from MySQL database")

    def test_connection(self) -> bool:
        """测试数据库连接是否正常"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Error:
            return False

    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """获取所有表名"""
        cursor = self.connection.cursor()
        try:
            if schema:
                cursor.execute(
                    "SELECT TABLE_NAME FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
                    (schema,)
                )
            else:
                cursor.execute("SHOW TABLES")

            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """获取表的列信息"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY,
                EXTRA,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_NAME = %s
            """
            params = [table_name]

            if schema:
                query += " AND TABLE_SCHEMA = %s"
                params.append(schema)
            else:
                query += " AND TABLE_SCHEMA = DATABASE()"

            query += " ORDER BY ORDINAL_POSITION"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = []
            for row in rows:
                column = ColumnInfo(
                    name=row['COLUMN_NAME'],
                    data_type=row['DATA_TYPE'],
                    is_nullable=row['IS_NULLABLE'] == 'YES',
                    default_value=row['COLUMN_DEFAULT'],
                    is_primary_key=row['COLUMN_KEY'] == 'PRI',
                    is_unique=row['COLUMN_KEY'] in ('PRI', 'UNI'),
                    is_auto_increment='auto_increment' in row.get('EXTRA', ''),
                    max_length=row['CHARACTER_MAXIMUM_LENGTH'],
                    numeric_precision=row['NUMERIC_PRECISION'],
                    numeric_scale=row['NUMERIC_SCALE'],
                    comment=row['COLUMN_COMMENT']
                )
                columns.append(column)

            return columns
        finally:
            cursor.close()

    def get_primary_keys(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """获取表的主键列"""
        cursor = self.connection.cursor()
        try:
            query = """
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
            """
            params = [table_name]

            if schema:
                query += " AND TABLE_SCHEMA = %s"
                params.append(schema)
            else:
                query += " AND TABLE_SCHEMA = DATABASE()"

            query += " ORDER BY ORDINAL_POSITION"

            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_indexes(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表的索引信息"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            rows = cursor.fetchall()

            # 按索引名分组
            indexes = {}
            for row in rows:
                index_name = row['Key_name']
                if index_name not in indexes:
                    indexes[index_name] = {
                        'name': index_name,
                        'is_unique': row['Non_unique'] == 0,
                        'is_primary': index_name == 'PRIMARY',
                        'columns': [],
                        'type': row.get('Index_type', 'BTREE')
                    }
                indexes[index_name]['columns'].append({
                    'name': row['Column_name'],
                    'order': row['Seq_in_index'],
                    'direction': 'ASC' if row.get('Collation') == 'A' else 'DESC'
                })

            # 对每个索引的列按顺序排序
            for index in indexes.values():
                index['columns'].sort(key=lambda x: x['order'])

            return list(indexes.values())
        finally:
            cursor.close()

    def get_foreign_keys(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表的外键信息"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
            SELECT 
                kcu.CONSTRAINT_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_SCHEMA,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME,
                rc.UPDATE_RULE,
                rc.DELETE_RULE
            FROM information_schema.KEY_COLUMN_USAGE kcu
            JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.TABLE_NAME = %s
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """
            params = [table_name]

            if schema:
                query += " AND kcu.TABLE_SCHEMA = %s"
                params.append(schema)
            else:
                query += " AND kcu.TABLE_SCHEMA = DATABASE()"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # 按外键名分组
            foreign_keys = {}
            for row in rows:
                fk_name = row['CONSTRAINT_NAME']
                if fk_name not in foreign_keys:
                    foreign_keys[fk_name] = {
                        'name': fk_name,
                        'columns': [],
                        'referenced_table': row['REFERENCED_TABLE_NAME'],
                        'referenced_schema': row['REFERENCED_TABLE_SCHEMA'],
                        'referenced_columns': [],
                        'update_rule': row['UPDATE_RULE'],
                        'delete_rule': row['DELETE_RULE']
                    }
                foreign_keys[fk_name]['columns'].append(row['COLUMN_NAME'])
                foreign_keys[fk_name]['referenced_columns'].append(row['REFERENCED_COLUMN_NAME'])

            return list(foreign_keys.values())
        finally:
            cursor.close()

    def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """获取表的详细信息"""
        columns = self.get_columns(table_name, schema)
        primary_keys = self.get_primary_keys(table_name, schema)
        indexes = self.get_indexes(table_name, schema)
        foreign_keys = self.get_foreign_keys(table_name, schema)
        row_count = self.get_row_count(table_name, schema)

        # 获取表注释和大小
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
            SELECT TABLE_COMMENT, DATA_LENGTH + INDEX_LENGTH as SIZE_BYTES
            FROM information_schema.TABLES
            WHERE TABLE_NAME = %s
            """
            params = [table_name]

            if schema:
                query += " AND TABLE_SCHEMA = %s"
                params.append(schema)
            else:
                query += " AND TABLE_SCHEMA = DATABASE()"

            cursor.execute(query, params)
            result = cursor.fetchone()

            return TableInfo(
                name=table_name,
                columns=[{
                    'name': col.name,
                    'type': col.data_type,
                    'nullable': col.is_nullable,
                    'default': col.default_value,
                    'auto_increment': col.is_auto_increment
                } for col in columns],
                primary_keys=primary_keys,
                indexes=indexes,
                foreign_keys=foreign_keys,
                row_count=row_count,
                size_bytes=result['SIZE_BYTES'] if result else None,
                comment=result['TABLE_COMMENT'] if result else None
            )
        finally:
            cursor.close()

    def get_table_ddl(self, table_name: str, schema: Optional[str] = None) -> str:
        """获取创建表的 DDL 语句"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            result = cursor.fetchone()
            return result[1] if result else ""
        finally:
            cursor.close()

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """执行命令语句"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(command, params or ())
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]],
                   schema: Optional[str] = None, batch_size: int = 1000) -> int:
        """批量插入数据"""
        if not data:
            return 0

        cursor = self.connection.cursor()
        try:
            # 获取列名
            columns = list(data[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'`{col}`' for col in columns])

            # 构建插入语句
            table_ref = f"`{schema}`.`{table_name}`" if schema else f"`{table_name}`"
            insert_sql = f"INSERT INTO {table_ref} ({columns_str}) VALUES ({placeholders})"

            # 批量插入
            total_inserted = 0
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                values = [tuple(row[col] for col in columns) for row in batch]
                cursor.executemany(insert_sql, values)
                self.connection.commit()
                total_inserted += cursor.rowcount

            return total_inserted
        except Exception as e:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def stream_query(self, query: str, params: Optional[Tuple] = None,
                    batch_size: int = 1000):
        """流式查询"""
        cursor = self.connection.cursor(dictionary=True, buffered=False)
        try:
            cursor.execute(query, params or ())

            batch = []
            for row in cursor:
                batch.append(row)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch
        finally:
            cursor.close()

    def get_row_count(self, table_name: str, schema: Optional[str] = None,
                     where_clause: Optional[str] = None) -> int:
        """获取表的行数"""
        cursor = self.connection.cursor()
        try:
            table_ref = f"`{schema}`.`{table_name}`" if schema else f"`{table_name}`"
            query = f"SELECT COUNT(*) FROM {table_ref}"

            if where_clause:
                query += f" WHERE {where_clause}"

            cursor.execute(query)
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """检查表是否存在"""
        cursor = self.connection.cursor()
        try:
            query = """
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_NAME = %s
            """
            params = [table_name]

            if schema:
                query += " AND TABLE_SCHEMA = %s"
                params.append(schema)
            else:
                query += " AND TABLE_SCHEMA = DATABASE()"

            cursor.execute(query, params)
            return cursor.fetchone()[0] > 0
        finally:
            cursor.close()

    def drop_table(self, table_name: str, schema: Optional[str] = None,
                  cascade: bool = False) -> None:
        """删除表"""
        cursor = self.connection.cursor()
        try:
            table_ref = f"`{schema}`.`{table_name}`" if schema else f"`{table_name}`"

            if cascade:
                # MySQL 不直接支持 CASCADE，需要先删除外键约束
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            cursor.execute(f"DROP TABLE IF EXISTS {table_ref}")

            if cascade:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            self.connection.commit()
        finally:
            cursor.close()

    def create_table(self, ddl: str) -> None:
        """创建表"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(ddl)
            self.connection.commit()
        finally:
            cursor.close()

    def begin_transaction(self) -> None:
        """开始事务"""
        self.connection.start_transaction()

    def commit_transaction(self) -> None:
        """提交事务"""
        self.connection.commit()

    def rollback_transaction(self) -> None:
        """回滚事务"""
        self.connection.rollback()

    def quote_identifier(self, identifier: str) -> str:
        """转义标识符"""
        return f"`{identifier}`"

    def get_type_mapping(self) -> Dict[str, str]:
        """获取到其他数据库的类型映射"""
        return {
            # 到 PostgreSQL 的映射
            'postgresql': {
                'tinyint': 'smallint',
                'smallint': 'smallint',
                'mediumint': 'integer',
                'int': 'integer',
                'bigint': 'bigint',
                'float': 'real',
                'double': 'double precision',
                'decimal': 'decimal',
                'varchar': 'varchar',
                'char': 'char',
                'text': 'text',
                'tinytext': 'text',
                'mediumtext': 'text',
                'longtext': 'text',
                'datetime': 'timestamp',
                'timestamp': 'timestamp',
                'date': 'date',
                'time': 'time',
                'year': 'integer',
                'boolean': 'boolean',
                'json': 'json',
                'enum': 'varchar(255)',
                'set': 'varchar(255)',
                'blob': 'bytea',
                'tinyblob': 'bytea',
                'mediumblob': 'bytea',
                'longblob': 'bytea',
            }
        }

    def get_table_count(self, table_name: str, where_clause: str = "") -> int:
        """获取表的行数"""
        cursor = self.connection.cursor()
        try:
            query = f"SELECT COUNT(*) FROM `{table_name}`"
            if where_clause:
                query += f" WHERE {where_clause}"
            cursor.execute(query)
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'Field': row[0],
                    'Type': row[1],
                    'Null': row[2],
                    'Key': row[3],
                    'Default': row[4],
                    'Extra': row[5]
                })
            return columns
        finally:
            cursor.close()

    def get_table_data(self, table_name: str, batch_size: int = 1000, offset: int = 0, where_clause: str = "") -> List[Tuple]:
        """获取表数据"""
        cursor = self.connection.cursor()
        try:
            query = f"SELECT * FROM `{table_name}`"
            if where_clause:
                query += f" WHERE {where_clause}"
            query += f" LIMIT {batch_size} OFFSET {offset}"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    def insert_data(self, table_name: str, columns: List[str], data: List[Tuple]) -> bool:
        """插入数据到表中"""
        if not data:
            return True
        
        cursor = self.connection.cursor()
        try:
            # 构建插入语句
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join([f'`{col}`' for col in columns])
            query = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
            
            # 批量插入
            cursor.executemany(query, data)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"插入数据失败: {e}")
            return False
        finally:
            cursor.close()