# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass

import allure

from src.core import BasePage, BaseElement

DEFAULT_TIMEOUT = 10


@dataclass
class TableLocators:
    table = "//table[ancestor::*[@id='resultSQL']]"
    table_header = f"{table}//th"
    table_row = f"{table}//tr"
    table_column = f"{table}//td"


class Table(BasePage):
    """Комплексный объект таблицы"""
    _locator = TableLocators()
    self = BaseElement(_locator.table)
    table_header = BaseElement(_locator.table_header)
    table_row = BaseElement(_locator.table_row)
    table_column = BaseElement(_locator.table_column)

    @allure.step("Получить таблицу результатов")
    def get_table_as_matrix(self) -> tuple[namedtuple, ...]:
        """
        Получение таблицы как списка с именованными кортежами, элементы которых 
        соответствуют столбцам таблицы
        :return: кортеж именованных кортежей вида
        >>> (
        >>> row(column_name1="value1", column_name2="value2", column_name3="value3"),
        >>> row(column_name1="value4", column_name2="value5", column_name3="value6"),
        >>> row(...),
        >>> )
        """
        html = self.get_etree()
        row = namedtuple(
            typename="Row",
            field_names=self.table_header.get_text_of_all()
        )
        return tuple(
            row(*(cell.text for cell in line.getchildren()))
            for line in html.xpath(self._locator.table_row)[1:]
        )
