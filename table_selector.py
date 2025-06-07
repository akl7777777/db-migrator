#!/usr/bin/env python3
"""
数据库表选择器工具 - 演示增强的表选择功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
import fnmatch
from db_migrator.connectors.mysql_connector import MySQLConnector


class TableSelectorDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🗃️ 数据库表选择器演示")
        self.root.geometry("900x700")
        
        # 数据存储
        self.all_tables_data = []
        
        # 变量
        self.search_var = tk.StringVar()
        self.show_filter_var = tk.StringVar(value="all")
        
        self.create_widgets()
        
        # 预加载数据
        self.load_sample_data()

    def create_widgets(self):
        """创建界面组件"""
        
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ttk.Label(title_frame, text="🗃️ 数据库表选择器 - 功能演示", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="演示MySQL到PostgreSQL迁移工具的表选择功能", 
                                  font=("Arial", 10))
        subtitle_label.pack(pady=(5, 0))
        
        # 连接配置
        config_frame = ttk.LabelFrame(self.root, text="数据库连接配置")
        config_frame.pack(fill="x", padx=10, pady=10)
        
        # MySQL配置输入框
        mysql_frame = ttk.Frame(config_frame)
        mysql_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(mysql_frame, text="MySQL:").pack(side="left")
        self.mysql_config_var = tk.StringVar(value="root:12345678@127.0.0.1:3306/shellapiminipool")
        mysql_entry = ttk.Entry(mysql_frame, textvariable=self.mysql_config_var, width=60)
        mysql_entry.pack(side="left", padx=(10, 5), fill="x", expand=True)
        
        ttk.Button(mysql_frame, text="🔗 连接并加载表", command=self.load_real_data).pack(side="right")
        
        # 操作按钮区域
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="✅ 全选", command=self.select_all).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="❌ 全不选", command=self.deselect_all).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🔄 反选", command=self.invert_selection).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🔍 按模式选择", command=self.pattern_select_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="📊 表统计", command=self.show_stats).pack(side="left", padx=5)
        
        # 搜索和过滤区域
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="🔍 搜索:").pack(side="left")
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(5, 15))
        search_entry.bind('<KeyRelease>', self.filter_tables)
        
        ttk.Label(filter_frame, text="显示:").pack(side="left")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.show_filter_var, 
                                   values=["all", "selected", "unselected", "large", "small", "empty"], 
                                   width=12, state="readonly")
        filter_combo.pack(side="left", padx=(5, 15))
        filter_combo.bind('<<ComboboxSelected>>', self.filter_tables)
        
        ttk.Label(filter_frame, text="大小阈值:").pack(side="left")
        self.size_threshold_var = tk.StringVar(value="10000")
        size_entry = ttk.Entry(filter_frame, textvariable=self.size_threshold_var, width=10)
        size_entry.pack(side="left", padx=(5, 0))
        size_entry.bind('<KeyRelease>', self.filter_tables)
        
        # 表列表区域
        list_frame = ttk.LabelFrame(self.root, text="表列表与详情")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建树形视图
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 表格列定义
        columns = ('table', 'rows', 'size', 'columns', 'type')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', selectmode='extended')
        
        # 设置列标题和宽度
        self.tree.heading('#0', text='✓', anchor='center')
        self.tree.heading('table', text='表名', anchor='w')
        self.tree.heading('rows', text='行数', anchor='e')
        self.tree.heading('size', text='大小', anchor='e')
        self.tree.heading('columns', text='列数', anchor='e')
        self.tree.heading('type', text='类型', anchor='center')
        
        self.tree.column('#0', width=40, minwidth=40)
        self.tree.column('table', width=250, minwidth=150)
        self.tree.column('rows', width=100, minwidth=80)
        self.tree.column('size', width=100, minwidth=80)
        self.tree.column('columns', width=80, minwidth=60)
        self.tree.column('type', width=80, minwidth=60)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定事件
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)
        self.tree.bind('<Double-1>', self.show_table_details)
        self.tree.bind('<Button-3>', self.show_context_menu)  # 右键菜单
        
        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="📋 准备就绪")
        self.status_label.pack(side="left")
        
        # 选择信息标签
        self.selection_label = ttk.Label(status_frame, text="选中: 0/0")
        self.selection_label.pack(side="right")

    def load_sample_data(self):
        """加载示例数据"""
        # 生成示例表数据
        sample_tables = [
            {'name': 'users', 'rows': 150000, 'columns': 12, 'type': '用户'},
            {'name': 'orders', 'rows': 500000, 'columns': 8, 'type': '订单'},
            {'name': 'products', 'rows': 25000, 'columns': 15, 'type': '商品'},
            {'name': 'user_profiles', 'rows': 149500, 'columns': 20, 'type': '用户'},
            {'name': 'order_items', 'rows': 2000000, 'columns': 6, 'type': '订单'},
            {'name': 'categories', 'rows': 500, 'columns': 5, 'type': '分类'},
            {'name': 'inventory', 'rows': 75000, 'columns': 10, 'type': '库存'},
            {'name': 'user_logs', 'rows': 5000000, 'columns': 8, 'type': '日志'},
            {'name': 'payment_logs', 'rows': 800000, 'columns': 12, 'type': '日志'},
            {'name': 'system_config', 'rows': 50, 'columns': 3, 'type': '配置'},
            {'name': 'temp_data', 'rows': 0, 'columns': 5, 'type': '临时'},
            {'name': 'backup_users', 'rows': 100000, 'columns': 12, 'type': '备份'},
        ]
        
        # 计算大小并完善数据
        for table in sample_tables:
            size_mb = table['rows'] * table['columns'] * 0.001
            if size_mb < 1:
                table['size'] = f"{size_mb*1000:.0f}KB"
                table['size_mb'] = size_mb
            elif size_mb < 1024:
                table['size'] = f"{size_mb:.1f}MB"
                table['size_mb'] = size_mb
            else:
                table['size'] = f"{size_mb/1024:.1f}GB"
                table['size_mb'] = size_mb
        
        self.all_tables_data = sample_tables
        self.populate_table_list()
        self.update_status("✅ 示例数据加载完成")

    def load_real_data(self):
        """从真实数据库加载表数据"""
        try:
            config_str = self.mysql_config_var.get()
            # 解析连接字符串 user:pass@host:port/db
            parts = config_str.split('@')
            if len(parts) != 2:
                raise ValueError("配置格式错误")
            
            user_pass = parts[0].split(':')
            host_port_db = parts[1].split('/')
            host_port = host_port_db[0].split(':')
            
            mysql_config = {
                'host': host_port[0],
                'port': int(host_port[1]) if len(host_port) > 1 else 3306,
                'username': user_pass[0],
                'password': user_pass[1],
                'database': host_port_db[1]
            }
            
            self.update_status("🔄 正在连接数据库...")
            
            connector = MySQLConnector(mysql_config)
            if connector.connect():
                tables = connector.get_tables()
                self.all_tables_data = []
                
                self.update_status(f"📊 正在获取 {len(tables)} 个表的信息...")
                
                for i, table_name in enumerate(tables):
                    try:
                        rows = connector.get_table_count(table_name)
                        structure = connector.get_table_structure(table_name)
                        columns = len(structure) if structure else 0
                        
                        # 估算大小
                        size_mb = rows * columns * 0.001
                        if size_mb < 1:
                            size_str = f"{size_mb*1000:.0f}KB"
                        elif size_mb < 1024:
                            size_str = f"{size_mb:.1f}MB"
                        else:
                            size_str = f"{size_mb/1024:.1f}GB"
                        
                        # 判断表类型
                        table_type = "数据"
                        if "_log" in table_name.lower():
                            table_type = "日志"
                        elif "temp" in table_name.lower():
                            table_type = "临时"
                        elif "backup" in table_name.lower():
                            table_type = "备份"
                        elif "config" in table_name.lower():
                            table_type = "配置"
                        
                        table_info = {
                            'name': table_name,
                            'rows': rows,
                            'columns': columns,
                            'size': size_str,
                            'size_mb': size_mb,
                            'type': table_type
                        }
                        
                        self.all_tables_data.append(table_info)
                        
                        # 更新进度
                        if i % 5 == 0:  # 每5个表更新一次状态
                            self.update_status(f"📊 正在获取表信息... ({i+1}/{len(tables)})")
                            self.root.update()
                    
                    except Exception as e:
                        print(f"获取表 {table_name} 信息时出错: {e}")
                
                connector.disconnect()
                self.populate_table_list()
                self.update_status(f"✅ 成功加载 {len(self.all_tables_data)} 个表的信息")
                
            else:
                messagebox.showerror("连接错误", "无法连接到MySQL数据库")
                self.update_status("❌ 数据库连接失败")
        
        except Exception as e:
            messagebox.showerror("加载错误", f"加载数据时发生错误:\n{str(e)}")
            self.update_status("❌ 数据加载失败")

    def populate_table_list(self):
        """填充表列表"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加表数据
        for table_info in self.all_tables_data:
            self.tree.insert('', 'end', text='☐',
                values=(table_info['name'], 
                       f"{table_info['rows']:,}",
                       table_info['size'],
                       table_info['columns'],
                       table_info['type']))
        
        self.update_selection_info()

    def filter_tables(self, event=None):
        """过滤表列表"""
        search_text = self.search_var.get().lower()
        show_filter = self.show_filter_var.get()
        
        try:
            size_threshold = int(self.size_threshold_var.get())
        except ValueError:
            size_threshold = 10000
        
        # 清空现有显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取选中的表
        selected_tables = self.get_selected_tables()
        
        # 过滤并显示表
        for table_info in self.all_tables_data:
            table_name = table_info['name']
            is_selected = table_name in selected_tables
            
            # 应用搜索过滤
            if search_text and search_text not in table_name.lower():
                continue
            
            # 应用显示过滤
            if show_filter == "selected" and not is_selected:
                continue
            elif show_filter == "unselected" and is_selected:
                continue
            elif show_filter == "large" and table_info['rows'] < size_threshold:
                continue
            elif show_filter == "small" and table_info['rows'] >= size_threshold:
                continue
            elif show_filter == "empty" and table_info['rows'] > 0:
                continue
            
            # 设置选择标记
            check_mark = '☑' if is_selected else '☐'
            
            item_id = self.tree.insert('', 'end', text=check_mark,
                values=(table_name, 
                       f"{table_info['rows']:,}",
                       table_info['size'],
                       table_info['columns'],
                       table_info['type']))
            
            # 如果是选中的表，添加选择
            if is_selected:
                self.tree.selection_add(item_id)
        
        self.update_selection_info()

    def get_selected_tables(self):
        """获取选中的表"""
        selection = self.tree.selection()
        selected_tables = []
        for item_id in selection:
            table_name = self.tree.item(item_id)['values'][0]
            selected_tables.append(table_name)
        return selected_tables

    def select_all(self):
        """全选"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self.update_selection_marks()

    def deselect_all(self):
        """全不选"""
        self.tree.selection_remove(self.tree.get_children())
        self.update_selection_marks()

    def invert_selection(self):
        """反选"""
        current_selection = self.tree.selection()
        all_items = self.tree.get_children()
        
        # 先取消所有选择
        self.tree.selection_remove(all_items)
        
        # 选择之前未选择的项目
        for item in all_items:
            if item not in current_selection:
                self.tree.selection_add(item)
        
        self.update_selection_marks()

    def update_selection_marks(self):
        """更新选择标记"""
        selected_tables = self.get_selected_tables()
        
        for item in self.tree.get_children():
            table_name = self.tree.item(item)['values'][0]
            check_mark = '☑' if table_name in selected_tables else '☐'
            self.tree.item(item, text=check_mark)
        
        self.update_selection_info()

    def on_selection_change(self, event=None):
        """选择变化事件"""
        self.update_selection_marks()

    def update_selection_info(self):
        """更新选择信息"""
        total = len(self.tree.get_children())
        selected = len(self.tree.selection())
        
        # 计算选中表的总行数
        selected_tables = self.get_selected_tables()
        total_rows = 0
        for table_info in self.all_tables_data:
            if table_info['name'] in selected_tables:
                total_rows += table_info['rows']
        
        info_text = f"选中: {selected}/{total} | 总行数: {total_rows:,}"
        self.selection_label.configure(text=info_text)

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.configure(text=message)
        self.root.update()

    def pattern_select_dialog(self):
        """按模式选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("按模式选择表")
        dialog.geometry("450x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 预设模式
        preset_frame = ttk.LabelFrame(dialog, text="常用模式")
        preset_frame.pack(fill="x", padx=10, pady=10)
        
        presets = [
            ("用户相关", "user*"),
            ("订单相关", "order*"),
            ("日志表", "*log*"),
            ("临时表", "temp*"),
            ("备份表", "backup*"),
            ("配置表", "*config*")
        ]
        
        for i, (name, pattern) in enumerate(presets):
            row, col = i // 3, i % 3
            btn = ttk.Button(preset_frame, text=name, width=12,
                           command=lambda p=pattern: pattern_var.set(p))
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # 自定义模式
        custom_frame = ttk.LabelFrame(dialog, text="自定义模式")
        custom_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(custom_frame, text="模式 (支持通配符 * 和 ?):").pack(anchor="w", padx=5, pady=(5, 0))
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(custom_frame, textvariable=pattern_var, width=50)
        pattern_entry.pack(fill="x", padx=5, pady=5)
        pattern_entry.focus()
        
        ttk.Label(custom_frame, text="示例: user_*, *_log, temp_?_*", 
                 foreground="gray").pack(anchor="w", padx=5)
        
        # 预览
        preview_frame = ttk.LabelFrame(dialog, text="匹配预览")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        preview_list = tk.Listbox(preview_frame)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", 
                                     command=preview_list.yview)
        preview_list.configure(yscrollcommand=preview_scroll.set)
        
        preview_list.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        preview_scroll.pack(side="right", fill="y", pady=5)
        
        def update_preview(*args):
            pattern = pattern_var.get()
            preview_list.delete(0, tk.END)
            
            if pattern:
                matched = []
                for table_info in self.all_tables_data:
                    if fnmatch.fnmatch(table_info['name'], pattern):
                        matched.append(table_info['name'])
                
                if matched:
                    preview_list.insert(0, f"--- 匹配到 {len(matched)} 个表 ---")
                    for table in matched:
                        preview_list.insert(tk.END, table)
                else:
                    preview_list.insert(0, "--- 没有匹配的表 ---")
        
        pattern_var.trace('w', update_preview)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def apply_pattern():
            pattern = pattern_var.get()
            if pattern:
                # 先清空选择
                self.deselect_all()
                
                # 选择匹配的表
                for item in self.tree.get_children():
                    table_name = self.tree.item(item)['values'][0]
                    if fnmatch.fnmatch(table_name, pattern):
                        self.tree.selection_add(item)
                
                self.update_selection_marks()
                dialog.destroy()
        
        ttk.Button(button_frame, text="应用", command=apply_pattern).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="right")

    def show_stats(self):
        """显示统计信息"""
        if not self.all_tables_data:
            messagebox.showwarning("提示", "没有表数据")
            return
        
        total_tables = len(self.all_tables_data)
        total_rows = sum(table['rows'] for table in self.all_tables_data)
        total_size_mb = sum(table['size_mb'] for table in self.all_tables_data)
        
        # 按类型统计
        type_stats = {}
        for table in self.all_tables_data:
            table_type = table['type']
            if table_type not in type_stats:
                type_stats[table_type] = {'count': 0, 'rows': 0}
            type_stats[table_type]['count'] += 1
            type_stats[table_type]['rows'] += table['rows']
        
        # 找出最大的表
        largest_table = max(self.all_tables_data, key=lambda x: x['rows']) if self.all_tables_data else None
        
        # 空表统计
        empty_tables = [table for table in self.all_tables_data if table['rows'] == 0]
        
        message = f"📊 数据库统计信息\n\n"
        message += f"总表数: {total_tables}\n"
        message += f"总行数: {total_rows:,}\n"
        message += f"估算大小: {total_size_mb:.1f} MB\n\n"
        
        message += f"按类型统计:\n"
        for table_type, stats in type_stats.items():
            message += f"  {table_type}: {stats['count']} 个表, {stats['rows']:,} 行\n"
        
        if largest_table:
            message += f"\n最大表: {largest_table['name']}\n"
            message += f"  行数: {largest_table['rows']:,}\n"
            message += f"  列数: {largest_table['columns']}\n"
        
        if empty_tables:
            message += f"\n空表数量: {len(empty_tables)}\n"
            if len(empty_tables) <= 5:
                message += f"空表: {', '.join([t['name'] for t in empty_tables])}"
            else:
                message += f"空表: {', '.join([t['name'] for t in empty_tables[:5]])} 等"
        
        messagebox.showinfo("数据库统计", message)

    def show_table_details(self, event):
        """显示表详细信息"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        table_name = self.tree.item(item)['values'][0]
        
        # 找到表信息
        table_info = None
        for info in self.all_tables_data:
            if info['name'] == table_name:
                table_info = info
                break
        
        if not table_info:
            return
        
        # 创建详情对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"表详情: {table_name}")
        dialog.geometry("400x300")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        
        # 基本信息
        info_text = f"""
表名: {table_info['name']}
行数: {table_info['rows']:,}
列数: {table_info['columns']}
大小: {table_info['size']}
类型: {table_info['type']}

估算信息:
- 平均每行大小: {(table_info['size_mb']*1024*1024/max(table_info['rows'], 1)):.1f} 字节
- 如果批量处理 1000 行，需要 {max(1, table_info['rows']//1000)} 批次
- 估算迁移时间: {max(1, table_info['rows']//10000)} 秒
        """
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert(tk.END, info_text.strip())
        text_widget.configure(state=tk.DISABLED)
        
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选择右键点击的项目
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # 创建右键菜单
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="📋 查看详情", command=lambda: self.show_table_details(None))
            context_menu.add_separator()
            context_menu.add_command(label="✅ 选择", command=lambda: self.tree.selection_add(item))
            context_menu.add_command(label="❌ 取消选择", command=lambda: self.tree.selection_remove(item))
            context_menu.add_separator()
            context_menu.add_command(label="🔍 选择同类型表", command=self.select_same_type)
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def select_same_type(self):
        """选择相同类型的表"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        table_name = self.tree.item(item)['values'][0]
        table_type = self.tree.item(item)['values'][4]
        
        # 选择所有相同类型的表
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][4] == table_type:
                self.tree.selection_add(item)
        
        self.update_selection_marks()
        messagebox.showinfo("批量选择", f"已选择所有 '{table_type}' 类型的表")

    def run(self):
        """运行演示"""
        self.root.mainloop()


if __name__ == "__main__":
    print("🚀 启动数据库表选择器演示...")
    demo = TableSelectorDemo()
    demo.run() 