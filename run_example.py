#!/usr/bin/env python3
"""
数据库迁移工具 - 命令行示例启动脚本
Database Migrator - CLI Example Launcher
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 运行命令行示例
    from examples.mysql_to_postgresql_example import main
    main() 