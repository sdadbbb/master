"""
Web UI 配置模块
统一管理共享对象，避免循环导入
"""
import platform
from multiprocessing import Manager
from log.logger import LoggerUtil
from util.file_util import FileUtil

logger = LoggerUtil.get_logger()
REPORT_DIR = FileUtil.get_report_dir()

# 检测操作系统，Windows 需要延迟初始化 Manager 以避免多进程启动问题
_system = platform.system().lower()
_is_windows = _system == 'windows'

if _is_windows:
    # Windows: 延迟初始化，避免 spawn 模式下的递归导入问题
    _manager = None
    running_tasks = None
else:
    # Linux (openKylin等): 直接初始化，使用 fork 模式无此问题
    _manager = Manager()
    running_tasks = _manager.dict()


def get_running_tasks():
    """获取运行中的任务字典(单例模式)
    
    Windows 下首次调用时初始化 Manager，Linux 下直接返回已初始化的对象
    """
    global _manager, running_tasks
    if _is_windows and _manager is None:
        _manager = Manager()
        running_tasks = _manager.dict()
    return running_tasks
