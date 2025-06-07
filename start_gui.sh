#!/bin/bash
# 数据库迁移工具GUI启动脚本

echo "🚀 启动数据库迁移工具图形界面..."

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "🔄 激活虚拟环境..."
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活：$(python --version)"
fi

# 设置tkinter环境
export PYTHONPATH="/opt/homebrew/Cellar/python-tk@3.10/3.10.18/lib/python3.10/site-packages:$PYTHONPATH"

# 启动GUI
python run_gui.py 