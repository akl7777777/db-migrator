#!/bin/bash

# 同时启动两个图形界面程序
echo "🚀 启动数据库迁移工具演示程序..."
echo "============================================"

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "🔄 激活虚拟环境..."
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活：$(python --version)"
fi

# 设置环境变量
export PYTHONPATH="/opt/homebrew/Cellar/python-tk@3.10/3.10.18/lib/python3.10/site-packages:/opt/homebrew/Cellar/python-tk@3.12/3.12.11/lib/python3.12/site-packages:$PYTHONPATH"

# 检查tkinter支持
python -c "import tkinter; print('✅ tkinter可用')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误：tkinter不可用"
    echo "请运行：brew install python-tk@3.10 或 python-tk@3.12"
    exit 1
fi

echo ""
echo "🗃️ 启动表选择器演示程序..."
python table_selector.py &

echo ""
echo "🏠 启动主GUI迁移工具..."
python run_gui.py &

echo ""
echo "✅ 两个程序都已启动！"
echo "📝 测试重点：单击表格行切换选择状态"
echo ""

wait 