class DriverUtil:
    _instance = None
    _driver = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_driver(self, driver_name):
        if self._driver is None:
            if driver_name == "firefox":
                from selenium.webdriver import Firefox
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                options = FirefoxOptions()
                options.add_argument('--start-maximized')
                self._driver = Firefox(options=options)
            elif driver_name == "chrome":
                from selenium.webdriver import Chrome
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                options = ChromeOptions()
                options.add_argument('--start-maximized')
                self._driver = Chrome(options=options)
            elif driver_name == "ie":
                from selenium.webdriver import Ie
                self._driver = Ie()
            elif driver_name == "edge":
                from selenium.webdriver import Edge
                from selenium.webdriver.edge.options import Options as EdgeOptions
                options = EdgeOptions()
                options.add_argument('--start-maximized')
                self._driver = Edge(options=options)
        return self._driver

    def quit_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None


def get_driver(driver_name):
    return DriverUtil().get_driver(driver_name)


def quit_driver():
    return DriverUtil().quit_driver()
