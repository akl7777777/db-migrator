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
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 迁移器实例
        self.migrator: Optional[MySQLToPostgreSQLMigrator] = None
        self.migration_thread: Optional[threading.Thread] = None
        self.is_migrating = False
        
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
        """创建迁移选项卡"""
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
        else:
            options_frame = ttk.LabelFrame(migration_frame, text="迁移选项", padding=10)
        options_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # 批处理大小
        if self.use_custom_tk:
            batch_label = ctk.CTkLabel(options_frame, text="批处理大小:")
            batch_label.pack(anchor="w", padx=10, pady=(10, 0))
            
            self.batch_size_var = tk.StringVar(value='1000')
            batch_entry = ctk.CTkEntry(options_frame, textvariable=self.batch_size_var)
            batch_entry.pack(fill="x", padx=10, pady=(0, 10))
        else:
            batch_frame = ttk.Frame(options_frame)
            batch_frame.pack(fill="x", pady=5)
            ttk.Label(batch_frame, text="批处理大小:").pack(side="left")
            self.batch_size_var = tk.StringVar(value='1000')
            ttk.Entry(batch_frame, textvariable=self.batch_size_var, width=10).pack(side="right")
        
        # 选项复选框
        self.include_indexes_var = tk.BooleanVar(value=True)
        self.drop_existing_var = tk.BooleanVar(value=True)
        
        if self.use_custom_tk:
            ctk.CTkCheckBox(options_frame, text="包含索引迁移", variable=self.include_indexes_var).pack(anchor="w", padx=10, pady=5)
            ctk.CTkCheckBox(options_frame, text="删除现有表", variable=self.drop_existing_var).pack(anchor="w", padx=10, pady=(0, 10))
        else:
            ttk.Checkbutton(options_frame, text="包含索引迁移", variable=self.include_indexes_var).pack(anchor="w", pady=2)
            ttk.Checkbutton(options_frame, text="删除现有表", variable=self.drop_existing_var).pack(anchor="w", pady=2)
        
        # 表选择框架
        if self.use_custom_tk:
            table_frame = ctk.CTkFrame(migration_frame)
        else:
            table_frame = ttk.LabelFrame(migration_frame, text="表选择", padding=10)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 表选择按钮
        if self.use_custom_tk:
            table_btn_frame = ctk.CTkFrame(table_frame)
            table_btn_frame.pack(fill="x", pady=(10, 10))
            
            refresh_btn = ctk.CTkButton(table_btn_frame, text="刷新表列表", command=self.refresh_tables)
            refresh_btn.pack(side="left", padx=(10, 5))
            
            select_all_btn = ctk.CTkButton(table_btn_frame, text="全选", command=self.select_all_tables)
            select_all_btn.pack(side="left", padx=5)
            
            deselect_all_btn = ctk.CTkButton(table_btn_frame, text="全不选", command=self.deselect_all_tables)
            deselect_all_btn.pack(side="left", padx=5)
        else:
            table_btn_frame = ttk.Frame(table_frame)
            table_btn_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
            
            ttk.Button(table_btn_frame, text="刷新表列表", command=self.refresh_tables).pack(side="left", padx=(0, 5))
            ttk.Button(table_btn_frame, text="全选", command=self.select_all_tables).pack(side="left", padx=5)
            ttk.Button(table_btn_frame, text="全不选", command=self.deselect_all_tables).pack(side="left", padx=5)
        
        # 表列表
        if self.use_custom_tk:
            self.table_listbox = tk.Listbox(table_frame, selectmode=tk.MULTIPLE)
            self.table_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        else:
            list_frame = ttk.Frame(table_frame)
            list_frame.grid(row=1, column=0, sticky="nsew")
            list_frame.grid_rowconfigure(0, weight=1)
            list_frame.grid_columnconfigure(0, weight=1)
            
            self.table_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.table_listbox.yview)
            self.table_listbox.configure(yscrollcommand=scrollbar.set)
            
            self.table_listbox.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
    
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
            
            migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
            results = migrator.test_connections()
            
            message = "连接测试结果:\n"
            message += f"MySQL: {'✓ 成功' if results['mysql'] else '✗ 失败'}\n"
            message += f"PostgreSQL: {'✓ 成功' if results['postgresql'] else '✗ 失败'}"
            
            if all(results.values()):
                messagebox.showinfo("连接测试", message)
            else:
                messagebox.showerror("连接测试", message)
        
        except Exception as e:
            messagebox.showerror("连接测试", f"测试连接时发生错误:\n{str(e)}")
    
    def refresh_tables(self):
        """刷新表列表"""
        try:
            mysql_config = self.get_mysql_config()
            from ..connectors.mysql_connector import MySQLConnector
            
            connector = MySQLConnector(mysql_config)
            if connector.connect():
                tables = connector.get_tables()
                connector.disconnect()
                
                self.table_listbox.delete(0, tk.END)
                for table in tables:
                    self.table_listbox.insert(tk.END, table)
                
                messagebox.showinfo("刷新完成", f"找到 {len(tables)} 个表")
            else:
                messagebox.showerror("错误", "无法连接到MySQL数据库")
        
        except Exception as e:
            messagebox.showerror("错误", f"刷新表列表时发生错误:\n{str(e)}")
    
    def select_all_tables(self):
        """全选表"""
        self.table_listbox.select_set(0, tk.END)
    
    def deselect_all_tables(self):
        """全不选表"""
        self.table_listbox.selection_clear(0, tk.END)
    
    def get_selected_tables(self):
        """获取选中的表"""
        selection = self.table_listbox.curselection()
        return [self.table_listbox.get(i) for i in selection]
    
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
        
        # 添加到日志
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
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
            self.migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
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
            
            migrator = MySQLToPostgreSQLMigrator(mysql_config, pg_config)
            
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
                    'drop_existing': self.drop_existing_var.get()
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