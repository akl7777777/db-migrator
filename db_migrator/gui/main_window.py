#!/usr/bin/env python3
"""
数据库迁移工具 - 图形界面主窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from typing import Dict, Any, Optional
import logging
import tkinter.ttk as ttk
import re
import time

try:
    import customtkinter as ctk
    CUSTOM_TK_AVAILABLE = True
except ImportError:
    CUSTOM_TK_AVAILABLE = False

from ..migrators.mysql_to_postgresql import MySQLToPostgreSQLMigrator


class MigratorGUI:
    """数据库迁移工具图形界面"""
    
    def __init__(self):
        """初始化GUI"""
        if CUSTOM_TK_AVAILABLE:
            # 使用现代化的CustomTkinter
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
            self.use_custom_tk = True
        else:
            # 使用标准tkinter
            self.root = tk.Tk()
            self.use_custom_tk = False
        
        self.root.title("数据库迁移工具 - Database Migrator")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)
        
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 迁移器实例
        self.migrator: Optional[MySQLToPostgreSQLMigrator] = None
        self.migration_thread: Optional[threading.Thread] = None
        self.is_migrating = False
        
        # 表选择状态管理
        self.all_tables_data = []
        self.selected_table_names = set()  # 独立维护选择状态
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的配置
        self.load_config()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        if self.use_custom_tk:
            main_frame = ctk.CTkFrame(self.root)
        else:
            main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 标题
        if self.use_custom_tk:
            title_label = ctk.CTkLabel(
                main_frame, 
                text="数据库迁移工具", 
                font=ctk.CTkFont(size=24, weight="bold")
            )
        else:
            title_label = ttk.Label(
                main_frame, 
                text="数据库迁移工具", 
                font=("Arial", 24, "bold")
            )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 创建选项卡
        if self.use_custom_tk:
            self.notebook = ctk.CTkTabview(main_frame)
        else:
            self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # 配置选项卡
        self.create_config_tab()
        
        # 迁移选项卡
        self.create_migration_tab()
        
        # 日志选项卡
        self.create_log_tab()
        
        # 控制按钮框架
        self.create_control_buttons(main_frame)
    
    def create_config_tab(self):
        """创建配置选项卡"""
        if self.use_custom_tk:
            config_frame = self.notebook.add("数据库配置")
        else:
            config_frame = ttk.Frame(self.notebook)
            self.notebook.add(config_frame, text="数据库配置")
        
        # 配置滚动框架
        if self.use_custom_tk:
            config_scroll = ctk.CTkScrollableFrame(config_frame)
        else:
            canvas = tk.Canvas(config_frame)
            scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
            config_scroll = ttk.Frame(canvas)
            
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.create_window((0, 0), window=config_scroll, anchor="nw")
        
        config_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # MySQL配置
        self.create_mysql_config(config_scroll)
        
        # PostgreSQL配置
        self.create_postgresql_config(config_scroll)
        
        # 配置操作按钮
        self.create_config_buttons(config_scroll)
    
    def create_mysql_config(self, parent):
        """创建MySQL配置区域"""
        if self.use_custom_tk:
            mysql_frame = ctk.CTkFrame(parent)
            mysql_frame.pack(fill="x", pady=(0, 15))
            
            title = ctk.CTkLabel(mysql_frame, text="MySQL 源数据库", font=ctk.CTkFont(size=16, weight="bold"))
            title.pack(pady=(10, 15))
        else:
            mysql_frame = ttk.LabelFrame(parent, text="MySQL 源数据库", padding=10)
            mysql_frame.pack(fill="x", pady=(0, 15))
        
        # MySQL配置变量
        self.mysql_vars = {
            'host': tk.StringVar(value='127.0.0.1'),
            'port': tk.StringVar(value='3306'),
            'username': tk.StringVar(value='root'),
            'password': tk.StringVar(value=''),
            'database': tk.StringVar(value='')
        }
        
        # 配置字段
        fields = [
            ('主机地址:', 'host'),
            ('端口:', 'port'),
            ('用户名:', 'username'),
            ('密码:', 'password'),
            ('数据库名:', 'database')
        ]
        
        for i, (label_text, var_name) in enumerate(fields):
            if self.use_custom_tk:
                label = ctk.CTkLabel(mysql_frame, text=label_text)
                label.pack(anchor="w", padx=10, pady=(5, 0))
                
                if var_name == 'password':
                    entry = ctk.CTkEntry(mysql_frame, textvariable=self.mysql_vars[var_name], show="*")
                else:
                    entry = ctk.CTkEntry(mysql_frame, textvariable=self.mysql_vars[var_name])
                entry.pack(fill="x", padx=10, pady=(0, 10))
            else:
                frame = ttk.Frame(mysql_frame)
                frame.pack(fill="x", pady=2)
                
                label = ttk.Label(frame, text=label_text, width=12)
                label.pack(side="left")
                
                if var_name == 'password':
                    entry = ttk.Entry(frame, textvariable=self.mysql_vars[var_name], show="*")
                else:
                    entry = ttk.Entry(frame, textvariable=self.mysql_vars[var_name])
                entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def create_postgresql_config(self, parent):
        """创建PostgreSQL配置区域"""
        if self.use_custom_tk:
            pg_frame = ctk.CTkFrame(parent)
            pg_frame.pack(fill="x", pady=(0, 15))
            
            title = ctk.CTkLabel(pg_frame, text="PostgreSQL 目标数据库", font=ctk.CTkFont(size=16, weight="bold"))
            title.pack(pady=(10, 15))
        else:
            pg_frame = ttk.LabelFrame(parent, text="PostgreSQL 目标数据库", padding=10)
            pg_frame.pack(fill="x", pady=(0, 15))
        
        # PostgreSQL配置变量
        self.pg_vars = {
            'host': tk.StringVar(value='127.0.0.1'),
            'port': tk.StringVar(value='5432'),
            'username': tk.StringVar(value='postgres'),
            'password': tk.StringVar(value=''),
            'database': tk.StringVar(value='')
        }
        
        # 配置字段
        fields = [
            ('主机地址:', 'host'),
            ('端口:', 'port'),
            ('用户名:', 'username'),
            ('密码:', 'password'),
            ('数据库名:', 'database')
        ]
        
        for i, (label_text, var_name) in enumerate(fields):
            if self.use_custom_tk:
                label = ctk.CTkLabel(pg_frame, text=label_text)
                label.pack(anchor="w", padx=10, pady=(5, 0))
                
                if var_name == 'password':
                    entry = ctk.CTkEntry(pg_frame, textvariable=self.pg_vars[var_name], show="*")
                else:
                    entry = ctk.CTkEntry(pg_frame, textvariable=self.pg_vars[var_name])
                entry.pack(fill="x", padx=10, pady=(0, 10))
            else:
                frame = ttk.Frame(pg_frame)
                frame.pack(fill="x", pady=2)
                
                label = ttk.Label(frame, text=label_text, width=12)
                label.pack(side="left")
                
                if var_name == 'password':
                    entry = ttk.Entry(frame, textvariable=self.pg_vars[var_name], show="*")
                else:
                    entry = ttk.Entry(frame, textvariable=self.pg_vars[var_name])
                entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def create_config_buttons(self, parent):
        """创建配置操作按钮"""
        if self.use_custom_tk:
            button_frame = ctk.CTkFrame(parent)
            button_frame.pack(fill="x", pady=10)
            
            test_btn = ctk.CTkButton(button_frame, text="测试连接", command=self.test_connections)
            test_btn.pack(side="left", padx=(10, 5))
            
            save_btn = ctk.CTkButton(button_frame, text="保存配置", command=self.save_config)
            save_btn.pack(side="left", padx=5)
            
            load_btn = ctk.CTkButton(button_frame, text="加载配置", command=self.load_config_file)
            load_btn.pack(side="left", padx=5)
        else:
            button_frame = ttk.Frame(parent)
            button_frame.pack(fill="x", pady=10)
            
            test_btn = ttk.Button(button_frame, text="测试连接", command=self.test_connections)
            test_btn.pack(side="left", padx=(0, 5))
            
            save_btn = ttk.Button(button_frame, text="保存配置", command=self.save_config)
            save_btn.pack(side="left", padx=5)
            
            load_btn = ttk.Button(button_frame, text="加载配置", command=self.load_config_file)
            load_btn.pack(side="left", padx=5)
    
    def create_migration_tab(self):
        """创建迁移设置选项卡"""
        if self.use_custom_tk:
            migration_frame = self.notebook.add("迁移设置")
        else:
            migration_frame = ttk.Frame(self.notebook)
            self.notebook.add(migration_frame, text="迁移设置")
        
        migration_frame.grid_rowconfigure(1, weight=1)
        migration_frame.grid_columnconfigure(0, weight=1)
        
        # 迁移选项
        if self.use_custom_tk:
            options_frame = ctk.CTkFrame(migration_frame)
            options_frame.pack(fill="x", padx=10, pady=10)
            
            # 第一行：批处理大小
            batch_frame = ctk.CTkFrame(options_frame)
            batch_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(batch_frame, text="批处理大小:").pack(side="left", padx=(10, 5))
            self.batch_size_var = tk.StringVar(value="1000")
            batch_entry = ctk.CTkEntry(batch_frame, textvariable=self.batch_size_var, width=80)
            batch_entry.pack(side="left", padx=5)
            
            # 第二行：复选框选项
            options_row2 = ctk.CTkFrame(options_frame)
            options_row2.pack(fill="x", padx=10, pady=5)
            
            self.include_indexes_var = tk.BooleanVar(value=True)
            include_check = ctk.CTkCheckBox(options_row2, text="包含索引", variable=self.include_indexes_var)
            include_check.pack(side="left", padx=(10, 20))
            
            self.drop_existing_var = tk.BooleanVar()
            drop_check = ctk.CTkCheckBox(options_row2, text="删除现有表", variable=self.drop_existing_var)
            drop_check.pack(side="left", padx=5)
            
            # 第三行：TINYINT转换选项
            tinyint_row = ctk.CTkFrame(options_frame)
            tinyint_row.pack(fill="x", padx=10, pady=(5, 10))
            
            self.auto_convert_tinyint_var = tk.BooleanVar(value=True)
            tinyint_check = ctk.CTkCheckBox(
                tinyint_row, 
                text="自动转换TINYINT为BOOLEAN", 
                variable=self.auto_convert_tinyint_var
            )
            tinyint_check.pack(side="left", padx=(10, 5))
            
            # 添加说明文本（CustomTkinter版本）
            help_text = ctk.CTkLabel(
                tinyint_row,
                text="(影响没有长度的TINYINT字段)",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            help_text.pack(side="left", padx=(5, 0))
        else:
            options_frame = ttk.LabelFrame(migration_frame, text="迁移选项", padding=10)
            options_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            # 第一行：批处理大小
            batch_frame = ttk.Frame(options_frame)
            batch_frame.pack(fill="x", pady=(0, 5))
            ttk.Label(batch_frame, text="批处理大小:").pack(side="left")
            self.batch_size_var = tk.StringVar(value="1000")
            ttk.Entry(batch_frame, textvariable=self.batch_size_var, width=10).pack(side="left", padx=(5, 10))
            
            # 第二行：复选框选项
            self.include_indexes_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="包含索引", variable=self.include_indexes_var).pack(anchor="w", pady=2)
            
            self.drop_existing_var = tk.BooleanVar()
            ttk.Checkbutton(options_frame, text="删除现有表", variable=self.drop_existing_var).pack(anchor="w", pady=2)
            
            # 添加tinyint转换选项（默认勾选）
            self.auto_convert_tinyint_var = tk.BooleanVar(value=True)
            tinyint_frame = ttk.Frame(options_frame)
            tinyint_frame.pack(fill="x", pady=2)
            
            ttk.Checkbutton(
                tinyint_frame, 
                text="自动转换没有长度的TINYINT为BOOLEAN类型", 
                variable=self.auto_convert_tinyint_var
            ).pack(anchor="w")
            
            # 添加说明标签
            help_label = ttk.Label(
                tinyint_frame, 
                text="说明: TINYINT(1)始终转换为BOOLEAN，此选项影响没有长度的TINYINT字段", 
                font=("Arial", 8),
                foreground="gray"
            )
            help_label.pack(anchor="w", padx=(20, 0))
        
        # 改进的表选择框架
        if self.use_custom_tk:
            table_frame = ctk.CTkFrame(migration_frame)
        else:
            table_frame = ttk.LabelFrame(migration_frame, text="表选择与管理", padding=10)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(2, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 第一行：表操作按钮
        if self.use_custom_tk:
            btn_frame1 = ctk.CTkFrame(table_frame)
            btn_frame1.pack(fill="x", pady=(10, 5))
        else:
            btn_frame1 = ttk.Frame(table_frame)
            btn_frame1.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # 基本操作按钮
        if self.use_custom_tk:
            refresh_btn = ctk.CTkButton(btn_frame1, text="🔄 刷新表列表", command=self.refresh_tables, width=100)
            refresh_btn.pack(side="left", padx=(10, 5))
            select_all_btn = ctk.CTkButton(btn_frame1, text="✅ 全选", command=self.select_all_tables, width=80)
            select_all_btn.pack(side="left", padx=5)
            deselect_all_btn = ctk.CTkButton(btn_frame1, text="❌ 全不选", command=self.deselect_all_tables, width=80)
            deselect_all_btn.pack(side="left", padx=5)
        else:
            ttk.Button(btn_frame1, text="🔄 刷新表列表", command=self.refresh_tables).pack(side="left", padx=(0, 5))
            ttk.Button(btn_frame1, text="✅ 全选", command=self.select_all_tables).pack(side="left", padx=5)
            ttk.Button(btn_frame1, text="❌ 全不选", command=self.deselect_all_tables).pack(side="left", padx=5)
            ttk.Button(btn_frame1, text="🔍 按模式选择", command=self.pattern_select_dialog).pack(side="left", padx=5)
            ttk.Button(btn_frame1, text="📊 表统计", command=self.show_table_stats).pack(side="left", padx=5)
        
        # 第二行：搜索和过滤
        if self.use_custom_tk:
            search_frame = ctk.CTkFrame(table_frame)
            search_frame.pack(fill="x", pady=5)
        else:
            search_frame = ttk.Frame(table_frame)
            search_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        if self.use_custom_tk:
            ctk.CTkLabel(search_frame, text="🔍 搜索表:").pack(side="left", padx=(10, 5))
            self.search_var = tk.StringVar()
            search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=200)
            search_entry.pack(side="left", padx=5)
            search_entry.bind('<KeyRelease>', self.filter_tables)
        else:
            ttk.Label(search_frame, text="🔍 搜索表:").pack(side="left", padx=(0, 5))
            self.search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
            search_entry.pack(side="left", padx=5)
            search_entry.bind('<KeyRelease>', self.filter_tables)
            
            ttk.Label(search_frame, text="显示:").pack(side="left", padx=(20, 5))
            self.show_filter_var = tk.StringVar(value="all")
            show_combo = ttk.Combobox(search_frame, textvariable=self.show_filter_var, 
                                    values=["all", "selected", "unselected", "large", "small", "empty"], width=10, state="readonly")
            show_combo.pack(side="left", padx=5)
            show_combo.bind('<<ComboboxSelected>>', self.filter_tables)
        
        # 第三行：表列表（使用Treeview显示更多信息）
        if self.use_custom_tk:
            # 简化版本，继续使用Listbox
            self.table_listbox = tk.Listbox(table_frame, selectmode=tk.MULTIPLE)
            self.table_listbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        else:
            list_frame = ttk.Frame(table_frame)
            list_frame.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
            list_frame.grid_rowconfigure(0, weight=1)
            list_frame.grid_columnconfigure(0, weight=1)
            
            # 使用Treeview替代Listbox以显示更多信息
            columns = ('table', 'rows', 'size', 'columns')
            self.table_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', selectmode='extended')
            
            # 设置列标题和宽度
            self.table_tree.heading('#0', text='选择', anchor='w')
            self.table_tree.heading('table', text='表名', anchor='w')
            self.table_tree.heading('rows', text='行数', anchor='e')
            self.table_tree.heading('size', text='大小', anchor='e')
            self.table_tree.heading('columns', text='列数', anchor='e')
            
            self.table_tree.column('#0', width=60, minwidth=50)
            self.table_tree.column('table', width=200, minwidth=150)
            self.table_tree.column('rows', width=100, minwidth=80)
            self.table_tree.column('size', width=100, minwidth=80)
            self.table_tree.column('columns', width=80, minwidth=60)
            
            # 添加滚动条
            tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.table_tree.yview)
            self.table_tree.configure(yscrollcommand=tree_scroll.set)
            
            self.table_tree.grid(row=0, column=0, sticky="nsew")
            tree_scroll.grid(row=0, column=1, sticky="ns")
            
            # 绑定双击事件显示表详情
            self.table_tree.bind('<Double-1>', self.show_table_details)
            
            # 添加单击事件处理checkbox式选择
            self.table_tree.bind('<Button-1>', self.on_table_click)
            
            # 存储所有表数据
            self.all_tables_data = []
        
        # 第四行：选择状态显示
        if not self.use_custom_tk:
            status_frame = ttk.Frame(table_frame)
            status_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
            
            self.table_status_label = ttk.Label(status_frame, text="📋 表: 0 | 选中: 0 | 总行数: 0")
            self.table_status_label.pack(side="left")
    
    def create_log_tab(self):
        """创建日志选项卡"""
        if self.use_custom_tk:
            log_frame = self.notebook.add("迁移日志")
        else:
            log_frame = ttk.Frame(self.notebook)
            self.notebook.add(log_frame, text="迁移日志")
        
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # 进度条
        if self.use_custom_tk:
            progress_frame = ctk.CTkFrame(log_frame)
            progress_frame.pack(fill="x", padx=10, pady=10)
            
            self.progress_label = ctk.CTkLabel(progress_frame, text="准备就绪")
            self.progress_label.pack(pady=(10, 5))
            
            self.progress_bar = ctk.CTkProgressBar(progress_frame)
            self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
            self.progress_bar.set(0)
        else:
            progress_frame = ttk.Frame(log_frame)
            progress_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            self.progress_label = ttk.Label(progress_frame, text="准备就绪")
            self.progress_label.pack(pady=(0, 5))
            
            self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
            self.progress_bar.pack(fill="x")
        
        # 日志文本区域
        if self.use_custom_tk:
            self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED)
            self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        else:
            self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
            self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    def create_control_buttons(self, parent):
        """创建控制按钮"""
        if self.use_custom_tk:
            button_frame = ctk.CTkFrame(parent)
            button_frame.grid(row=2, column=0, sticky="ew", pady=10)
            
            self.start_btn = ctk.CTkButton(
                button_frame, 
                text="开始迁移", 
                command=self.start_migration,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            self.start_btn.pack(side="left", padx=(10, 5), pady=10)
            
            self.stop_btn = ctk.CTkButton(
                button_frame, 
                text="停止迁移", 
                command=self.stop_migration,
                state="disabled"
            )
            self.stop_btn.pack(side="left", padx=5, pady=10)
            
            self.preview_btn = ctk.CTkButton(
                button_frame, 
                text="预览迁移", 
                command=self.preview_migration
            )
            self.preview_btn.pack(side="left", padx=5, pady=10)
        else:
            button_frame = ttk.Frame(parent)
            button_frame.grid(row=2, column=0, sticky="ew", pady=10)
            
            self.start_btn = ttk.Button(button_frame, text="开始迁移", command=self.start_migration)
            self.start_btn.pack(side="left", padx=(0, 5))
            
            self.stop_btn = ttk.Button(button_frame, text="停止迁移", command=self.stop_migration, state="disabled")
            self.stop_btn.pack(side="left", padx=5)
            
            self.preview_btn = ttk.Button(button_frame, text="预览迁移", command=self.preview_migration)
            self.preview_btn.pack(side="left", padx=5)
    
    def get_mysql_config(self) -> Dict[str, Any]:
        """获取MySQL配置"""
        return {
            'host': self.mysql_vars['host'].get(),
            'port': int(self.mysql_vars['port'].get() or 3306),
            'username': self.mysql_vars['username'].get(),
            'password': self.mysql_vars['password'].get(),
            'database': self.mysql_vars['database'].get()
        }
    
    def get_pg_config(self) -> Dict[str, Any]:
        """获取PostgreSQL配置"""
        return {
            'host': self.pg_vars['host'].get(),
            'port': int(self.pg_vars['port'].get() or 5432),
            'username': self.pg_vars['username'].get(),
            'password': self.pg_vars['password'].get(),
            'database': self.pg_vars['database'].get()
        }
    
    def test_connections(self):
        """测试数据库连接"""
        try:
            mysql_config = self.get_mysql_config()
            pg_config = self.get_pg_config()
            
            migrator = MySQLToPostgreSQLMigrator(
                mysql_config, 
                pg_config, 
                auto_convert_tinyint_to_bool=self.auto_convert_tinyint_var.get()
            )
            results = migrator.test_connections()
            
            # 获取配置信息
            config_info = migrator.get_config_info()
            
            message = "连接测试结果:\n"
            message += f"MySQL: {'✓ 成功' if results['mysql'] else '✗ 失败'}\n"
            message += f"PostgreSQL: {'✓ 成功' if results['postgresql'] else '✗ 失败'}\n\n"
            message += "当前配置:\n"
            message += f"批处理大小: {self.batch_size_var.get()}\n"
            message += f"包含索引: {'是' if self.include_indexes_var.get() else '否'}\n"
            message += f"TINYINT转换: {config_info['tinyint_conversion_note']}"
            
            if all(results.values()):
                messagebox.showinfo("连接测试", message)
            else:
                messagebox.showerror("连接测试", message)
        
        except Exception as e:
            messagebox.showerror("连接测试", f"测试连接时发生错误:\n{str(e)}")
    
    def refresh_tables(self):
        """刷新表列表（增强版）"""
        try:
            mysql_config = self.get_mysql_config()
            from ..connectors.mysql_connector import MySQLConnector
            
            connector = MySQLConnector(mysql_config)
            if connector.connect():
                # 获取表列表
                tables = connector.get_tables()
                
                # 获取每个表的详细信息
                self.all_tables_data = []
                total_rows = 0
                
                self.update_progress("正在获取表信息...", 0, len(tables))
                
                for i, table_name in enumerate(tables):
                    try:
                        # 获取表行数
                        rows = connector.get_table_count(table_name)
                        
                        # 获取表结构（列数）
                        structure = connector.get_table_structure(table_name)
                        columns = len(structure) if structure else 0
                        
                        # 估算表大小（简化）
                        size_mb = rows * columns * 0.001  # 粗略估算
                        if size_mb < 1:
                            size_str = f"{size_mb*1000:.0f}KB"
                        elif size_mb < 1024:
                            size_str = f"{size_mb:.1f}MB"
                        else:
                            size_str = f"{size_mb/1024:.1f}GB"
                        
                        table_info = {
                            'name': table_name,
                            'rows': rows,
                            'columns': columns,
                            'size': size_str,
                            'size_mb': size_mb
                        }
                        
                        self.all_tables_data.append(table_info)
                        total_rows += rows
                        
                        # 更新进度
                        self.update_progress(f"获取表信息: {table_name}", i+1, len(tables))
                        
                    except Exception as e:
                        print(f"获取表 {table_name} 信息时出错: {e}")
                        # 添加基本信息
                        self.all_tables_data.append({
                            'name': table_name,
                            'rows': 0,
                            'columns': 0,
                            'size': '未知',
                            'size_mb': 0
                        })
                
                connector.disconnect()
                
                # 更新GUI显示
                self.populate_table_list()
                self.update_table_status()
                
                messagebox.showinfo("刷新完成", 
                    f"找到 {len(tables)} 个表\n"
                    f"总行数: {total_rows:,}\n"
                    f"数据获取完成")
                
            else:
                messagebox.showerror("错误", "无法连接到MySQL数据库")
        
        except Exception as e:
            messagebox.showerror("错误", f"刷新表列表时发生错误:\n{str(e)}")
        finally:
            self.update_progress("准备就绪")

    def populate_table_list(self):
        """填充表列表显示"""
        if self.use_custom_tk:
            # 简化版本：使用Listbox
            self.table_listbox.delete(0, tk.END)
            for table_info in self.all_tables_data:
                display_text = f"{table_info['name']} ({table_info['rows']:,} 行)"
                self.table_listbox.insert(tk.END, display_text)
        else:
            # 增强版本：使用Treeview
            # 清空现有项目
            for item in self.table_tree.get_children():
                self.table_tree.delete(item)
            
            # 添加表数据
            for table_info in self.all_tables_data:
                self.table_tree.insert('', 'end', text='☐',
                    values=(table_info['name'], 
                           f"{table_info['rows']:,}",
                           table_info['size'],
                           table_info['columns']))

    def filter_tables(self, event=None):
        """过滤表列表"""
        if self.use_custom_tk:
            return
        
        search_text = self.search_var.get().lower()
        show_filter = self.show_filter_var.get()
        
        # 清空现有显示
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)
        
        # 过滤并显示表
        for table_info in self.all_tables_data:
            table_name = table_info['name']
            is_selected = table_name in self.selected_table_names
            
            # 应用搜索过滤
            if search_text and search_text not in table_name.lower():
                continue
            
            # 应用显示过滤
            if show_filter == "selected" and not is_selected:
                continue
            elif show_filter == "unselected" and is_selected:
                continue
            elif show_filter == "large" and table_info['rows'] < 10000:
                continue
            elif show_filter == "small" and table_info['rows'] >= 10000:
                continue
            elif show_filter == "empty" and table_info['rows'] > 0:
                continue
            
            # 添加表项
            item_id = self.table_tree.insert('', 'end', text='☐',
                   values=(table_info['name'], 
                          f"{table_info['rows']:,}",
                          table_info['size'],
                          table_info['columns']))
        
        self.update_selection_marks()
        self.update_table_status()

    def get_selected_tables(self):
        """获取选中的表"""
        if self.use_custom_tk:
            # 获取列表框选中的项目
            selection = self.table_listbox.curselection()
            selected_tables = []
            for index in selection:
                table_name = self.table_listbox.get(index)
                selected_tables.append(table_name)
            return selected_tables
        else:
            # 使用独立维护的选择状态
            return list(self.selected_table_names)

    def select_all_tables(self):
        """全选表"""
        if self.use_custom_tk:
            self.table_listbox.select_set(0, tk.END)
        else:
            # 选择所有显示的表
            self.selected_table_names.clear()
            for item in self.table_tree.get_children():
                table_name = self.table_tree.item(item)['values'][0]
                self.selected_table_names.add(table_name)
            
            self.update_selection_marks()
            self.update_table_status()

    def deselect_all_tables(self):
        """取消全选表"""
        if self.use_custom_tk:
            self.table_listbox.selection_clear(0, tk.END)
        else:
            # 清空所有选择
            self.selected_table_names.clear()
            self.update_selection_marks()
            self.update_table_status()

    def update_table_status(self):
        """更新表选择状态显示"""
        if self.use_custom_tk:
            return
        
        total_tables = len(self.all_tables_data)
        selected_tables = self.get_selected_tables()
        selected_count = len(selected_tables)
        
        # 计算选中表的总行数
        total_rows = 0
        for table_info in self.all_tables_data:
            if table_info['name'] in selected_tables:
                total_rows += table_info['rows']
        
        status_text = f"📋 表: {total_tables} | 选中: {selected_count} | 选中表行数: {total_rows:,}"
        self.table_status_label.configure(text=status_text)

    def pattern_select_dialog(self):
        """按模式选择表对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("按模式选择表")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # 使对话框居中
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 模式输入
        pattern_frame = ttk.Frame(dialog)
        pattern_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(pattern_frame, text="选择模式 (支持通配符 * 和 ?):").pack(anchor="w")
        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(pattern_frame, textvariable=pattern_var, width=40)
        pattern_entry.pack(fill="x", pady=(5, 0))
        pattern_entry.focus()
        
        # 示例
        ttk.Label(pattern_frame, text="示例: user_*, order_*, *_log", foreground="gray").pack(anchor="w", pady=(2, 0))
        
        # 匹配预览
        preview_frame = ttk.LabelFrame(dialog, text="匹配预览")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        preview_listbox = tk.Listbox(preview_frame)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_listbox.yview)
        preview_listbox.configure(yscrollcommand=preview_scroll.set)
        
        preview_listbox.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")
        
        def update_preview(*args):
            pattern = pattern_var.get()
            preview_listbox.delete(0, tk.END)
            
            if pattern:
                import fnmatch
                matched_tables = []
                for table_info in self.all_tables_data:
                    if fnmatch.fnmatch(table_info['name'], pattern):
                        matched_tables.append(table_info['name'])
                        preview_listbox.insert(tk.END, table_info['name'])
                
                if matched_tables:
                    preview_listbox.insert(0, f"--- 匹配到 {len(matched_tables)} 个表 ---")
        
        pattern_var.trace('w', update_preview)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def apply_pattern():
            pattern = pattern_var.get()
            if pattern:
                # 先清空选择
                self.deselect_all_tables()
                
                # 选择匹配的表
                import fnmatch
                for table_info in self.all_tables_data:
                    if fnmatch.fnmatch(table_info['name'], pattern):
                        self.selected_table_names.add(table_info['name'])
                
                # 重新填充列表以显示更新的选择状态
                self.update_selection_marks()
                self.update_table_status()
                dialog.destroy()
        
        ttk.Button(button_frame, text="应用", command=apply_pattern).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side="right")

    def show_table_stats(self):
        """显示表统计信息"""
        if not self.all_tables_data:
            messagebox.showwarning("提示", "请先刷新表列表")
            return
        
        # 计算统计信息
        total_tables = len(self.all_tables_data)
        total_rows = sum(table['rows'] for table in self.all_tables_data)
        total_size_mb = sum(table['size_mb'] for table in self.all_tables_data)
        
        # 找出最大的表
        largest_table = max(self.all_tables_data, key=lambda x: x['rows']) if self.all_tables_data else None
        
        # 统计空表
        empty_tables = [table for table in self.all_tables_data if table['rows'] == 0]
        
        message = f"📊 数据库统计信息\n\n"
        message += f"总表数: {total_tables}\n"
        message += f"总行数: {total_rows:,}\n"
        message += f"估算大小: {total_size_mb:.1f} MB\n\n"
        
        if largest_table:
            message += f"最大表: {largest_table['name']}\n"
            message += f"  行数: {largest_table['rows']:,}\n"
            message += f"  列数: {largest_table['columns']}\n\n"
        
        if empty_tables:
            message += f"空表数量: {len(empty_tables)}\n"
            if len(empty_tables) <= 5:
                message += f"空表: {', '.join([t['name'] for t in empty_tables])}\n"
            else:
                message += f"空表: {', '.join([t['name'] for t in empty_tables[:5]])} 等\n"
        
        messagebox.showinfo("表统计信息", message)

    def show_table_details(self, event):
        """显示表详细信息（双击事件）"""
        if self.use_custom_tk:
            return
        
        selection = self.table_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        table_name = self.table_tree.item(item)['values'][0]
        
        # 找到表信息
        table_info = None
        for info in self.all_tables_data:
            if info['name'] == table_name:
                table_info = info
                break
        
        if not table_info:
            return
        
        # 显示详细信息对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"表详情: {table_name}")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 基本信息
        info_frame = ttk.LabelFrame(dialog, text="基本信息")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"表名: {table_info['name']}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"行数: {table_info['rows']:,}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"列数: {table_info['columns']}").pack(anchor="w", padx=10, pady=2)
        ttk.Label(info_frame, text=f"估算大小: {table_info['size']}").pack(anchor="w", padx=10, pady=2)
        
        # 表结构信息
        structure_frame = ttk.LabelFrame(dialog, text="表结构")
        structure_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 获取表结构
        try:
            mysql_config = self.get_mysql_config()
            from ..connectors.mysql_connector import MySQLConnector
            
            connector = MySQLConnector(mysql_config)
            if connector.connect():
                structure = connector.get_table_structure(table_name)
                connector.disconnect()
                
                if structure:
                    # 创建表格显示结构
                    columns = ('field', 'type', 'null', 'key', 'default')
                    tree = ttk.Treeview(structure_frame, columns=columns, show='headings')
                    
                    tree.heading('field', text='字段名')
                    tree.heading('type', text='类型')
                    tree.heading('null', text='允许NULL')
                    tree.heading('key', text='键')
                    tree.heading('default', text='默认值')
                    
                    tree.column('field', width=120)
                    tree.column('type', width=100)
                    tree.column('null', width=80)
                    tree.column('key', width=60)
                    tree.column('default', width=100)
                    
                    for field_info in structure:
                        tree.insert('', 'end', values=(
                            field_info.get('Field', ''),
                            field_info.get('Type', ''),
                            field_info.get('Null', ''),
                            field_info.get('Key', ''),
                            field_info.get('Default', '')
                        ))
                    
                    tree.pack(fill="both", expand=True, padx=5, pady=5)
                else:
                    ttk.Label(structure_frame, text="无法获取表结构").pack(padx=10, pady=10)
            else:
                ttk.Label(structure_frame, text="无法连接到数据库").pack(padx=10, pady=10)
        
        except Exception as e:
            ttk.Label(structure_frame, text=f"获取表结构时出错: {str(e)}").pack(padx=10, pady=10)
        
        # 关闭按钮
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def start_migration(self):
        """开始迁移"""
        if self.is_migrating:
            return
        
        try:
            # 验证配置
            mysql_config = self.get_mysql_config()
            pg_config = self.get_pg_config()
            
            if not mysql_config['database'] or not pg_config['database']:
                messagebox.showerror("错误", "请填写数据库名称")
                return
            
            # 获取选中的表
            selected_tables = self.get_selected_tables()
            if not selected_tables:
                if not messagebox.askyesno("确认", "未选择表，是否迁移所有表？"):
                    return
                selected_tables = None
            
            # 清空日志
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state=tk.DISABLED)
            
            # 创建迁移器
            self.migrator = MySQLToPostgreSQLMigrator(
                mysql_config, 
                pg_config, 
                auto_convert_tinyint_to_bool=self.auto_convert_tinyint_var.get()
            )
            self.migrator.set_progress_callback(self.progress_callback)
            
            # 获取批处理大小
            try:
                batch_size = int(self.batch_size_var.get())
            except ValueError:
                batch_size = 1000
            
            # 开始迁移线程
            self.is_migrating = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            self.migration_thread = threading.Thread(
                target=self.run_migration,
                args=(selected_tables, batch_size, self.include_indexes_var.get())
            )
            self.migration_thread.daemon = True
            self.migration_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动迁移时发生错误:\n{str(e)}")
            self.reset_migration_state()
    
    def run_migration(self, tables, batch_size, include_indexes):
        """运行迁移（在后台线程中）"""
        try:
            results = self.migrator.migrate(tables, batch_size, include_indexes)
            
            # 在主线程中显示结果
            self.root.after(0, self.show_migration_results, results)
            
        except Exception as e:
            self.root.after(0, self.show_migration_error, str(e))
        finally:
            self.root.after(0, self.reset_migration_state)
    
    def show_migration_results(self, results):
        """显示迁移结果"""
        message = f"迁移完成!\n\n"
        message += f"总表数: {results['total_tables']}\n"
        message += f"成功: {results['migrated_tables']}\n"
        message += f"失败: {len(results['failed_tables'])}\n"
        
        if results['failed_tables']:
            message += f"\n失败的表:\n" + "\n".join(results['failed_tables'])
        
        if results['errors']:
            message += f"\n\n错误信息:\n" + "\n".join(results['errors'][:5])  # 只显示前5个错误
        
        if results['success']:
            messagebox.showinfo("迁移完成", message)
        else:
            messagebox.showerror("迁移失败", message)
    
    def show_migration_error(self, error_message):
        """显示迁移错误"""
        messagebox.showerror("迁移错误", f"迁移过程中发生错误:\n{error_message}")
    
    def reset_migration_state(self):
        """重置迁移状态"""
        self.is_migrating = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_label.configure(text="迁移完成")
    
    def stop_migration(self):
        """停止迁移"""
        if self.is_migrating and self.migration_thread:
            # 注意：实际上很难安全地停止线程，这里只是禁用按钮
            self.reset_migration_state()
            self.update_progress("用户取消迁移")
    
    def preview_migration(self):
        """预览迁移"""
        try:
            mysql_config = self.get_mysql_config()
            pg_config = self.get_pg_config()
            
            migrator = MySQLToPostgreSQLMigrator(
                mysql_config, 
                pg_config, 
                auto_convert_tinyint_to_bool=self.auto_convert_tinyint_var.get()
            )
            
            selected_tables = self.get_selected_tables()
            if not selected_tables:
                selected_tables = None
            
            preview = migrator.get_migration_preview(selected_tables)
            
            message = f"迁移预览:\n\n"
            message += f"表数量: {len(preview['tables'])}\n"
            message += f"总行数: {preview['total_rows']:,}\n"
            message += f"预计时间: {preview['estimated_time']} 秒\n\n"
            message += "表详情:\n"
            
            for table_info in preview['tables'][:10]:  # 只显示前10个表
                message += f"- {table_info['name']}: {table_info['rows']:,} 行, {table_info['columns']} 列\n"
            
            if len(preview['tables']) > 10:
                message += f"... 还有 {len(preview['tables']) - 10} 个表"
            
            messagebox.showinfo("迁移预览", message)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取预览信息时发生错误:\n{str(e)}")
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'mysql': {var: val.get() for var, val in self.mysql_vars.items()},
                'postgresql': {var: val.get() for var, val in self.pg_vars.items()},
                'options': {
                    'batch_size': self.batch_size_var.get(),
                    'include_indexes': self.include_indexes_var.get(),
                    'drop_existing': self.drop_existing_var.get(),
                    'auto_convert_tinyint_to_bool': self.auto_convert_tinyint_var.get()
                }
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("保存成功", f"配置已保存到: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时发生错误:\n{str(e)}")
    
    def load_config_file(self):
        """加载配置文件"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载MySQL配置
                if 'mysql' in config:
                    for var, val in config['mysql'].items():
                        if var in self.mysql_vars:
                            self.mysql_vars[var].set(val)
                
                # 加载PostgreSQL配置
                if 'postgresql' in config:
                    for var, val in config['postgresql'].items():
                        if var in self.pg_vars:
                            self.pg_vars[var].set(val)
                
                # 加载选项
                if 'options' in config:
                    options = config['options']
                    if 'batch_size' in options:
                        self.batch_size_var.set(options['batch_size'])
                    if 'include_indexes' in options:
                        self.include_indexes_var.set(options['include_indexes'])
                    if 'drop_existing' in options:
                        self.drop_existing_var.set(options['drop_existing'])
                    if 'auto_convert_tinyint_to_bool' in options:
                        self.auto_convert_tinyint_var.set(options['auto_convert_tinyint_to_bool'])
                
                messagebox.showinfo("加载成功", f"配置已从 {filename} 加载")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置时发生错误:\n{str(e)}")
    
    def load_config(self):
        """加载默认配置"""
        config_file = os.path.join(os.path.expanduser("~"), ".db_migrator_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 只加载非敏感信息
                if 'mysql' in config:
                    for var in ['host', 'port', 'username', 'database']:
                        if var in config['mysql'] and var in self.mysql_vars:
                            self.mysql_vars[var].set(config['mysql'][var])
                
                if 'postgresql' in config:
                    for var in ['host', 'port', 'username', 'database']:
                        if var in config['postgresql'] and var in self.pg_vars:
                            self.pg_vars[var].set(config['postgresql'][var])
            
            except Exception:
                pass  # 忽略加载错误
    
    def progress_callback(self, message: str, current: int = 0, total: int = 0):
        """进度回调函数"""
        self.root.after(0, self.update_progress, message, current, total)
    
    def update_progress(self, message: str, current: int = 0, total: int = 0):
        """更新进度显示"""
        self.progress_label.configure(text=message)
        
        if total > 0:
            progress = current / total
            if self.use_custom_tk:
                self.progress_bar.set(progress)
            else:
                self.progress_bar['value'] = progress * 100
        
        # 过滤和格式化日志消息
        display_message = self._format_log_message(message, current, total)
        
        if display_message:  # 只显示非空消息
            # 添加到日志
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, display_message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
    
    def _format_log_message(self, message: str, current: int = 0, total: int = 0):
        """格式化日志消息，过滤重复和无用信息"""
        # 跳过某些重复的消息
        skip_patterns = [
            r"^  已迁移: \w+$",  # 跳过旧式的简单进度消息
            r"^  已迁移: channels$",  # 跳过重复的channels消息
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, message):
                return None
        
        # 格式化时间戳
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 为不同类型的消息添加不同的格式
        if message.startswith("开始迁移"):
            return f"[{timestamp}] 🚀 {message}"
        elif "处理表:" in message:
            return f"[{timestamp}] 📋 {message}"
        elif message.startswith("  ✓"):
            return f"[{timestamp}] ✅ {message.strip()}"
        elif message.startswith("  ✗"):
            return f"[{timestamp}] ❌ {message.strip()}"
        elif message.startswith("  ⏳"):
            # 进度消息，添加进度条
            if current > 0 and total > 0:
                percent = (current / total) * 100
                bar_length = 20
                filled_length = int(bar_length * current // total)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                return f"[{timestamp}] {message.strip()} [{bar}]"
            else:
                return f"[{timestamp}] {message.strip()}"
        elif message.startswith("迁移完成"):
            return f"[{timestamp}] 🎉 {message}"
        elif "错误" in message or "失败" in message:
            return f"[{timestamp}] ⚠️ {message}"
        else:
            return f"[{timestamp}] ℹ️ {message}"
    
    def on_table_click(self, event):
        """表点击事件处理 - 实现checkbox式选择"""
        if self.use_custom_tk:
            return
        
        # 获取点击的项目
        item = self.table_tree.identify_row(event.y)
        if not item:
            return
        
        # 获取表名
        values = self.table_tree.item(item)['values']
        if not values:
            return
        table_name = values[0]
        
        # 切换选择状态
        if table_name in self.selected_table_names:
            # 取消选择
            self.selected_table_names.discard(table_name)
        else:
            # 添加选择
            self.selected_table_names.add(table_name)
        
        # 更新显示
        self.update_selection_marks()
        self.update_table_status()
        
        # 阻止默认的Treeview选择行为
        return "break"

    def update_selection_marks(self):
        """更新表列表中的选择标记"""
        if self.use_custom_tk:
            return
        
        # 更新所有项目的选择标记
        for item in self.table_tree.get_children():
            table_name = self.table_tree.item(item)['values'][0]
            check_mark = '☑' if table_name in self.selected_table_names else '☐'
            self.table_tree.item(item, text=check_mark)

    def run(self):
        """运行GUI"""
        # 保存配置到默认位置（退出时）
        def on_closing():
            try:
                config = {
                    'mysql': {var: val.get() if var != 'password' else '' 
                             for var, val in self.mysql_vars.items()},
                    'postgresql': {var: val.get() if var != 'password' else '' 
                                  for var, val in self.pg_vars.items()}
                }
                
                config_file = os.path.join(os.path.expanduser("~"), ".db_migrator_config.json")
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception:
                pass  # 忽略保存错误
            
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建并运行GUI
    app = MigratorGUI()
    app.run() 