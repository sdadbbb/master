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
        
        # 总日志文件（无限追加，保存所有日志）
        all_log_file = os.path.join(log_dir, 'all.log')

        logger = logging.getLogger('TestLogger')
        logger.setLevel(log_level)

        if logger.handlers:
            return logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)

        # 总日志文件处理器（无限追加）
        all_file_handler = logging.FileHandler(all_log_file, encoding='utf-8', mode='a')
        all_file_handler.setLevel(log_level)

        # 详细格式：用于文件日志（包含文件名、行号、函数名）
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d - %(funcName)s()] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler.setFormatter(simple_formatter)
        file_handler.setFormatter(detailed_formatter)
        all_file_handler.setFormatter(detailed_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(all_file_handler)

        LoggerUtil._logger = logger

        logger.info("=" * 50)
        logger.info(f"测试开始 - 本次日志文件：{log_file}")
        logger.info(f"总日志文件：{all_log_file}")
        logger.info("=" * 50)

        return logger

    @staticmethod
    def debug(msg):
        logger = LoggerUtil.get_logger()
        logger.debug(msg)

    @staticmethod
    def info(msg):
        logger = LoggerUtil.get_logger()
        logger.info(msg)

    @staticmethod
    def warning(msg):
        logger = LoggerUtil.get_logger()
        logger.warning(msg)

    @staticmethod
    def error(msg):
        logger = LoggerUtil.get_logger()
        logger.error(msg)

    @staticmethod
    def critical(msg):
        logger = LoggerUtil.get_logger()
        logger.critical(msg)
