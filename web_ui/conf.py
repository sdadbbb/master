"""
Web UI 配置模块
统一管理共享对象，避免循环导入
"""
from multiprocessing import Manager
from log.logger import LoggerUtil
from util.file_util import FileUtil

logger = LoggerUtil.get_logger()
REPORT_DIR = FileUtil.get_report_dir()

_manager = Manager()
running_tasks = _manager.dict()
