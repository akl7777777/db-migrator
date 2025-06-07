#!/usr/bin/env python3
"""
Migration Manager - 统一的迁移管理器
"""

import logging
from typing import Dict, List, Any, Optional
from ..migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator


class MigrationManager:
    """迁移管理器 - 统一管理不同类型数据库之间的迁移"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化迁移管理器
        
        Args:
            config: 迁移配置字典
        """
        self.config = config
        self.migration_config = config['migration']
        self.source_config = self.migration_config['source']
        self.target_config = self.migration_config['target']
        self.options = self.migration_config.get('options', {})
        
        # 根据数据库类型选择迁移器
        self.migrator = self._create_migrator()
    
    def _create_migrator(self):
        """根据源和目标数据库类型创建对应的迁移器"""
        source_type = self.source_config['type'].lower()
        target_type = self.target_config['type'].lower()
        
        if source_type == 'mysql' and target_type == 'postgresql':
            return MySQLToPostgreSQLMigrator(
                self._build_connector_config(self.source_config),
                self._build_connector_config(self.target_config)
            )
        else:
            raise ValueError(f"不支持的迁移类型: {source_type} -> {target_type}")
    
    def _build_connector_config(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建连接器配置"""
        return {
            'host': db_config['host'],
            'port': db_config['port'],
            'username': db_config['username'],
            'password': db_config['password'],
            'database': db_config['database']
        }
    
    def test_source_connection(self) -> bool:
        """测试源数据库连接"""
        try:
            if hasattr(self.migrator, 'mysql_connector'):
                return self.migrator.mysql_connector.test_connection()
            return False
        except Exception as e:
            logging.error(f"源数据库连接测试失败: {e}")
            return False
    
    def test_target_connection(self) -> bool:
        """测试目标数据库连接"""
        try:
            if hasattr(self.migrator, 'pg_connector'):
                return self.migrator.pg_connector.test_connection()
            return False
        except Exception as e:
            logging.error(f"目标数据库连接测试失败: {e}")
            return False
    
    def get_source_tables(self) -> List[str]:
        """获取源数据库表列表"""
        try:
            if hasattr(self.migrator, 'mysql_connector'):
                if not self.migrator.mysql_connector.connect():
                    raise Exception("无法连接到源数据库")
                tables = self.migrator.mysql_connector.get_tables()
                self.migrator.mysql_connector.disconnect()
                return [{'name': table} for table in tables]
            return []
        except Exception as e:
            logging.error(f"获取源数据库表列表失败: {e}")
            raise
    
    def migrate(self) -> Dict[str, Any]:
        """执行迁移"""
        try:
            # 获取迁移选项
            tables = self.options.get('tables')
            batch_size = self.options.get('batch_size', 1000)
            include_indexes = self.options.get('migrate_indexes', True)
            
            # 执行迁移
            return self.migrator.migrate(
                tables=tables,
                batch_size=batch_size,
                include_indexes=include_indexes
            )
            
        except Exception as e:
            logging.error(f"迁移执行失败: {e}")
            return {
                'success': False,
                'total_tables': 0,
                'migrated_tables': 0,
                'failed_tables': [],
                'errors': [str(e)]
            }
    
    def get_migration_preview(self) -> Dict[str, Any]:
        """获取迁移预览"""
        try:
            tables = self.options.get('tables')
            return self.migrator.get_migration_preview(tables)
        except Exception as e:
            logging.error(f"获取迁移预览失败: {e}")
            return {
                'tables': [],
                'total_rows': 0,
                'estimated_time': 0
            } 