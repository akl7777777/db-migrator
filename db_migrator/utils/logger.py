#!/usr/bin/env python3
"""
Logging utilities for database migration.
"""

import logging
import sys
from pathlib import Path


def setup_logger(level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径 (可选)
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取根日志记录器
    logger = logging.getLogger()
    
    # 清除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置日志级别
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    logger.setLevel(level_mapping.get(level.upper(), logging.INFO))
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (如果指定了日志文件)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger 