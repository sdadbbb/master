from page.base_page import base_page


class ConfigPage(base_page):

    def get_goods_type(self, text):
        self.find_element_by_text(text).click()

    def click_button_add(self, click_contains_text='新增'):
        self.click_button_by_text(click_contains_text)

    def click_button_update(self, click_contains_text='修改'):
        self.click_button_by_text(click_contains_text)

    def click_button_delete(self, click_contains_text='删除'):
        self.click_button_by_text(click_contains_text)
