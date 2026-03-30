import time

from selenium.webdriver.common.by import By

from page.base_page import base_page


class MoutumPage(base_page):
    USER_INPUT = (By.XPATH, "/html/body/div/div[1]/div[2]/div/div[2]/form/div[1]/div/div[1]/input")
    PASSWORD = (By.XPATH, "/html/body/div/div[1]/div[2]/div/div[2]/form/div[2]/div/div[1]/input")
    LOGIN = (By.XPATH,"/html/body/div/div[1]/div[2]/div/div[2]/form/div[3]/div/button")

    def goto_login(self,url):
        self.go_url(url)

    def login(self,username,password):
        self.input_element(self.USER_INPUT,username)
        self.input_element(self.PASSWORD,password)
        self.click_element(self.LOGIN)
        time.sleep(2)
