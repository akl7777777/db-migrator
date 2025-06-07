#!/bin/bash
# 数据库迁移工具图形界面启动脚本

# 设置tkinter支持
export PYTHONPATH="/opt/homebrew/Cellar/python-tk@3.10/3.10.18/lib/python3.10/site-packages:$PYTHONPATH"

# 激活虚拟环境
source .venv/bin/activate

# 启动GUI
python run_gui.py 