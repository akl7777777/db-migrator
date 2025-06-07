"""
Database Migrator Package
A universal database migration tool supporting multiple database systems.
"""

__version__ = "1.0.0"
__author__ = "DB Migrator Team"
__email__ = "contact@dbmigrator.com"

from .core.base_connector import BaseConnector
from .core.type_mapper import TypeMapper

__all__ = [
    "BaseConnector",
    "TypeMapper",
] 