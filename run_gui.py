#!/usr/bin/env python3
"""
数据库迁移工具 - 图形界面启动脚本
Database Migrator - GUI Launcher

使用方法:
python run_gui.py

或者直接双击运行
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from db_migrator.gui.main_window import MigratorGUI
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖包:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def main():
    """主函数"""
    print("正在启动数据库迁移工具图形界面...")
    
    # 配置日志
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "gui.log"),
            logging.StreamHandler()
        ]
    )
    
    try:
        # 创建并运行GUI
        app = MigratorGUI()
        app.run()
    except Exception as e:
        logging.exception("GUI运行异常")
        print(f"启动图形界面时发生错误: {e}")
        
        # 检查是否缺少GUI依赖
        if "tkinter" in str(e).lower():
            print("\n可能缺少tkinter支持。")
            print("在Ubuntu/Debian上，请安装: sudo apt-get install python3-tk")
            print("在CentOS/RHEL上，请安装: sudo yum install tkinter")
        
        sys.exit(1)


if __name__ == "__main__":
    main() 