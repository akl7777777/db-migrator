"""
base_connector.py - 数据库连接器基类
定义了所有数据库连接器必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class TableInfo:
    """表信息数据类"""
    name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    indexes: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    row_count: int
    size_bytes: Optional[int] = None
    comment: Optional[str] = None


@dataclass
class ColumnInfo:
    """列信息数据类"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Any
    is_primary_key: bool
    is_unique: bool
    is_auto_increment: bool
    max_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    comment: Optional[str] = None


class BaseConnector(ABC):
    """数据库连接器基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化连接器

        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.connection = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def connect(self) -> None:
        """建立数据库连接"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开数据库连接"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试数据库连接是否正常"""
        pass

    @abstractmethod
    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        获取所有表名

        Args:
            schema: 数据库模式名，如果为None则使用默认模式

        Returns:
            表名列表
        """
        pass

    @abstractmethod
    def get_table_info(self, table_name: str, schema: Optional[str] = None) -> TableInfo:
        """
        获取表的详细信息

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            TableInfo 对象
        """
        pass

    @abstractmethod
    def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """
        获取表的列信息

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            ColumnInfo 对象列表
        """
        pass

    @abstractmethod
    def get_primary_keys(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """
        获取表的主键列

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            主键列名列表
        """
        pass

    @abstractmethod
    def get_indexes(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表的索引信息

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            索引信息字典列表
        """
        pass

    @abstractmethod
    def get_foreign_keys(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表的外键信息

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            外键信息字典列表
        """
        pass

    @abstractmethod
    def get_table_ddl(self, table_name: str, schema: Optional[str] = None) -> str:
        """
        获取创建表的 DDL 语句

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            DDL 语句
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        pass

    @abstractmethod
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """
        执行命令语句（INSERT, UPDATE, DELETE 等）

        Args:
            command: SQL 命令语句
            params: 命令参数

        Returns:
            受影响的行数
        """
        pass

    @abstractmethod
    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]],
                    schema: Optional[str] = None, batch_size: int = 1000) -> int:
        """
        批量插入数据

        Args:
            table_name: 表名
            data: 要插入的数据列表
            schema: 数据库模式名
            batch_size: 批次大小

        Returns:
            插入的行数
        """
        pass

    @abstractmethod
    def stream_query(self, query: str, params: Optional[Tuple] = None,
                     batch_size: int = 1000):
        """
        流式查询，用于处理大量数据

        Args:
            query: SQL 查询语句
            params: 查询参数
            batch_size: 每批返回的行数

        Yields:
            数据批次
        """
        pass

    @abstractmethod
    def get_row_count(self, table_name: str, schema: Optional[str] = None,
                      where_clause: Optional[str] = None) -> int:
        """
        获取表的行数

        Args:
            table_name: 表名
            schema: 数据库模式名
            where_clause: WHERE 条件

        Returns:
            行数
        """
        pass

    @abstractmethod
    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """
        检查表是否存在

        Args:
            table_name: 表名
            schema: 数据库模式名

        Returns:
            是否存在
        """
        pass

    @abstractmethod
    def drop_table(self, table_name: str, schema: Optional[str] = None,
                   cascade: bool = False) -> None:
        """
        删除表

        Args:
            table_name: 表名
            schema: 数据库模式名
            cascade: 是否级联删除
        """
        pass

    @abstractmethod
    def create_table(self, ddl: str) -> None:
        """
        创建表

        Args:
            ddl: CREATE TABLE 语句
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """开始事务"""
        pass

    @abstractmethod
    def commit_transaction(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback_transaction(self) -> None:
        """回滚事务"""
        pass

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库基本信息

        Returns:
            数据库信息字典
        """
        return {
            'type': self.__class__.__name__.replace('Connector', ''),
            'host': self.config.get('host'),
            'port': self.config.get('port'),
            'database': self.config.get('database'),
            'user': self.config.get('user', self.config.get('username'))
        }

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            self.rollback_transaction()
        self.disconnect()

    def quote_identifier(self, identifier: str) -> str:
        """
        转义标识符（表名、列名等）

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        # 子类可以覆盖此方法以实现特定的转义规则
        return f'"{identifier}"'

    def get_type_mapping(self) -> Dict[str, str]:
        """
        获取数据类型映射表

        Returns:
            类型映射字典
        """
        # 子类应该覆盖此方法
        return {}