#!/usr/bin/env python3
"""
快速表选择迁移脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_migrator.migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator

def main():
    """演示表选择功能"""
    
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
    
    print("🔍 获取表列表...")
    migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
    
    # 获取所有表
    preview = migrator.get_migration_preview()
    all_tables = [table['name'] for table in preview['tables']]
    
    print(f"📋 找到 {len(all_tables)} 个表：")
    for i, table in enumerate(all_tables, 1):
        print(f"   {i:2d}. {table}")
    
    # 让用户选择表
    print("\n📌 请选择要迁移的表：")
    print("   输入表名（逗号分隔）或序号（逗号分隔）")
    print("   例如：users,orders 或 1,3,5")
    print("   输入 'all' 迁移所有表")
    
    selection = input("\n请输入：").strip()
    
    if selection.lower() == 'all':
        selected_tables = None  # None表示所有表
        print("✅ 选择迁移所有表")
    else:
        selected_tables = []
        for item in selection.split(','):
            item = item.strip()
            if item.isdigit():
                # 序号选择
                idx = int(item) - 1
                if 0 <= idx < len(all_tables):
                    selected_tables.append(all_tables[idx])
            else:
                # 表名选择
                if item in all_tables:
                    selected_tables.append(item)
        
        if not selected_tables:
            print("❌ 没有选择任何有效的表")
            return
        
        print(f"✅ 选择迁移以下表：{', '.join(selected_tables)}")
    
    # 预览选择的表
    if selected_tables:
        preview = migrator.get_migration_preview(selected_tables)
        print(f"\n📊 预览信息：")
        print(f"   表数量：{len(preview['tables'])}")
        print(f"   总行数：{preview['total_rows']:,}")
        print(f"   预计时间：{preview['estimated_time']} 秒")
    
    # 确认迁移
    confirm = input("\n是否开始迁移？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 迁移已取消")
        return
    
    # 开始迁移
    print("\n🚀 开始迁移...")
    results = migrator.migrate(tables=selected_tables, batch_size=1000, include_indexes=True)
    
    # 显示结果
    print("\n" + "=" * 50)
    print("迁移结果")
    print("=" * 50)
    
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
    

if __name__ == "__main__":
    main() 