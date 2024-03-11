# -*- coding: utf-8 -*-
import pytest

from src.page_objects.sql_page import SQLPage


@pytest.fixture
def sql_page():
    """Фикстура страницы с SQL-редактором"""
    return SQLPage()
