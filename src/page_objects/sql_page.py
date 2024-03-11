# -*- coding: utf-8 -*-
from dataclasses import dataclass

import allure

from src.core import BasePage, BaseElement
from src.helpers.composite_elements import Table


@dataclass
class SQLLocators:
    query_input = '(//*[contains(@class, "CodeMirror")])[1]'
    run_button = '//button[contains(text(), "Run SQL")]'


class SQLPage(BasePage):
    """
    Страница с SQL-редактором в песочнице со страницы школы
    https://www.w3schools.com/sql/trysql.asp?filename=trysql_select_all
    """
    _locator = SQLLocators()
    result_table = Table()
    query_input = BaseElement(_locator.query_input)
    run_button = BaseElement(_locator.run_button)

    def _insert_query(self, query: str) -> bool:
        """
        Отправка sql-запроса через `window.editor` объект
        :param query: sql-запрос
        :return: подтверждение успешного ввода
        """
        query = query.replace('"', "'")
        script = f'window.editor.getDoc().setValue("{query}")'
        self.driver.execute_script(script)
        return self.query_input.get_text() == query

    @allure.step("Отправить и подтвердить SQL запрос")
    def send_and_confirm_query(self, query: str, via_editor: bool = False) -> bool:
        """
        Метод ввода sql-запроса как эмуляцией ввода с клавиатуры так и через
        `window.editor` объект
        :param query: sql-запрос
        :param via_editor: флаг выбора способа ввода, по-умолчанию через клавиатуру
        :return: ui-подтверждение успеха обработки запроса страницей
        """
        self._insert_query(query) if via_editor else self.query_input.send_keys(query)
        self.run_button.click()
        output_msg = self.make_base_element('//*[@id="resultSQL"]')
        return self.result_table.self.find(2) or output_msg.get_text(2)
