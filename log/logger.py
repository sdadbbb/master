import logging
import os
from datetime import datetime

from util.file_util import FileUtil


class LoggerUtil:
    """日志工具类"""

    _logger = None

    @staticmethod
    def get_logger(log_dir=None, log_level=logging.INFO):
        """
        获取日志记录器实例
        :param log_dir: 日志文件存放目录
        :param log_level: 日志级别
        :return: logger 实例
        """
        if LoggerUtil._logger is not None:
            return LoggerUtil._logger
        if log_dir is None:
            log_dir = FileUtil.get_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'test_{timestamp}.log')

        logger = logging.getLogger('TestLogger')
        logger.setLevel(log_level)

        if logger.handlers:
            return logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        LoggerUtil._logger = logger

        logger.info(f"=" * 50)
        logger.info(f"测试开始 - 日志文件：{log_file}")
        logger.info(f"=" * 50)

        return logger

    @staticmethod
    def debug(msg):
        """输出 DEBUG 级别日志"""
        logger = LoggerUtil.get_logger()
        logger.debug(msg)

    @staticmethod
    def info(msg):
        """输出 INFO 级别日志"""
        logger = LoggerUtil.get_logger()
        logger.info(msg)

    @staticmethod
    def warning(msg):
        """输出 WARNING 级别日志"""
        logger = LoggerUtil.get_logger()
        logger.warning(msg)

    @staticmethod
    def error(msg):
        """输出 ERROR 级别日志"""
        logger = LoggerUtil.get_logger()
        logger.error(msg)

    @staticmethod
    def critical(msg):
        """输出 CRITICAL 级别日志"""
        logger = LoggerUtil.get_logger()
        logger.critical(msg)
