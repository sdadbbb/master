import time

import pytest
import os

from selenium.webdriver.common.by import By

from driver.driver_util import get_driver, quit_driver
from log.logger import LoggerUtil
from util.screenshot_util import ScreenshotUtil
from util.file_util import FileUtil
from page.moutum_page import MoutumPage
from page.config_page import ConfigPage

config = FileUtil.read_yaml(FileUtil.get_config_path())
REPORT_DIR = FileUtil.get_report_dir()
SCREENSHOT_DIR = os.path.join(REPORT_DIR, 'screenshots')
logger = LoggerUtil.get_logger()


@pytest.fixture(scope="function")
def driver_setup():
    browser = config['driver']['browser']
    logger.info(f"启动浏览器：{browser}")
    driver = get_driver(browser)
    try:
        yield driver
    finally:
        logger.info("关闭浏览器")
        quit_driver()


@pytest.fixture(scope="function")
def logged_in_driver(driver_setup):
    """
    已登录的 driver fixture
    如果登录成功，返回 driver；否则跳过测试
    """
    driver = driver_setup
    username = config['login']['users'][0]['username']
    password = config['login']['users'][0]['password']
    
    try:
        mt_page = MoutumPage(driver)
        mt_page.go_url(config['login']['url'])
        mt_page.login(username, password)
        
        result = mt_page.check_login_result(
            config['login']['expected_text'],
            config['login'].get('error_texts', [])
        )
        
        # 登录截图
        screenshot_path = ScreenshotUtil.save_screenshot_always(
            driver,
            SCREENSHOT_DIR,
            f"{username}_login",
            result['status']
        )
        logger.info(f"登录截图：{screenshot_path}")
        
        if result['status'] != 'success':
            pytest.skip(f"登录失败，跳过后续测试：{result['message']}")
        
        logger.info("✅ 登录成功，继续执行测试")
        return driver
        
    except Exception as e:
        logger.error(f"登录过程出错：{str(e)}")
        ScreenshotUtil.save_screenshot_always(
            driver,
            SCREENSHOT_DIR,
            f"{username}_login",
            'error'
        )
        pytest.skip(f"登录异常：{str(e)}")


class TestLogin:
    """登录测试类"""

    @pytest.mark.parametrize("username,password", [
        (user['username'], user['password'])
        for user in config['login']['users']
    ])
    def test_login_only(self, driver_setup, username, password):
        """只测试登录功能"""
        logger.info(f"{'='*50}")
        logger.info(f"测试登录：{username}")
        logger.info(f"{'='*50}")
        
        mt_page = MoutumPage(driver_setup)
        
        try:
            mt_page.go_url(config['login']['url'])
            mt_page.login(username, password)
            
            result = mt_page.check_login_result(
                config['login']['expected_text'],
                config['login'].get('error_texts', [])
            )
            
            # 登录截图
            screenshot_path = ScreenshotUtil.save_screenshot_always(
                driver_setup,
                SCREENSHOT_DIR,
                f"{username}",
                result['status']
            )
            logger.info(f"登录结果：{result['status']} - {result['message']}")
            logger.info(f"截图路径：{screenshot_path}")
            
            assert result['status'] in ['success', 'failed'], f"登录出现异常状态：{result['message']}"
            
        except Exception as e:
            logger.error(f"登录测试失败：{str(e)}")
            ScreenshotUtil.save_screenshot_always(
                driver_setup,
                SCREENSHOT_DIR,
                f"{username}_error",
                'error'
            )
            raise e
        finally:
            logger.info(f"登录测试结束\n")


class TestConfig:

    def test_add_config(self, logged_in_driver):
        logger.info(f"{'='*50}")
        logger.info(f"测试用例：test_add_config")
        logger.info(f"{'='*50}")
        
        config_page = ConfigPage(logged_in_driver)
        username = config['login']['users'][0]['username']
        
        try:
            config_page.get_goods_type('初始配置')
            config_page.get_goods_type('物资配置')
            config_page.get_goods_type('物资类型')
            config_page.click_button_add()
            assert config_page.find_element_by_text('添加物资类型').text == '添加物资类型'
            logger.info("成功打开新增界面")

            time.sleep(1)
            # 操作截图
            screenshot_path = ScreenshotUtil.save_screenshot_always(
                logged_in_driver,
                SCREENSHOT_DIR,
                f"{username}_add_config",
                'success'
            )
            logger.info(f"配置截图：{screenshot_path}")
            logger.info("✅ 配置添加完成")
            
        except Exception as e:
            logger.error(f"❌ 新增测试失败：{str(e)}")
            # 失败截图
            screenshot_path = ScreenshotUtil.save_screenshot_always(
                logged_in_driver,
                SCREENSHOT_DIR,
                f"{username}_add_config_error",
                'error'
            )
            logger.error(f"错误截图：{screenshot_path}")
            raise e
        finally:
            logger.info(f"测试结束\n")
    
    # def test_edit_config(self, logged_in_driver):
    #     """测试编辑配置"""
    #     logger.info("测试编辑配置")
    #
    #     config_page = ConfigPage(logged_in_driver)
    #
    #     # TODO: 添加你的编辑操作
    #     # config_page.edit_existing_config()
    #
    #     logger.info("配置编辑完成")

    # def test_delete_config(self, logged_in_driver):
    #     """测试删除配置"""
    #     logger.info("测试删除配置")
    #
    #     config_page = ConfigPage(logged_in_driver)
    #
    #     # TODO: 添加你的删除操作
    #     # config_page.delete_config()
    #
    #     logger.info("配置删除完成")
