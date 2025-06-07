#!/usr/bin/env python3
"""
MySQL to PostgreSQL Migration Example
MySQL到PostgreSQL数据迁移完整示例

这个示例展示了如何使用数据库迁移工具将MySQL数据库迁移到PostgreSQL数据库。
包含自动序列生成和数据类型转换功能。

使用方法:
1. 修改下面的数据库配置信息
2. 运行脚本: python examples/mysql_to_postgresql_example.py
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_migrator.migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator


def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """主函数"""
    print("=" * 60)
    print("MySQL到PostgreSQL数据迁移工具")
    print("=" * 60)
    
    # 设置日志
    setup_logging()
    
    # 数据库配置
    mysql_config = {
        'host': '127.0.0.1',        # MySQL服务器地址
        'port': 3306,               # MySQL端口
        'username': 'root',         # MySQL用户名
        'password': '12345678',     # MySQL密码
        'database': 'shellapiminipool'  # 源数据库名
    }
    
    postgresql_config = {
        'host': '127.0.0.1',        # PostgreSQL服务器地址
        'port': 5432,               # PostgreSQL端口
        'username': 'takedayuuichi', # PostgreSQL用户名
        'password': '12345678',     # PostgreSQL密码
        'database': 'shellapiminipool'  # 目标数据库名
    }
    
    print(f"源数据库: MySQL {mysql_config['database']} @ {mysql_config['host']}:{mysql_config['port']}")
    print(f"目标数据库: PostgreSQL {postgresql_config['database']} @ {postgresql_config['host']}:{postgresql_config['port']}")
    print()
    
    # 创建迁移器
    migrator = MySQLToPostgreSQLMigrator(mysql_config, postgresql_config)
    
    # 设置进度回调
    def progress_callback(message, current=0, total=0):
        if total > 0:
            percentage = (current / total) * 100
            print(f"[{percentage:6.2f}%] {message}")
        else:
            print(f"[INFO] {message}")
    
    migrator.set_progress_callback(progress_callback)
    
    try:
        # 1. 测试数据库连接
        print("1. 测试数据库连接...")
        connections = migrator.test_connections()
        
        if not connections['mysql']:
            print("❌ MySQL连接失败！请检查配置信息。")
            return False
        
        if not connections['postgresql']:
            print("❌ PostgreSQL连接失败！请检查配置信息。")
            return False
        
        print("✅ 数据库连接测试成功！")
        print()
        
        # 2. 获取迁移预览
        print("2. 获取迁移预览...")
        preview = migrator.get_migration_preview()
        
        print(f"   📊 总表数: {len(preview['tables'])}")
        print(f"   📊 总行数: {preview['total_rows']:,}")
        print(f"   ⏱️  预计时间: {preview['estimated_time']} 秒")
        print()
        
        if preview['tables']:
            print("   表详情:")
            for table_info in preview['tables'][:5]:  # 显示前5个表
                print(f"   - {table_info['name']}: {table_info['rows']:,} 行, {table_info['columns']} 列")
            
            if len(preview['tables']) > 5:
                print(f"   ... 还有 {len(preview['tables']) - 5} 个表")
            print()
        
        # 3. 确认是否继续
        while True:
            choice = input("是否继续迁移？(y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                break
            elif choice in ['n', 'no', '否']:
                print("取消迁移。")
                return True
            else:
                print("请输入 y 或 n")
        
        # 4. 开始迁移
        print("\n3. 开始数据迁移...")
        print("=" * 60)
        
        # 迁移配置
        migration_options = {
            'tables': None,          # None表示迁移所有表，或者指定表列表：['table1', 'table2']
            'batch_size': 1000,      # 批处理大小
            'include_indexes': True  # 是否包含索引迁移
        }
        
        # 执行迁移
        results = migrator.migrate(
            tables=migration_options['tables'],
            batch_size=migration_options['batch_size'],
            include_indexes=migration_options['include_indexes']
        )
        
        # 5. 显示迁移结果
        print("\n" + "=" * 60)
        print("迁移结果")
        print("=" * 60)
        
        if results['success']:
            print("✅ 迁移成功完成！")
        else:
            print("❌ 迁移失败！")
        
        print(f"📊 总表数: {results['total_tables']}")
        print(f"✅ 成功迁移: {results['migrated_tables']}")
        print(f"❌ 失败表数: {len(results['failed_tables'])}")
        
        if results['failed_tables']:
            print(f"\n失败的表:")
            for table in results['failed_tables']:
                print(f"   - {table}")
        
        if results['errors']:
            print(f"\n错误信息:")
            for error in results['errors'][:3]:  # 显示前3个错误
                print(f"   - {error}")
            
            if len(results['errors']) > 3:
                print(f"   ... 还有 {len(results['errors']) - 3} 个错误")
        
        print(f"\n📝 详细日志已保存到当前目录的日志文件中")
        
        return results['success']
        
    except KeyboardInterrupt:
        print("\n\n用户中断迁移过程。")
        return False
    except Exception as e:
        print(f"\n❌ 迁移过程中发生异常: {e}")
        logging.exception("迁移异常")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"程序异常退出: {e}")
        sys.exit(1) 