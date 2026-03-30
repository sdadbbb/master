import os
import time


class ScreenshotUtil:
    """截图工具类"""

    @staticmethod
    def save_screenshot(driver, screenshot_dir, filename=None):
        """
        保存截图到指定目录
        :param driver: Selenium WebDriver 实例
        :param screenshot_dir: 截图保存目录
        :param filename: 文件名（可选），如果不传则自动生成
        :return: 截图文件路径
        """
        # 确保目录存在
        os.makedirs(screenshot_dir, exist_ok=True)

        # 如果没有传入文件名，自动生成带时间戳的文件名
        if filename is None:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"

        # 如果文件名不包含 .png，添加后缀
        if not filename.endswith('.png'):
            filename = f"{filename}.png"

        # 生成完整路径
        screenshot_path = os.path.join(screenshot_dir, filename)

        # 保存截图
        driver.save_screenshot(screenshot_path)

        print(f"✅ 截图已保存：{screenshot_path}")
        return screenshot_path
    
    @staticmethod
    def save_screenshot_always(driver, screenshot_dir, test_name, status):
        """
        无论成功失败都截图
        :param driver: Selenium WebDriver 实例
        :param screenshot_dir: 截图保存目录
        :param test_name: 测试名称（用于文件名）
        :param status: 测试结果状态 ('success' 或 'failed')
        :return: 截图文件路径
        """
        # 确保目录存在
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # 生成带状态和时间戳的文件名
        timestamp = int(time.time())
        filename = f"{status}_{test_name}_{timestamp}.png"
        
        # 生成完整路径
        screenshot_path = os.path.join(screenshot_dir, filename)
        
        # 保存截图
        driver.save_screenshot(screenshot_path)
        
        if status == 'success':
            print(f"✅ 测试通过，截图已保存：{screenshot_path}")
        else:
            print(f"❌ 测试失败，截图已保存：{screenshot_path}")
        
        return screenshot_path
