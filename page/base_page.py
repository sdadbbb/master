import time

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()


class base_page:
    def __init__(self, driver):
        self.driver = driver

    def go_url(self, url):
        self.driver.get(url)

    def wait_element(self, locator, timeout=10):
        """
        :param locator: 元素定位器，主要为解决元素定位
        :param timeout: 等待时间
        :return:element
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(ec.visibility_of_element_located(locator))
            return element
        except TimeoutException:
            raise TimeoutException(f"元素{locator}超时未找到")

    def wait_elements(self, locator, timeout=10):
        """
        等待多个元素出现
        :param locator: 元素定位器
        :param timeout: 等待时间
        :return: 元素列表
        """
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_all_elements_located(locator)
            )
            return elements
        except TimeoutException:
            raise TimeoutException(f"元素{locator}超时未找到")

    def click_element(self, locator, timeout=10):
        element = self.wait_element(locator, timeout)
        element.click()

    def input_element(self, locator, text, timeout=10):
        element = self.wait_element(locator, timeout)
        element.clear()
        element.send_keys(text)

    def get_element_text(self, locator, timeout=10):
        element = self.wait_element(locator, timeout)
        return element.text

    def click_button_by_text(self, button_text, timeout=10):
        """
        根据按钮文本点击按钮（支持多种标签类型）
        :param button_text: 按钮上显示的文本
        :param timeout: 等待超时时间（秒）
        """
        locators = [
            (By.XPATH, f"//button[contains(., '{button_text}')]"),
            # button 标签，包含文本
            (By.XPATH, f"//button[contains(text(), '{button_text}')]"),
            # input type=button，value 属性匹配
            (By.XPATH, f"//input[@type='button' and @value='{button_text}']"),
            # a 标签，当作按钮使用
            (By.XPATH, f"//a[text()='{button_text}']"),
            # 任何包含按钮文本的元素（通用）
            (By.XPATH, f"//*[text()='{button_text}' and contains(@class, 'btn')]"),
            # 通过 aria-label 查找
            (By.XPATH, f"//*[@aria-label='{button_text}']"),
            # 通过 title 属性查找
            (By.XPATH, f"//*[@title='{button_text}']"),
        ]

        # 依次尝试每个定位器
        for locator in locators:
            try:
                element = self.wait_element(locator, timeout=2)
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    logger.info(f"✅ 成功点击按钮：{button_text}")
                    return True
            except Exception:
                continue

        # 如果所有定位器都失败，抛出异常
        raise TimeoutException(f"无法找到并点击按钮：{button_text}")

    # def click_menu_text(self, menu_text, timeout=10):
    #     """
    #     获取菜单项的文本
    #     :param menu_text: 菜单项的文本
    #     :param timeout: 等待超时时间（秒）
    #     :return: 菜单项的文本
    #     """
    #     locator = (By.XPATH, f"//span[text()='{menu_text}']/parent::div[contains(@class,'el-submenu__title')]")
    #     element = self.wait_element(locator, timeout)
    #     self.click_element(element)

    def click_contains_text(self, text, tag_name='*', timeout=10):
        """
        点击包含指定文本的元素（更灵活的方法）
        :param text: 要匹配的文本
        :param tag_name: HTML 标签名，默认为 '*'（任意标签）
        :param timeout: 等待超时时间（秒）
        """
        locator = (By.XPATH, f"//{tag_name}[contains(text(), '{text}')]")
        element = self.wait_element(locator, timeout)
        element.click()
        logger.info(f"✅ 已点击包含文本 '{text}' 的 {tag_name} 元素")

    def find_element_by_text(self, text, tag_name='*', timeout=10):
        """
        根据文本内容查找元素
        :param text: 要查找的文本
        :param tag_name: HTML 标签名，默认为 '*'（任意标签）
        :param timeout: 等待超时时间（秒）
        :return: 找到的元素
        """
        locator = (By.XPATH, f"//{tag_name}[text()='{text}']")
        element = self.wait_element(locator, timeout)
        logger.info(f"✅ 找到包含文本 '{text}' 的 {tag_name} 元素")
        return element
    
    def find_contains_text_element(self, text, tag_name='*', timeout=10):
        """
        根据包含的文本内容查找元素（支持模糊匹配）
        :param text: 要查找的文本（部分匹配）
        :param tag_name: HTML 标签名，默认为 '*'（任意标签）
        :param timeout: 等待超时时间（秒）
        :return: 找到的元素
        """
        locator = (By.XPATH, f"//{tag_name}[contains(text(), '{text}')]")
        element = self.wait_element(locator, timeout)
        logger.info(f"✅ 找到包含文本 '{text}' 的 {tag_name} 元素")
        return element
    
    def find_elements_by_text(self, text, tag_name='*', timeout=10):
        """
        根据文本内容查找所有匹配的元素
        :param text: 要查找的文本
        :param tag_name: HTML 标签名，默认为 '*'（任意标签）
        :param timeout: 等待超时时间（秒）
        :return: 元素列表
        """
        locator = (By.XPATH, f"//{tag_name}[text()='{text}']")
        elements = self.wait_elements(locator, timeout)
        logger.info(f"✅ 找到 {len(elements)} 个包含文本 '{text}' 的 {tag_name} 元素")
        return elements

    def click_button_by_text_in_form(self, button_text, form_locator=None, timeout=10):
        """
        在指定表单内根据文本点击按钮（支持层级定位）
        :param button_text: 按钮上显示的文本
        :param form_locator: 表单的定位器（可选），用于限定范围
        :param timeout: 等待超时时间（秒）
        """
        if form_locator:
            # 在指定表单内查找按钮
            locator = (By.XPATH, f"{form_locator}[1]//button[contains(text(), '{button_text}')]")
        else:
            # 在整个页面查找
            locator = (By.XPATH, f"//button[contains(text(), '{button_text}')]")

        element = self.wait_element(locator, timeout)
        element.click()
        logger.info(f"✅ 已点击按钮：{button_text}")

    def click_button_element_by_index(self, button_text, index=0, timeout=10):
        """
        点击匹配的第 N 个元素（从 0 开始）
        :param locator: 元素定位器
        :param index: 索引位置（默认第 1 个）
        :param timeout: 等待超时时间（秒）
        """
        locators = [
            # button 标签，精确匹配文本
            (By.XPATH, f"//button[text()='{button_text}']"),
            # button 标签，包含文本
            (By.XPATH, f"//button[contains(text(), '{button_text}')]"),
            # input type=button，value 属性匹配
            (By.XPATH, f"//input[@type='button' and @value='{button_text}']"),
            # a 标签，当作按钮使用
            (By.XPATH, f"//a[text()='{button_text}']"),
            # 任何包含按钮文本的元素（通用）
            (By.XPATH, f"//*[text()='{button_text}' and contains(@class, 'btn')]"),
            # 通过 aria-label 查找
            (By.XPATH, f"//*[@aria-label='{button_text}']"),
            # 通过 title 属性查找
            (By.XPATH, f"//*[@title='{button_text}']"),
        ]
        for locator in locators:
            try:
                elements = self.wait_elements(locator, timeout=2)
                if index >= len(elements):
                    raise TimeoutException(f"元素索引 {index} 超出范围，只找到 {len(elements)} 个元素")
                elements[index].click()
                logger.info(f"✅ 成功点击第{index + 1}个按钮：{button_text}")
                return True
            except Exception:
                continue

    def check_login_result(self, success_text, error_texts):
        """
        检查登录结果（支持成功和失败两种情况）
        :param success_text:
        :param error_tests:
        :return: dict {'status': 'success'/'failed', 'message': str}
        """

        page_source = self.driver.page_source
        if success_text in page_source:
            return {"status": "success", "message": success_text}

        # 检查页面源码（包括 HTML 内的弹窗、toast、标签等）
        page_source = self.driver.page_source
        for error_text in error_texts:
            if error_text in page_source:
                return {"status": "failed", "message": error_text}

        # 异常情况
        raise AssertionError(f"登录结果异常！未找到预期的提示。页面内容：{page_source[:300]}")
