#!/usr/bin/env python3
"""
PostgreSQL Database Connector
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Any, Optional, Tuple
from ..core.base_connector import BaseConnector, TableInfo, ColumnInfo


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL数据库连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化PostgreSQL连接器
        
        Args:
            config: 数据库配置信息
        """
        super().__init__(config)
        self.connection = None
        
    def connect(self) -> bool:
        """
        连接到PostgreSQL数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config.get('port', 5432),
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                **self.config.get('options', {})
            )
            self.connection.autocommit = False
            logging.info(f"成功连接到PostgreSQL数据库: {self.config['database']}")
            return True
        except Exception as e:
            logging.error(f"连接PostgreSQL数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("PostgreSQL数据库连接已断开")
    
    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, (schema or 'public',))
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        except Exception as e:
            logging.error(f"获取表列表失败: {e}")
            return []
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict]: 列信息列表
        """
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default,
                        ordinal_position
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'Field': row['column_name'],
                        'Type': self._format_pg_type(row),
                        'Null': 'YES' if row['is_nullable'] == 'YES' else 'NO',
                        'Key': '',  # 需要另外查询
                        'Default': row['column_default'],
                        'Extra': ''
                    })
                
                # 获取主键信息
                self._add_key_info(cursor, table_name, columns)
                
                return columns
        except Exception as e:
            logging.error(f"获取表结构失败: {e}")
            return []
    
    def get_indexes(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表的索引信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict]: 索引信息列表
        """
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        i.relname as index_name,
                        ix.indisunique as is_unique,
                        ix.indisprimary as is_primary,
                        a.attname as column_name,
                        ix.indkey
                    FROM 
                        pg_class t,
                        pg_class i,
                        pg_index ix,
                        pg_attribute a
                    WHERE 
                        t.oid = ix.indrelid
                        AND i.oid = ix.indexrelid
                        AND a.attrelid = t.oid
                        AND a.attnum = ANY(ix.indkey)
                        AND t.relkind = 'r'
                        AND t.relname = %s
                    ORDER BY i.relname, a.attnum
                """, (table_name,))
                
                indexes = []
                for row in cursor.fetchall():
                    indexes.append({
                        'Key_name': row['index_name'],
                        'Non_unique': 0 if row['is_unique'] else 1,
                        'Column_name': row['column_name']
                    })
                
                return indexes
        except Exception as e:
            logging.error(f"获取索引信息失败: {e}")
            return []
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict]: 查询结果
        """
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except Exception as e:
            logging.error(f"执行查询失败: {e}")
            return []
    
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """
        执行SQL命令
        
        Args:
            command: SQL命令
            params: 命令参数
            
        Returns:
            int: 受影响的行数
        """
        if not self.connection:
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(command, params)
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            logging.error(f"执行命令失败: {e}")
            self.connection.rollback()
            return 0
    
    def get_table_count(self, table_name: str, where_clause: str = "") -> int:
        """
        获取表的行数
        
        Args:
            table_name: 表名
            where_clause: WHERE条件
            
        Returns:
            int: 行数
        """
        if not self.connection:
            return 0
        
        try:
            query = f'SELECT COUNT(*) FROM "{table_name}"'
            if where_clause:
                query += f" WHERE {where_clause}"
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"获取表行数失败: {e}")
            return 0
    
    def get_table_data(
        self, 
        table_name: str, 
        batch_size: int = 1000, 
        offset: int = 0, 
        where_clause: str = ""
    ) -> List[Tuple]:
        """
        获取表数据
        
        Args:
            table_name: 表名
            batch_size: 批处理大小
            offset: 偏移量
            where_clause: WHERE条件
            
        Returns:
            List[Tuple]: 数据行列表
        """
        if not self.connection:
            return []
        
        try:
            query = f'SELECT * FROM "{table_name}"'
            if where_clause:
                query += f" WHERE {where_clause}"
            query += f" LIMIT {batch_size} OFFSET {offset}"
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"获取表数据失败: {e}")
            return []
    
    def insert_data(self, table_name: str, columns: List[str], data: List[Tuple]) -> bool:
        """
        插入数据
        
        Args:
            table_name: 表名
            columns: 列名列表
            data: 数据列表
            
        Returns:
            bool: 插入是否成功
        """
        if not self.connection or not data:
            return False
        
        try:
            placeholders = ','.join(['%s'] * len(columns))
            column_names = ','.join([f'"{col}"' for col in columns])
            query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
            
            with self.connection.cursor() as cursor:
                cursor.executemany(query, data)
                self.connection.commit()
                return True
        except Exception as e:
            logging.error(f"插入数据失败: {e}")
            self.connection.rollback()
            return False
    
    def create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            columns: 列定义列表
            
        Returns:
            bool: 创建是否成功
        """
        if not self.connection:
            return False
        
        try:
            # 删除表（如果存在）
            drop_sql = f'DROP TABLE IF EXISTS "{table_name}" CASCADE'
            
            # 构建CREATE TABLE语句
            column_defs = []
            primary_keys = []
            
            for col in columns:
                col_name = col['Field']
                col_type = col['Type']
                
                # 处理 AUTO_INCREMENT -> SERIAL
                if 'auto_increment' in col.get('Extra', ''):
                    if 'int' in col_type.lower():
                        col_type = 'SERIAL'
                    else:
                        col_type = 'BIGSERIAL'
                
                col_def = f'"{col_name}" {col_type}'
                
                # 处理 NULL/NOT NULL
                if col['Null'] == 'NO' and 'auto_increment' not in col.get('Extra', ''):
                    col_def += ' NOT NULL'
                
                # 处理默认值
                if col['Default'] is not None and 'auto_increment' not in col.get('Extra', ''):
                    if col['Default'] == 'CURRENT_TIMESTAMP':
                        col_def += ' DEFAULT CURRENT_TIMESTAMP'
                    else:
                        col_def += f" DEFAULT '{col['Default']}'"
                
                column_defs.append(col_def)
                
                # 记录主键
                if col['Key'] == 'PRI':
                    primary_keys.append(col_name)
            
            create_sql = f'CREATE TABLE "{table_name}" (\n'
            create_sql += ',\n'.join(f'  {col}' for col in column_defs)
            
            if primary_keys:
                pk_list = ', '.join([f'"{pk}"' for pk in primary_keys])
                create_sql += f',\n  PRIMARY KEY ({pk_list})'
            
            create_sql += '\n)'
            
            with self.connection.cursor() as cursor:
                cursor.execute(drop_sql)
                cursor.execute(create_sql)
                self.connection.commit()
                return True
        except Exception as e:
            logging.error(f"创建表失败: {e}")
            self.connection.rollback()
            return False

    # 新增的抽象方法实现
    def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """获取表的详细信息"""
        columns = self.get_columns(table_name, schema)
        primary_keys = self.get_primary_keys(table_name, schema)
        indexes = self.get_indexes(table_name, schema)
        foreign_keys = self.get_foreign_keys(table_name, schema)
        row_count = self.get_row_count(table_name, schema)
        
        return TableInfo(
            name=table_name,
            columns=[col.__dict__ for col in columns],
            primary_keys=primary_keys,
            indexes=indexes,
            foreign_keys=foreign_keys,
            row_count=row_count
        )

    def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """获取表的列信息"""
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = %s
                    ORDER BY ordinal_position
                """, (table_name, schema or 'public'))
                
                columns = []
                primary_keys = self.get_primary_keys(table_name, schema)
                
                for row in cursor.fetchall():
                    columns.append(ColumnInfo(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == 'YES',
                        default_value=row[3],
                        is_primary_key=row[0] in primary_keys,
                        is_unique=False,  # 需要单独查询
                        is_auto_increment='nextval' in (row[3] or ''),
                        max_length=row[4],
                        numeric_precision=row[5],
                        numeric_scale=row[6]
                    ))
                
                return columns
        except Exception as e:
            logging.error(f"获取列信息失败: {e}")
            return []

    def get_primary_keys(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """获取表的主键列"""
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.attname
                    FROM pg_constraint c
                    JOIN pg_attribute a ON a.attnum = ANY(c.conkey)
                    JOIN pg_class t ON t.oid = c.conrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE c.contype = 'p'
                    AND t.relname = %s
                    AND n.nspname = %s
                """, (table_name, schema or 'public'))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"获取主键信息失败: {e}")
            return []

    def get_foreign_keys(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表的外键信息"""
        if not self.connection:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = %s
                        AND tc.table_schema = %s
                """, (table_name, schema or 'public'))
                
                foreign_keys = []
                for row in cursor.fetchall():
                    foreign_keys.append({
                        'constraint_name': row[0],
                        'column_name': row[1],
                        'foreign_table_name': row[2],
                        'foreign_column_name': row[3]
                    })
                
                return foreign_keys
        except Exception as e:
            logging.error(f"获取外键信息失败: {e}")
            return []

    def get_table_ddl(self, table_name: str, schema: Optional[str] = None) -> str:
        """获取创建表的 DDL 语句"""
        # PostgreSQL 没有直接的方式获取DDL，需要构建
        columns = self.get_columns(table_name, schema)
        ddl = f'CREATE TABLE "{table_name}" (\n'
        
        column_defs = []
        for col in columns:
            col_def = f'  "{col.name}" {col.data_type}'
            if col.max_length:
                col_def += f'({col.max_length})'
            if not col.is_nullable:
                col_def += ' NOT NULL'
            if col.default_value:
                col_def += f' DEFAULT {col.default_value}'
            column_defs.append(col_def)
        
        ddl += ',\n'.join(column_defs)
        
        primary_keys = self.get_primary_keys(table_name, schema)
        if primary_keys:
            pk_list = ', '.join([f'"{pk}"' for pk in primary_keys])
            ddl += f',\n  PRIMARY KEY ({pk_list})'
        
        ddl += '\n);'
        return ddl

    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]], 
                    schema: Optional[str] = None, batch_size: int = 1000) -> int:
        """批量插入数据"""
        if not data:
            return 0
        
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]
        
        total_inserted = 0
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            if self.insert_data(table_name, columns, batch):
                total_inserted += len(batch)
        
        return total_inserted

    def stream_query(self, query: str, params: Optional[Tuple] = None, batch_size: int = 1000):
        """流式查询数据"""
        if not self.connection:
            return
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    yield rows
        except Exception as e:
            logging.error(f"流式查询失败: {e}")

    def get_row_count(self, table_name: str, schema: Optional[str] = None, 
                     where_clause: Optional[str] = None) -> int:
        """获取表的行数"""
        return self.get_table_count(table_name, where_clause or "")

    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """检查表是否存在"""
        if not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    )
                """, (schema or 'public', table_name))
                
                return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"检查表存在性失败: {e}")
            return False

    def drop_table(self, table_name: str, schema: Optional[str] = None, cascade: bool = False) -> None:
        """删除表"""
        if not self.connection:
            return
        
        try:
            cascade_clause = ' CASCADE' if cascade else ''
            with self.connection.cursor() as cursor:
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"{cascade_clause}')
                self.connection.commit()
        except Exception as e:
            logging.error(f"删除表失败: {e}")
            self.connection.rollback()

    def begin_transaction(self) -> None:
        """开始事务"""
        if self.connection:
            self.connection.autocommit = False

    def commit_transaction(self) -> None:
        """提交事务"""
        if self.connection:
            self.connection.commit()

    def rollback_transaction(self) -> None:
        """回滚事务"""
        if self.connection:
            self.connection.rollback()
    
    def _format_pg_type(self, row: Dict[str, Any]) -> str:
        """格式化PostgreSQL数据类型"""
        data_type = row['data_type']
        
        if data_type in ['character varying', 'varchar']:
            if row['character_maximum_length']:
                return f"varchar({row['character_maximum_length']})"
            return 'varchar'
        elif data_type in ['character', 'char']:
            if row['character_maximum_length']:
                return f"char({row['character_maximum_length']})"
            return 'char'
        elif data_type == 'numeric':
            if row['numeric_precision'] and row['numeric_scale']:
                return f"decimal({row['numeric_precision']},{row['numeric_scale']})"
            return 'decimal'
        else:
            return data_type
    
    def _add_key_info(self, cursor, table_name: str, columns: List[Dict[str, Any]]):
        """添加主键信息"""
        try:
            cursor.execute("""
                SELECT a.attname
                FROM pg_constraint c
                JOIN pg_attribute a ON a.attnum = ANY(c.conkey)
                WHERE c.conrelid = %s::regclass
                AND c.contype = 'p'
            """, (table_name,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            for col in columns:
                if col['Field'] in primary_keys:
                    col['Key'] = 'PRI'
        except Exception as e:
            logging.warning(f"获取主键信息失败: {e}")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if self.connect():
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                self.disconnect()
                return True
        except Exception as e:
            logging.error(f"连接测试失败: {e}")
        return False 