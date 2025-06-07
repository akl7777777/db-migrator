#!/bin/bash

# 表选择器演示启动脚本
echo "🗃️ 启动数据库表选择器演示程序..."
echo "============================================"

# 检查是否在项目目录中
if [ ! -f "table_selector.py" ]; then
    echo "❌ 错误：请在 db-migrator 项目目录中运行此脚本"
    exit 1
fi

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "🔄 激活虚拟环境..."
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活：$(python --version)"
else
    echo "⚠️  警告：未找到虚拟环境"
fi

# 设置Python环境
export PYTHONPATH="/opt/homebrew/Cellar/python-tk@3.10/3.10.18/lib/python3.10/site-packages:$PYTHONPATH"

# 检查tkinter支持
python -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误：tkinter未安装或不可用"
    echo "请运行：brew install python-tk@3.10"
    echo "或者安装当前Python版本的tkinter支持"
    exit 1
fi

echo "✅ 环境检查通过"
echo "🚀 启动表选择器..."
echo ""

# 启动表选择器
python table_selector.py 