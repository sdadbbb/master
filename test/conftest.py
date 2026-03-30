import pytest
import os

from log.logger import LoggerUtil
from util.file_util import FileUtil



# 全局配置
CONFIG = FileUtil.read_yaml(FileUtil.get_config_path())
REPORT_DIR = FileUtil.get_report_dir()
SCREENSHOT_DIR = os.path.join(REPORT_DIR, 'screenshots')
LOG_DIR = FileUtil.get_log_dir()

# 确保目录存在
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def global_setup():
    """全局前置处理"""
    LoggerUtil.info("测试套件开始执行")
    yield
    LoggerUtil.info("测试套件执行完毕")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获测试结果"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call':
        if report.passed:
            LoggerUtil.info(f"✅ 测试通过：{item.name}")
        elif report.failed:
            LoggerUtil.error(f"❌ 测试失败：{item.name}")
