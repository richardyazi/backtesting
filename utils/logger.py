"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from typing import Optional


class StockCacheLogger:
    """股票缓存日志管理器"""
    
    def __init__(self, log_dir: str = "./logs", log_level: str = "INFO"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录路径
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper())
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志系统"""
        # 创建logger
        self.logger = logging.getLogger("stock_cache")
        self.logger.setLevel(self.log_level)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 文件处理器
            log_file = os.path.join(self.log_dir, f"stock_cache_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录普通信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: Optional[Exception] = None):
        """记录错误信息"""
        if exc_info:
            self.logger.error(f"{message} - {str(exc_info)}", exc_info=exc_info)
        else:
            self.logger.error(message)
    
    def exception(self, message: str):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(message)


# 全局日志实例
_logger_instance: Optional[StockCacheLogger] = None


def get_logger(log_dir: str = "./logs", log_level: str = "INFO") -> StockCacheLogger:
    """
    获取全局日志实例
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别
        
    Returns:
        StockCacheLogger: 日志管理器实例
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = StockCacheLogger(log_dir, log_level)
    
    return _logger_instance


def debug(message: str):
    """记录调试信息"""
    get_logger().debug(message)


def info(message: str):
    """记录普通信息"""
    get_logger().info(message)


def warning(message: str):
    """记录警告信息"""
    get_logger().warning(message)


def error(message: str, exc_info: Optional[Exception] = None):
    """记录错误信息"""
    get_logger().error(message, exc_info)


def exception(message: str):
    """记录异常信息"""
    get_logger().exception(message)