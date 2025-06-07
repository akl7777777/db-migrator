#!/usr/bin/env python3
"""
MySQL to PostgreSQL Migration Script
包含自动序列生成和数据类型转换
"""

import logging
import re
import sys
from typing import Dict, List, Any, Callable, Optional
from ..connectors.mysql_connector import MySQLConnector
from ..connectors.postgresql_connector import PostgreSQLConnector
from ..core.type_mapper import TypeMapper


class MySQLToPostgreSQLMigrator:
    """MySQL到PostgreSQL数据库迁移器"""
    
    def __init__(self, mysql_config: Dict[str, Any], pg_config: Dict[str, Any]):
        """
        初始化迁移器
        
        Args:
            mysql_config: MySQL数据库配置
            pg_config: PostgreSQL数据库配置
        """
        self.mysql_config = mysql_config
        self.pg_config = pg_config
        self.mysql_connector = MySQLConnector(mysql_config)
        self.pg_connector = PostgreSQLConnector(pg_config)
        self.type_mapper = TypeMapper()
        
        # 进度回调函数
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
        
        # 类型映射
        self.type_mapping = {
            'int': 'INTEGER',
            'tinyint': 'SMALLINT',
            'smallint': 'SMALLINT',
            'mediumint': 'INTEGER',
            'bigint': 'BIGINT',
            'float': 'REAL',
            'double': 'DOUBLE PRECISION',
            'decimal': 'DECIMAL',
            'varchar': 'VARCHAR',
            'char': 'CHAR',
            'text': 'TEXT',
            'tinytext': 'TEXT',
            'mediumtext': 'TEXT',
            'longtext': 'TEXT',
            'datetime': 'TIMESTAMP',
            'timestamp': 'TIMESTAMP',
            'date': 'DATE',
            'time': 'TIME',
            'json': 'JSON',
            'enum': 'VARCHAR(255)',
            'blob': 'BYTEA',
            'tinyblob': 'BYTEA',
            'mediumblob': 'BYTEA',
            'longblob': 'BYTEA',
        }
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 进度回调函数 (message, current, total)
        """
        self.progress_callback = callback
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(f"{message} ({current}/{total})" if total > 0 else message)
    
    def test_connections(self) -> Dict[str, bool]:
        """
        测试数据库连接
        
        Returns:
            Dict[str, bool]: 连接测试结果
        """
        results = {}
        
        # 测试MySQL连接
        try:
            results['mysql'] = self.mysql_connector.test_connection()
        except Exception as e:
            logging.error(f"MySQL连接测试失败: {e}")
            results['mysql'] = False
        
        # 测试PostgreSQL连接
        try:
            results['postgresql'] = self.pg_connector.test_connection()
        except Exception as e:
            logging.error(f"PostgreSQL连接测试失败: {e}")
            results['postgresql'] = False
        
        return results
    
    def convert_column_type(self, mysql_type: str) -> str:
        """
        转换 MySQL 数据类型到 PostgreSQL
        
        Args:
            mysql_type: MySQL数据类型
            
        Returns:
            str: PostgreSQL数据类型
        """
        # 提取基本类型
        base_type = mysql_type.lower().split('(')[0]
        
        # 检查是否是 unsigned
        is_unsigned = 'unsigned' in mysql_type.lower()
        
        # 获取长度/精度
        length_match = re.search(r'\(([^)]+)\)', mysql_type)
        length = length_match.group(1) if length_match else None
        
        # 转换类型
        pg_type = self.type_mapping.get(base_type, 'TEXT')
        
        # 处理特殊情况
        if base_type in ['varchar', 'char'] and length:
            pg_type = f"{pg_type}({length})"
        elif base_type == 'decimal' and length:
            pg_type = f"{pg_type}({length})"
        elif base_type == 'int' and is_unsigned:
            pg_type = 'BIGINT'  # unsigned int 需要更大的类型
            
        return pg_type
    
    def create_table_sql(self, table_name: str, columns: List[Dict[str, Any]]) -> str:
        """
        生成 PostgreSQL CREATE TABLE 语句
        
        Args:
            table_name: 表名
            columns: 列信息列表
            
        Returns:
            str: CREATE TABLE SQL语句
        """
        column_defs = []
        primary_keys = []
        
        for col in columns:
            col_name = col['Field']
            col_type = self.convert_column_type(col['Type'])
            
            # 处理 AUTO_INCREMENT
            if 'auto_increment' in col.get('Extra', ''):
                col_type = 'SERIAL' if 'int' in col['Type'].lower() else 'BIGSERIAL'
            
            # 构建列定义
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
                primary_keys.append(f'"{col_name}"')
        
        # 构建 CREATE TABLE 语句
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
        create_sql += ',\n'.join(f'  {col}' for col in column_defs)
        
        if primary_keys:
            create_sql += f',\n  PRIMARY KEY ({", ".join(primary_keys)})'
        
        create_sql += '\n);'
        
        return create_sql
    
    def migrate_table_structure(self, table_name: str) -> bool:
        """
        迁移表结构
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 迁移是否成功
        """
        self._report_progress(f"创建表结构: {table_name}")
        
        try:
            # 获取表结构
            columns = self.mysql_connector.get_table_structure(table_name)
            if not columns:
                logging.error(f"无法获取表 {table_name} 的结构")
                return False
            
            # 转换列类型
            for col in columns:
                col['Type'] = self.convert_column_type(col['Type'])
            
            # 在 PostgreSQL 中创建表
            success = self.pg_connector.create_table(table_name, columns)
            if success:
                self._report_progress(f"  ✓ 表结构创建成功: {table_name}")
                return True
            else:
                self._report_progress(f"  ✗ 创建表结构失败: {table_name}")
                return False
                
        except Exception as e:
            logging.error(f"创建表结构失败: {e}")
            self._report_progress(f"  ✗ 创建表结构失败: {table_name} - {e}")
            return False
    
    def migrate_table_data(self, table_name: str, batch_size: int = 1000) -> bool:
        """
        迁移表数据
        
        Args:
            table_name: 表名
            batch_size: 批处理大小
            
        Returns:
            bool: 迁移是否成功
        """
        self._report_progress(f"迁移数据: {table_name}")
        
        try:
            # 获取总行数
            total_rows = self.mysql_connector.get_table_count(table_name)
            self._report_progress(f"  总行数: {total_rows:,}")
            
            if total_rows == 0:
                self._report_progress("  ✓ 无数据需要迁移")
                return True
            
            # 获取列信息
            columns = self.mysql_connector.get_table_structure(table_name)
            column_names = [col['Field'] for col in columns]
            
            # 批量迁移数据
            offset = 0
            migrated_rows = 0
            batch_count = 0
            
            while offset < total_rows:
                # 获取数据
                rows = self.mysql_connector.get_table_data(
                    table_name, batch_size, offset
                )
                
                if not rows:
                    break
                
                # 插入数据到PostgreSQL
                success = self.pg_connector.insert_data(table_name, column_names, rows)
                if not success:
                    logging.error(f"插入数据失败: {table_name}")
                    return False
                
                migrated_rows += len(rows)
                offset += batch_size
                batch_count += 1
                
                # 计算进度百分比
                progress_percent = min(100, (migrated_rows / total_rows) * 100)
                
                # 报告详细进度（每10批或最后一批报告一次）
                if batch_count % 10 == 0 or migrated_rows >= total_rows:
                    self._report_progress(
                        f"  ⏳ {table_name}: {migrated_rows:,}/{total_rows:,} 行 ({progress_percent:.1f}%)",
                        migrated_rows,
                        total_rows
                    )
            
            self._report_progress(f"  ✓ 数据迁移完成: {table_name} ({migrated_rows:,} 行)")
            
            # 更新序列
            self.update_sequences(table_name)
            
            return True
            
        except Exception as e:
            logging.error(f"数据迁移失败: {e}")
            self._report_progress(f"  ✗ 数据迁移失败: {table_name} - {e}")
            return False
    
    def update_sequences(self, table_name: str):
        """
        更新 PostgreSQL 序列的当前值
        
        Args:
            table_name: 表名
        """
        try:
            # 查找所有 SERIAL 列并更新序列
            if self.pg_connector.connection:
                with self.pg_connector.connection.cursor() as cursor:
                    # 查找序列列
                    cursor.execute("""
                        SELECT column_name, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s
                        AND column_default LIKE 'nextval%%'
                    """, (table_name,))
                    
                    serial_columns = cursor.fetchall()
                    
                    for col_name, col_default in serial_columns:
                        # 提取序列名
                        seq_match = re.search(r"'([^']+)'", col_default)
                        if seq_match:
                            seq_name = seq_match.group(1)
                            
                            # 获取列的最大值
                            cursor.execute(f'SELECT MAX("{col_name}") FROM "{table_name}"')
                            max_val = cursor.fetchone()[0]
                            
                            if max_val:
                                # 更新序列
                                cursor.execute(f"SELECT setval('{seq_name}', %s, true)", (max_val,))
                                self._report_progress(f"  ✓ 更新序列 {seq_name} 到 {max_val}")
                    
                    self.pg_connector.connection.commit()
        except Exception as e:
            logging.warning(f"更新序列时出现警告: {e}")
            self._report_progress(f"  ! 更新序列时出现警告: {e}")
    
    def create_indexes(self, table_name: str) -> bool:
        """
        迁移索引
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 索引创建是否成功
        """
        self._report_progress(f"创建索引: {table_name}")
        
        try:
            indexes = self.mysql_connector.get_indexes(table_name)
            
            if not self.pg_connector.connection:
                return False
            
            # 按索引名分组
            index_dict = {}
            for idx in indexes:
                key_name = idx['Key_name']
                if key_name == 'PRIMARY':
                    continue  # 主键已经在创建表时处理
                
                if key_name not in index_dict:
                    index_dict[key_name] = {
                        'unique': idx['Non_unique'] == 0,
                        'columns': []
                    }
                index_dict[key_name]['columns'].append(f'"{idx["Column_name"]}"')
            
            # 创建索引
            with self.pg_connector.connection.cursor() as cursor:
                for idx_name, idx_info in index_dict.items():
                    try:
                        unique = 'UNIQUE' if idx_info['unique'] else ''
                        columns = ', '.join(idx_info['columns'])
                        
                        create_idx_sql = f'''
                        CREATE {unique} INDEX IF NOT EXISTS "{idx_name}_{table_name}_idx"
                        ON "{table_name}" ({columns});
                        '''
                        
                        cursor.execute(create_idx_sql)
                        self.pg_connector.connection.commit()
                        self._report_progress(f"  ✓ 创建索引: {idx_name}")
                    except Exception as e:
                        self.pg_connector.connection.rollback()
                        logging.error(f"创建索引 {idx_name} 失败: {e}")
                        self._report_progress(f"  ✗ 创建索引 {idx_name} 失败: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"创建索引失败: {e}")
            self._report_progress(f"  ✗ 创建索引失败: {table_name} - {e}")
            return False
    
    def migrate(
        self, 
        tables: Optional[List[str]] = None,
        batch_size: int = 1000,
        include_indexes: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的迁移过程
        
        Args:
            tables: 要迁移的表列表，None表示所有表
            batch_size: 批处理大小
            include_indexes: 是否包含索引迁移
            
        Returns:
            Dict[str, Any]: 迁移结果统计
        """
        results = {
            'success': False,
            'total_tables': 0,
            'migrated_tables': 0,
            'failed_tables': [],
            'errors': []
        }
        
        try:
            self._report_progress("开始迁移...")
            self._report_progress(f"源数据库: MySQL {self.mysql_config['database']}")
            self._report_progress(f"目标数据库: PostgreSQL {self.pg_config['database']}")
            
            # 连接数据库
            if not self.mysql_connector.connect():
                raise Exception("无法连接到MySQL数据库")
            
            if not self.pg_connector.connect():
                raise Exception("无法连接到PostgreSQL数据库")
            
            # 获取要迁移的表
            if tables is None:
                tables = self.mysql_connector.get_tables()
            
            results['total_tables'] = len(tables)
            self._report_progress(f"找到 {len(tables)} 个表")
            
            # 迁移每个表
            for i, table in enumerate(tables, 1):
                self._report_progress(f"\n[{i}/{len(tables)}] 处理表: {table}")
                
                try:
                    # 迁移表结构
                    if not self.migrate_table_structure(table):
                        results['failed_tables'].append(table)
                        continue
                    
                    # 迁移数据
                    if not self.migrate_table_data(table, batch_size):
                        results['failed_tables'].append(table)
                        continue
                    
                    # 创建索引
                    if include_indexes:
                        self.create_indexes(table)
                    
                    results['migrated_tables'] += 1
                    self._report_progress(f"✓ 表 {table} 迁移完成")
                    
                except Exception as e:
                    error_msg = f"表 {table} 迁移失败: {e}"
                    logging.error(error_msg)
                    results['failed_tables'].append(table)
                    results['errors'].append(error_msg)
                    self._report_progress(f"✗ {error_msg}")
            
            results['success'] = results['migrated_tables'] > 0
            
            if results['success']:
                self._report_progress("\n" + "=" * 50)
                self._report_progress("迁移完成!")
                self._report_progress(f"成功迁移 {results['migrated_tables']}/{results['total_tables']} 个表")
                
                if results['failed_tables']:
                    self._report_progress(f"失败的表: {', '.join(results['failed_tables'])}")
            else:
                self._report_progress("\n迁移失败!")
            
        except Exception as e:
            error_msg = f"迁移过程出现错误: {e}"
            logging.error(error_msg)
            results['errors'].append(error_msg)
            self._report_progress(f"\n错误: {e}")
        
        finally:
            # 断开连接
            self.mysql_connector.disconnect()
            self.pg_connector.disconnect()
        
        return results
    
    def get_migration_preview(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取迁移预览信息
        
        Args:
            tables: 要预览的表列表
            
        Returns:
            Dict[str, Any]: 预览信息
        """
        preview = {
            'tables': [],
            'total_rows': 0,
            'estimated_time': 0
        }
        
        try:
            if not self.mysql_connector.connect():
                return preview
            
            if tables is None:
                tables = self.mysql_connector.get_tables()
            
            for table in tables:
                table_info = {
                    'name': table,
                    'rows': self.mysql_connector.get_table_count(table),
                    'columns': len(self.mysql_connector.get_table_structure(table))
                }
                preview['tables'].append(table_info)
                preview['total_rows'] += table_info['rows']
            
            # 估算时间（假设每秒处理1000行）
            preview['estimated_time'] = max(1, preview['total_rows'] // 1000)
            
        except Exception as e:
            logging.error(f"获取预览信息失败: {e}")
        finally:
            self.mysql_connector.disconnect()
        
        return preview


# 兼容性函数，保持与原代码示例的一致性
if __name__ == "__main__":
    # 这里是为了兼容原始的代码示例
    mysql_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '12345678',
        'database': 'shellapiminipool'
    }
    
    pg_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'username': 'takedayuuichi',
        'password': '12345678',
        'database': 'shellapiminipool'
    }
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 执行迁移
    migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
    
    # 测试连接
    connections = migrator.test_connections()
    if not all(connections.values()):
        print(f"连接测试失败: {connections}")
        sys.exit(1)
    
    # 执行迁移
    results = migrator.migrate()
    
    if not results['success']:
        sys.exit(1) 