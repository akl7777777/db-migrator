"""
cli/commands.py - 命令行接口
"""

import click
import yaml
import sys
import os
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
import time

from ..core.migration_manager import MigrationManager
from ..utils.logger import setup_logger


console = Console()


@click.group()
@click.version_option(version='1.0.0', prog_name='db-migrator')
def cli():
    """Database Migration Tool - 支持主流数据库之间的数据迁移"""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--source', '-s', help='源数据库连接字符串')
@click.option('--target', '-t', help='目标数据库连接字符串')
@click.option('--tables', help='要迁移的表，逗号分隔')
@click.option('--exclude-tables', help='要排除的表，逗号分隔')
@click.option('--batch-size', type=int, default=1000, help='批处理大小')
@click.option('--workers', type=int, default=4, help='并发工作线程数')
@click.option('--dry-run', is_flag=True, help='模拟运行，不实际执行迁移')
@click.option('--drop-target', is_flag=True, help='删除目标表')
@click.option('--no-indexes', is_flag=True, help='不迁移索引')
@click.option('--no-foreign-keys', is_flag=True, help='不迁移外键')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              default='INFO', help='日志级别')
def migrate(config, source, target, tables, exclude_tables, batch_size, workers,
           dry_run, drop_target, no_indexes, no_foreign_keys, log_level):
    """执行数据库迁移"""

    # 设置日志
    logger = setup_logger(log_level)

    # 加载配置
    if config:
        with open(config, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    else:
        if not source or not target:
            console.print("[red]错误：必须提供配置文件或源/目标数据库连接字符串[/red]")
            sys.exit(1)

        config_data = {
            'migration': {
                'source': parse_connection_string(source),
                'target': parse_connection_string(target),
                'options': {
                    'batch_size': batch_size,
                    'workers': workers,
                    'drop_target': drop_target,
                    'migrate_indexes': not no_indexes,
                    'migrate_foreign_keys': not no_foreign_keys
                }
            }
        }

    # 处理表选项
    if tables:
        config_data['migration']['options']['tables'] = tables.split(',')
    if exclude_tables:
        config_data['migration']['options']['exclude_tables'] = exclude_tables.split(',')

    # 显示迁移信息
    display_migration_info(config_data)

    if dry_run:
        console.print("\n[yellow]模拟运行模式 - 不会实际执行迁移[/yellow]")
        return

    # 确认执行
    if not Confirm.ask("\n是否继续执行迁移？"):
        console.print("[yellow]迁移已取消[/yellow]")
        return

    # 执行迁移
    try:
        manager = MigrationManager(config_data)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在迁移...", total=None)

            # 这里应该接入实际的迁移进度回调
            result = manager.migrate()

        # 显示结果
        display_migration_result(result)

    except Exception as e:
        console.print(f"\n[red]迁移失败：{str(e)}[/red]")
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        sys.exit(1)


@cli.command()
def interactive():
    """交互式迁移向导"""
    console.print("[bold]数据库迁移向导[/bold]\n")

    # 选择源数据库类型
    source_type = Prompt.ask(
        "选择源数据库类型",
        choices=["mysql", "postgresql", "oracle", "sqlserver", "sqlite"]
    )

    # 输入源数据库连接信息
    console.print("\n[bold]源数据库连接信息[/bold]")
    source_config = {
        'type': source_type,
        'host': Prompt.ask("主机", default="localhost"),
        'port': int(Prompt.ask("端口", default=get_default_port(source_type))),
        'username': Prompt.ask("用户名"),
        'password': Prompt.ask("密码", password=True),
        'database': Prompt.ask("数据库名")
    }

    # 选择目标数据库类型
    target_type = Prompt.ask(
        "\n选择目标数据库类型",
        choices=["mysql", "postgresql", "oracle", "sqlserver", "sqlite"]
    )

    # 输入目标数据库连接信息
    console.print("\n[bold]目标数据库连接信息[/bold]")
    target_config = {
        'type': target_type,
        'host': Prompt.ask("主机", default="localhost"),
        'port': int(Prompt.ask("端口", default=get_default_port(target_type))),
        'username': Prompt.ask("用户名"),
        'password': Prompt.ask("密码", password=True),
        'database': Prompt.ask("数据库名")
    }

    # 构建配置
    config_data = {
        'migration': {
            'source': source_config,
            'target': target_config,
            'options': {}
        }
    }

    # 测试连接
    console.print("\n[yellow]测试数据库连接...[/yellow]")
    try:
        manager = MigrationManager(config_data)
        source_tables = manager.get_source_tables()
        console.print(f"[green]✓ 成功连接到源数据库，发现 {len(source_tables)} 个表[/green]")
    except Exception as e:
        console.print(f"[red]✗ 连接失败：{str(e)}[/red]")
        return

    # 选择要迁移的表
    if Confirm.ask("\n是否选择特定的表进行迁移？（否则迁移所有表）"):
        selected_tables = select_tables_interactive(source_tables)
        config_data['migration']['options']['tables'] = selected_tables

    # 其他选项
    console.print("\n[bold]迁移选项[/bold]")
    config_data['migration']['options']['drop_target'] = Confirm.ask("是否删除目标表？", default=True)
    config_data['migration']['options']['migrate_indexes'] = Confirm.ask("是否迁移索引？", default=True)
    config_data['migration']['options']['migrate_foreign_keys'] = Confirm.ask("是否迁移外键？", default=True)
    config_data['migration']['options']['batch_size'] = int(Prompt.ask("批处理大小", default="1000"))
    config_data['migration']['options']['workers'] = int(Prompt.ask("并发线程数", default="4"))

    # 保存配置
    if Confirm.ask("\n是否保存配置文件？"):
        filename = Prompt.ask("配置文件名", default="migration_config.yaml")
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        console.print(f"[green]配置已保存到 {filename}[/green]")

    # 显示迁移信息
    display_migration_info(config_data)

    # 确认执行
    if Confirm.ask("\n是否开始迁移？"):
        # 执行迁移
        migrate.callback(
            config=None,
            source=None,
            target=None,
            tables=None,
            exclude_tables=None,
            batch_size=config_data['migration']['options']['batch_size'],
            workers=config_data['migration']['options']['workers'],
            dry_run=False,
            drop_target=config_data['migration']['options']['drop_target'],
            no_indexes=not config_data['migration']['options']['migrate_indexes'],
            no_foreign_keys=not config_data['migration']['options']['migrate_foreign_keys'],
            log_level='INFO'
        )


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True, help='配置文件路径')
def validate(config):
    """验证配置文件"""
    try:
        with open(config, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 验证配置结构
        validate_config_structure(config_data)

        # 测试数据库连接
        console.print("[yellow]测试数据库连接...[/yellow]\n")

        manager = MigrationManager(config_data)

        # 测试源数据库
        with console.status("测试源数据库连接..."):
            source_ok = manager.test_source_connection()

        if source_ok:
            console.print("[green]✓ 源数据库连接成功[/green]")
        else:
            console.print("[red]✗ 源数据库连接失败[/red]")

        # 测试目标数据库
        with console.status("测试目标数据库连接..."):
            target_ok = manager.test_target_connection()

        if target_ok:
            console.print("[green]✓ 目标数据库连接成功[/green]")
        else:
            console.print("[red]✗ 目标数据库连接失败[/red]")

        if source_ok and target_ok:
            console.print("\n[green]配置验证通过！[/green]")
        else:
            console.print("\n[red]配置验证失败！[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]配置验证失败：{str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--source', '-s', help='源数据库连接字符串')
def list_tables(config, source):
    """列出源数据库中的所有表"""
    try:
        if config:
            with open(config, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        elif source:
            config_data = {
                'migration': {
                    'source': parse_connection_string(source),
                    'target': {'type': 'dummy'}  # 只需要源数据库
                }
            }
        else:
            console.print("[red]错误：必须提供配置文件或源数据库连接字符串[/red]")
            sys.exit(1)

        manager = MigrationManager(config_data)
        tables = manager.get_source_tables()

        # 创建表格
        table = Table(title="源数据库表列表")
        table.add_column("序号", style="cyan", no_wrap=True)
        table.add_column("表名", style="magenta")
        table.add_column("行数", justify="right", style="green")
        table.add_column("大小", justify="right", style="yellow")

        for i, table_info in enumerate(tables, 1):
            size_str = format_bytes(table_info.get('size_bytes', 0))
            table.add_row(
                str(i),
                table_info['name'],
                f"{table_info.get('row_count', 0):,}",
                size_str
            )

        console.print(table)
        console.print(f"\n[bold]总计：{len(tables)} 个表[/bold]")

    except Exception as e:
        console.print(f"[red]错误：{str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', default='migration_config.yaml', help='输出文件名')
def generate_config(output):
    """生成配置文件模板"""
    template = """# 数据库迁移配置文件
migration:
  # 源数据库配置
  source:
    type: mysql  # mysql, postgresql, oracle, sqlserver, sqlite
    host: 127.0.0.1
    port: 3306
    username: root
    password: password
    database: source_db
    options:
      charset: utf8mb4
      auth_plugin: caching_sha2_password

  # 目标数据库配置
  target:
    type: postgresql
    host: 127.0.0.1
    port: 5432
    username: postgres
    password: password
    database: target_db
    options:
      sslmode: disable

  # 迁移选项
  options:
    # 要迁移的表（留空表示所有表）
    tables: []
    
    # 要排除的表
    exclude_tables: []
    
    # 批处理大小
    batch_size: 1000
    
    # 并发数
    workers: 4
    
    # 是否删除目标表
    drop_target: true
    
    # 是否迁移索引
    migrate_indexes: true
    
    # 是否迁移外键
    migrate_foreign_keys: true

  # 日志配置
  logging:
    level: INFO
    file: migration.log
"""

    with open(output, 'w', encoding='utf-8') as f:
        f.write(template)

    console.print(f"[green]配置文件模板已生成：{output}[/green]")
    console.print("\n请根据实际情况修改配置文件")


# 辅助函数
def parse_connection_string(conn_str: str) -> dict:
    """解析连接字符串"""
    # 格式: type://username:password@host:port/database
    import re
    pattern = r'(\w+)://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, conn_str)

    if not match:
        raise ValueError(f"无效的连接字符串格式：{conn_str}")

    return {
        'type': match.group(1),
        'username': match.group(2),
        'password': match.group(3),
        'host': match.group(4),
        'port': int(match.group(5)),
        'database': match.group(6)
    }


def get_default_port(db_type: str) -> str:
    """获取数据库默认端口"""
    ports = {
        'mysql': '3306',
        'postgresql': '5432',
        'oracle': '1521',
        'sqlserver': '1433',
        'sqlite': 'N/A'
    }
    return ports.get(db_type, '3306')


def select_tables_interactive(tables: List[str]) -> List[str]:
    """交互式选择表"""
    console.print("\n[bold]选择要迁移的表[/bold]")
    console.print("输入表名（逗号分隔）或表名模式（支持通配符*）")
    console.print("示例：users,orders 或 user_*,order_*")
    console.print(f"可用的表：{', '.join(tables[:10])}{'...' if len(tables) > 10 else ''}")

    selection = Prompt.ask("\n请输入")
    selected = []

    for pattern in selection.split(','):
        pattern = pattern.strip()
        if '*' in pattern:
            # 通配符匹配
            import fnmatch
            selected.extend([t for t in tables if fnmatch.fnmatch(t, pattern)])
        else:
            # 精确匹配
            if pattern in tables:
                selected.append(pattern)

    return list(set(selected))  # 去重


def display_migration_info(config_data: dict):
    """显示迁移信息"""
    migration = config_data['migration']

    console.print("\n[bold]迁移配置信息[/bold]")
    console.print(f"源数据库：{migration['source']['type']}://{migration['source']['host']}:{migration['source']['port']}/{migration['source']['database']}")
    console.print(f"目标数据库：{migration['target']['type']}://{migration['target']['host']}:{migration['target']['port']}/{migration['target']['database']}")

    options = migration.get('options', {})
    if options.get('tables'):
        console.print(f"迁移表：{', '.join(options['tables'])}")
    else:
        console.print("迁移表：全部")

    if options.get('exclude_tables'):
        console.print(f"排除表：{', '.join(options['exclude_tables'])}")


def display_migration_result(result: dict):
    """显示迁移结果"""
    console.print("\n[bold]迁移完成！[/bold]\n")

    # 创建结果表格
    table = Table(title="迁移结果汇总")
    table.add_column("表名", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("行数", justify="right")
    table.add_column("耗时", justify="right")
    table.add_column("速率", justify="right")

    total_rows = 0
    total_time = 0
    success_count = 0

    for table_result in result.get('tables', []):
        status = "[green]✓ 成功[/green]" if table_result['success'] else "[red]✗ 失败[/red]"
        rows = table_result.get('rows_migrated', 0)
        time_taken = table_result.get('time_taken', 0)
        rate = f"{rows / time_taken:.0f} 行/秒" if time_taken > 0 else "N/A"

        table.add_row(
            table_result['name'],
            status,
            f"{rows:,}",
            f"{time_taken:.2f}s",
            rate
        )

        if table_result['success']:
            success_count += 1
            total_rows += rows
            total_time += time_taken

    console.print(table)

    # 显示汇总信息
    console.print(f"\n[bold]汇总信息：[/bold]")
    console.print(f"成功表数：{success_count}/{len(result.get('tables', []))}")
    console.print(f"总行数：{total_rows:,}")
    console.print(f"总耗时：{format_duration(total_time)}")
    console.print(f"平均速率：{total_rows / total_time:.0f} 行/秒" if total_time > 0 else "")

    # 显示错误信息
    if result.get('errors'):
        console.print("\n[red][bold]错误信息：[/bold][/red]")
        for error in result['errors']:
            console.print(f"[red]- {error}[/red]")


def format_bytes(size: int) -> str:
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}小时"


def validate_config_structure(config_data: dict):
    """验证配置文件结构"""
    required_fields = {
        'migration': {
            'source': ['type', 'host', 'port', 'username', 'password', 'database'],
            'target': ['type', 'host', 'port', 'username', 'password', 'database']
        }
    }

    # 检查顶层结构
    if 'migration' not in config_data:
        raise ValueError("配置文件缺少 'migration' 字段")

    migration = config_data['migration']

    # 检查源和目标配置
    for db_type in ['source', 'target']:
        if db_type not in migration:
            raise ValueError(f"配置文件缺少 'migration.{db_type}' 字段")

        db_config = migration[db_type]
        for field in required_fields['migration'][db_type]:
            if field not in db_config:
                raise ValueError(f"配置文件缺少 'migration.{db_type}.{field}' 字段")


if __name__ == '__main__':
    cli()