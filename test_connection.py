#!/usr/bin/env python3
"""
数据库连接测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_migrator.connectors.mysql_connector import MySQLConnector
from db_migrator.connectors.postgresql_connector import PostgreSQLConnector

def test_mysql():
    """测试MySQL连接"""
    print("🔍 测试 MySQL 连接...")
    
    mysql_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '12345678',
        'database': 'shellapiminipool'
    }
    
    try:
        connector = MySQLConnector(mysql_config)
        connector.connect()
        print("✅ MySQL 连接成功!")
        
        # 获取所有数据库
        cursor = connector.connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        print(f"📊 可用数据库: {databases}")
        
        # 检查目标数据库是否存在
        if mysql_config['database'] in databases:
            print(f"✅ 数据库 '{mysql_config['database']}' 存在")
            
            # 获取表列表
            tables = connector.get_tables()
            print(f"📋 表数量: {len(tables)}")
            if tables:
                print(f"📋 表列表: {tables}")
            else:
                print("⚠️  数据库中没有表")
        else:
            print(f"❌ 数据库 '{mysql_config['database']}' 不存在")
        
        cursor.close()
        connector.disconnect()
        
    except Exception as e:
        print(f"❌ MySQL 连接失败: {e}")

def test_postgresql():
    """测试PostgreSQL连接"""
    print("\n🔍 测试 PostgreSQL 连接...")
    
    pg_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'username': 'takedayuuichi',
        'password': '12345678',
        'database': 'shellapiminipool'
    }
    
    try:
        connector = PostgreSQLConnector(pg_config)
        success = connector.connect()
        if success:
            print("✅ PostgreSQL 连接成功!")
            
            # 获取表列表
            tables = connector.get_tables()
            print(f"📋 表数量: {len(tables)}")
            if tables:
                print(f"📋 表列表: {tables}")
            else:
                print("⚠️  数据库中没有表")
            
            connector.disconnect()
        else:
            print("❌ PostgreSQL 连接失败")
        
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("数据库连接诊断工具")
    print("=" * 50)
    
    test_mysql()
    test_postgresql()
    
    print("\n" + "=" * 50)
    print("诊断完成!") 