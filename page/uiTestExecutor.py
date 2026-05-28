import os
import time
from selenium.webdriver.common.by import By
from log.logger import LoggerUtil
from page.base_page import base_page
from driver.driver_util import DriverUtil
from util.screenshot_util import ScreenshotUtil
from util.file_util import FileUtil

logger = LoggerUtil.get_logger()


class UITestExecutor:
    """UI自动化测试执行器 - 基于base_page的所有方法"""

    def __init__(self):
        self.driver = None
        self.page = None
        self.variables = {}

    def init_driver(self):
        """初始化浏览器驱动"""
        # 重置 DriverUtil 的 driver，确保每次都是新的
        driver_util = DriverUtil()
        if driver_util._driver:
            try:
                driver_util._driver.quit()
            except:
                pass
            driver_util._driver = None
        
        self.driver = driver_util.get_driver('edge')
        self.page = base_page(self.driver)

    def _build_locator(self, locator_type, locator_value):
        """构建定位器"""
        locator_map = {
            'xpath': By.XPATH,
            'id': By.ID,
            'css': By.CSS_SELECTOR,
            'class': By.CLASS_NAME,
            'name': By.NAME,
            'tag': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT
        }
        by_type = locator_map.get(locator_type.lower(), By.XPATH)
        return (by_type, locator_value)

    def _replace_variables(self, text):
        """替换变量占位符"""
        if not isinstance(text, str):
            return text
        for var_name, var_value in self.variables.items():
            placeholder = f"${{{var_name}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(var_value))
        return text

    def execute_step(self, step):
        """
        执行单个步骤 - 支持base_page的所有方法
        :param step: 步骤配置字典
        :return: (success, message)
        """
        action = step.get('action')
        params = step.get('params', {})

        logger.info(f"执行步骤: {action}")

        try:
            # 1. go_url - 访问URL
            if action == 'go_url':
                url = params.get('url', '')
                url = self._replace_variables(url)
                self.page.go_url(url)
                return True, f"访问URL: {url}"

            # 2. click_element - 点击元素
            elif action == 'click_element':
                locator = self._build_locator(
                    params.get('locator_type', 'xpath'),
                    params.get('locator_value', '')
                )
                timeout = params.get('timeout', 10)
                self.page.click_element(locator, timeout)
                return True, f"点击元素: {params.get('locator_value')}"

            # 3. input_element - 输入文本
            elif action == 'input_element':
                locator = self._build_locator(
                    params.get('locator_type', 'xpath'),
                    params.get('locator_value', '')
                )
                text = self._replace_variables(params.get('text', ''))
                timeout = params.get('timeout', 10)
                self.page.input_element(locator, text, timeout)
                return True, f"输入文本: {text}"

            # 4. input_by_placeholder - 通过placeholder输入
            elif action == 'input_by_placeholder':
                aria_label = self._replace_variables(params.get('aria_label', ''))
                placeholder = params.get('placeholder', '')
                text = self._replace_variables(params.get('text', ''))
                timeout = params.get('timeout', 10)
                self.page.input_by_placeholder(aria_label, placeholder, text, timeout)
                return True, f"在弹窗[{aria_label}]中输入: {text}"

            # 4.1 input_by_placeholder_only - 仅根据placeholder输入
            elif action == 'input_by_placeholder_only':
                placeholder = params.get('placeholder', '')
                text = self._replace_variables(params.get('text', ''))
                timeout = params.get('timeout', 10)
                self.page.input_by_placeholder_only(placeholder, text, timeout)
                return True, f"根据提示内容[{placeholder}]输入: {text}"

            # 5. get_element_text - 获取元素文本并存储到变量
            elif action == 'get_element_text':
                locator = self._build_locator(
                    params.get('locator_type', 'xpath'),
                    params.get('locator_value', '')
                )
                var_name = params.get('var_name', 'extracted_text')
                timeout = params.get('timeout', 10)
                text = self.page.get_element_text(locator, timeout)
                self.variables[var_name] = text
                return True, f"提取文本: {var_name} = {text}"

            # 6. click_button_by_text - 通过按钮文本点击
            elif action == 'click_button_by_text':
                button_text = self._replace_variables(params.get('button_text', ''))
                aria_label = params.get('aria_label')
                if aria_label:
                    aria_label = self._replace_variables(aria_label)
                timeout = params.get('timeout', 10)
                self.page.click_button_by_text(button_text, aria_label, timeout)
                return True, f"点击按钮: {button_text}"

            # 7. click_contains_text - 点击包含文本的元素
            elif action == 'click_contains_text':
                text = self._replace_variables(params.get('text', ''))
                tag_name = params.get('tag_name', '*')
                timeout = params.get('timeout', 10)
                self.page.click_contains_text(text, tag_name, timeout)
                return True, f"点击包含文本'{text}'的元素"

            # 8. find_element_by_text - 查找精确匹配文本的元素
            elif action == 'find_element_by_text':
                text = self._replace_variables(params.get('text', ''))
                tag_name = params.get('tag_name', '*')
                timeout = params.get('timeout', 10)
                element = self.page.find_element_by_text(text, tag_name, timeout)
                if element:
                    return True, f"找到精确匹配文本'{text}'的元素"
                else:
                    return False, f"未找到精确匹配文本'{text}'的元素"

            # 9. find_contains_text_element - 查找包含文本的元素
            elif action == 'find_contains_text_element':
                text = self._replace_variables(params.get('text', ''))
                tag_name = params.get('tag_name', '*')
                timeout = params.get('timeout', 10)
                element = self.page.find_contains_text_element(text, tag_name, timeout)
                if element:
                    return True, f"找到包含文本'{text}'的元素"
                else:
                    return False, f"未找到包含文本'{text}'的元素"

            # 10. find_elements_by_text - 查找所有匹配文本的元素
            elif action == 'find_elements_by_text':
                text = self._replace_variables(params.get('text', ''))
                tag_name = params.get('tag_name', '*')
                timeout = params.get('timeout', 10)
                elements = self.page.find_elements_by_text(text, tag_name, timeout)
                return True, f"找到{len(elements)}个包含文本'{text}'的元素"

            # 11. click_button_by_text_in_form - 在表单内点击按钮
            elif action == 'click_button_by_text_in_form':
                button_text = self._replace_variables(params.get('button_text', ''))
                form_locator_str = params.get('form_locator')
                timeout = params.get('timeout', 10)
                
                form_locator = None
                if form_locator_str:
                    form_locator = self._build_locator(
                        params.get('form_locator_type', 'xpath'),
                        form_locator_str
                    )
                
                self.page.click_button_by_text_in_form(button_text, form_locator, timeout)
                return True, f"在表单内点击按钮: {button_text}"

            # 12. click_button_element_by_index - 点击第N个匹配的元素
            elif action == 'click_button_element_by_index':
                button_text = self._replace_variables(params.get('button_text', ''))
                index = params.get('index', 0)
                timeout = params.get('timeout', 10)
                self.page.click_button_element_by_index(button_text, index, timeout)
                return True, f"点击第{index + 1}个按钮: {button_text}"

            # 13. check_login_result - 检查登录结果
            elif action == 'check_login_result':
                success_text = self._replace_variables(params.get('success_text', ''))
                error_texts = params.get('error_texts', [])
                error_texts = [self._replace_variables(t) for t in error_texts]
                
                result = self.page.check_login_result(success_text, error_texts)
                if result['status'] == 'success':
                    return True, f"登录成功: {result['message']}"
                else:
                    return False, f"登录失败: {result['message']}"

            # 14. wait_element - 等待元素出现
            elif action == 'wait_element':
                locator = self._build_locator(
                    params.get('locator_type', 'xpath'),
                    params.get('locator_value', '')
                )
                timeout = params.get('timeout', 10)
                self.page.wait_element(locator, timeout)
                return True, f"等待元素出现: {params.get('locator_value')}"

            # 15. wait - 固定等待
            elif action == 'wait':
                seconds = params.get('seconds', 3)
                time.sleep(seconds)
                return True, f"等待 {seconds} 秒"

            # 16. assert_text_exists - 断言文本存在
            elif action == 'assert_text_exists':
                text = self._replace_variables(params.get('text', ''))
                tag_name = params.get('tag_name', '*')
                timeout = params.get('timeout', 10)
                element = self.page.find_contains_text_element(text, tag_name, timeout)
                if element:
                    return True, f"断言成功: 文本'{text}'存在"
                else:
                    return False, f"断言失败: 文本'{text}'不存在"

            else:
                return False, f"未知的操作: {action}"

        except Exception as e:
            logger.error(f"步骤执行失败: {str(e)}")
            return False, str(e)

    def execute_case(self, case):
        """
        执行完整的测试用例
        :param case: 测试用例配置
        :return: 执行结果
        """
        # 获取截图目录
        report_dir = FileUtil.get_report_dir()
        screenshot_dir = os.path.join(report_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        result = {
            'case_id': case.get('id'),
            'case_name': case.get('name'),
            'passed': False,
            'steps_results': [],
            'error': None,
            'screenshot': None
        }

        try:
            self.init_driver()
            
            url = case.get('url', '')
            steps = case.get('steps', [])

            logger.info(f"\n{'='*60}")
            logger.info(f"开始执行UI测试: {case.get('name')}")
            logger.info(f"URL: {url}")
            logger.info(f"步骤数: {len(steps)}")
            logger.info(f"截图目录: {screenshot_dir}")

            if url:
                url = self._replace_variables(url)
                self.page.go_url(url)
                time.sleep(2)

            all_passed = True
            for i, step in enumerate(steps, 1):
                logger.info(f"\n--- 步骤 {i}/{len(steps)} ---")
                
                success, message = self.execute_step(step)
                
                step_result = {
                    'step_index': i,
                    'action': step.get('action'),
                    'action_name': self._get_action_name(step.get('action')),
                    'params': step.get('params'),
                    'passed': success,
                    'message': message
                }
                result['steps_results'].append(step_result)

                if not success:
                    all_passed = False
                    logger.error(f"步骤 {i} 失败: {message}")
                    
                    screenshot_path = ScreenshotUtil.save_screenshot(
                        self.driver, 
                        screenshot_dir=screenshot_dir,
                        filename=f"error_step_{i}_{int(time.time())}"
                    )
                    result['screenshot'] = screenshot_path
                    break
                else:
                    logger.info(f"步骤 {i} 成功: {message}")

            result['passed'] = all_passed

            if all_passed:
                logger.info(f"✅ 测试通过: {case.get('name')}")
            else:
                logger.error(f"❌ 测试失败: {case.get('name')}")

        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
            logger.error(f"测试异常: {str(e)}")
            
            try:
                screenshot_path = ScreenshotUtil.save_screenshot(
                    self.driver, 
                    screenshot_dir=screenshot_dir,
                    filename=f"error_exception_{int(time.time())}"
                )
                result['screenshot'] = screenshot_path
            except:
                pass

        finally:
            if self.driver:
                try:
                    final_screenshot = ScreenshotUtil.save_screenshot(
                        self.driver, 
                        screenshot_dir=screenshot_dir,
                        filename=f"final_{case.get('id', 'unknown')}_{int(time.time())}"
                    )
                    result['final_screenshot'] = final_screenshot
                    logger.info(f"已保存最终截图: {final_screenshot}")
                except Exception as e:
                    logger.warning(f"保存最终截图失败: {e}")
                
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"关闭 driver 失败: {e}")

        return result

    def _get_action_name(self, action):
        """获取操作的中文名称"""
        action_names = {
            'go_url': '访问URL',
            'click_element': '点击元素',
            'input_element': '输入文本',
            'input_by_placeholder': '通过Placeholder输入',
            'get_element_text': '提取元素文本',
            'click_button_by_text': '点击按钮(文本)',
            'click_contains_text': '点击包含文本',
            'find_element_by_text': '查找元素(精确)',
            'find_contains_text_element': '查找元素(包含)',
            'find_elements_by_text': '查找多个元素',
            'click_button_by_text_in_form': '表单内点击按钮',
            'click_button_element_by_index': '点击第N个按钮',
            'check_login_result': '检查登录结果',
            'wait_element': '等待元素',
            'wait': '固定等待',
            'assert_text_exists': '断言文本存在'
        }
        return action_names.get(action, action)
