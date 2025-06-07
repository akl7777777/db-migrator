#!/usr/bin/env python3
"""
简单的数据库迁移测试脚本
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from db_migrator.migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator


def main():
    """主函数"""
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("数据库迁移工具 - MySQL to PostgreSQL")
    print("=" * 60)
    
    # 数据库配置
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
    
    try:
        # 1. 创建迁移器
        print("\n1. 初始化迁移器...")
        migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
        
        # 2. 测试连接
        print("\n2. 测试数据库连接...")
        connections = migrator.test_connections()
        print(f"   MySQL连接: {'✅ 成功' if connections['mysql'] else '❌ 失败'}")
        print(f"   PostgreSQL连接: {'✅ 成功' if connections['postgresql'] else '❌ 失败'}")
        
        if not all(connections.values()):
            print("❌ 数据库连接失败，请检查配置")
            return False
        
        # 3. 获取迁移预览
        print("\n3. 获取迁移预览...")
        preview = migrator.get_migration_preview()
        
        print(f"   📊 总表数: {len(preview['tables'])}")
        print(f"   📊 总行数: {preview['total_rows']}")
        print(f"   ⏱️  预计时间: {preview['estimated_time']} 秒")
        
        # 4. 询问是否继续
        response = input("\n是否继续迁移？(y/n): ").strip().lower()
        if response != 'y':
            print("迁移已取消")
            return True
        
        # 5. 执行迁移
        print("\n4. 开始数据迁移...")
        print("=" * 60)
        
        results = migrator.migrate()
        
        # 6. 显示结果
        print("\n" + "=" * 60)
        print("迁移结果")
        print("=" * 60)
        
        if results['success']:
            print("✅ 迁移成功!")
        else:
            print("❌ 迁移失败!")
        
        print(f"📊 总表数: {results['total_tables']}")
        print(f"✅ 成功迁移: {results['migrated_tables']}")
        print(f"❌ 失败表数: {len(results['failed_tables'])}")
        
        if results['failed_tables']:
            print(f"\n失败的表:")
            for table in results['failed_tables']:
                print(f"   - {table}")
        
        if results['errors']:
            print(f"\n错误信息:")
            for error in results['errors']:
                print(f"   - {error}")
        
        return results['success']
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生异常: {e}")
        logging.exception("迁移异常")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 