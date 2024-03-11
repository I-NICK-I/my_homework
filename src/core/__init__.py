# -*- coding: utf-8 -*-
from __future__ import annotations

import contextlib
import time
from inspect import stack
from io import StringIO
from typing import List, Optional, Tuple, Union

import allure
from lxml import etree
from lxml.etree import _ElementTree
from selenium.common.exceptions import (
    InvalidArgumentException,
    TimeoutException,
)
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.checks.web import is_page_url_change
from src.helpers.singletons import SingletonDriver

DEFAULT_TIMEOUT = 5
DEFAULT_ATTEMPTS_COUNT = 10
HTML_PARSER = etree.HTMLParser()


class BasePage:
    """Базовая страница для использования в Page Object"""
    def __init__(self, url: str = None):
        self._driver: WebDriver = SingletonDriver()
        self.get(url) if url else None

    def __setattr__(self, name, value):
        if isinstance(self, BaseElement):
            return
        elif isinstance(self, BasePage):
            super(BasePage, self).__setattr__(name, value)
        else:
            setattr(self, name, value)

    def __getattribute__(self, item):
        """
        Переопределение стандартоного метода с целью покладывания таймаута и родительской
        страницы внутрь экземпляров базовых элементов
        :param item: базовый элемент
        :return: базовый элемент с добавленными таймаутом и страницей в атрибутах
        """
        attr = object.__getattribute__(self, item)

        if isinstance(attr, BaseElement):
            setattr(attr, "_page", self)
            setattr(attr, "_timeout", self.driver.element_timeout)

        return attr

    @property
    def driver(self):
        return SingletonDriver()

    @is_page_url_change
    @allure.step("Перейти по адресу {url}")
    def get(
            self,
            url: str,
            sleep_before_execute: Union[int, float] = None,
            attempts_to_load: Union[int, float] = 10,
            wait_until_find=None,
            check_js_complete=True,
    ):
        """
        Метод перехода на страницу с указаным урлом
        :param url: желаемый урл
        :param sleep_before_execute: ожидание перед переходом
        :param attempts_to_load: количество попыток при проверке загрузки страницы
        :param wait_until_find: ожидание появления элемента
        :param check_js_complete: проверка на завершение js-скриптов
        :return: булево значение успеха загрузки старницы
        """
        if not self.driver:
            raise UserWarning("Web driver is not initialized")
        cur_url = self.get_current_url().strip("/")

        if url and url != cur_url:
            self.driver.get(url)
            self.wait_page_loaded(
                sleep_before_execute=sleep_before_execute,
                attempts_to_load=attempts_to_load,
                wait_until_find=wait_until_find,
                check_js_complete=check_js_complete,
            )

    @allure.step("Получить урл текущей страницы")
    def get_current_url(self) -> Optional[str]:
        if current_url := self.driver.current_url:
            allure.attach(name=current_url, body=current_url)
        return current_url

    @allure.step("Получить html-исходник текущей страницы")
    def get_page_source(self) -> Optional[str]:
        source = ""
        with contextlib.suppress(Exception):
            source = self.driver.page_source
        return source

    @allure.step("Дождаться загрузки страницы")
    def wait_page_loaded(
            self,
            wait_until_find: Union[str, BaseElement] = "",
            wait_until_not_find: Union[str, BaseElement] = "",
            attempts_to_load: int = DEFAULT_ATTEMPTS_COUNT,
            check_js_complete: bool = True,
            sleep_before_execute: Union[int, float] = 0,
            sleep_after_execute: Union[int, float] = 0,
    ) -> None:
        """
        Метод ожидания загрузки страницы
        :param wait_until_find: ожидание появления элемента
        :param wait_until_not_find: ожидание исчезновения элемента
        :param attempts_to_load: количество попыток проверки загрузки старницы
        :param check_js_complete: провека на завершение js-скриптов
        :param sleep_before_execute: ожидание перед вызовом проверки
        :param sleep_after_execute: ожидание после вызова проверки
        """

        load_strategy = self.driver.caps["pageLoadStrategy"]
        if load_strategy == "normal":
            ready_state = ["complete"]
        else:
            ready_state = ["complete", "interactive"]

        if sleep_before_execute:
            time.sleep(sleep_before_execute)

        def break_page_loading():
            """Прерывание загрузки страницы"""
            with contextlib.suppress(Exception):
                self.driver.execute_script("window.stop();")

        def do_we_try_again(checks: dict = None):
            """
            Хелпер который прерывает загрузку страницы,
            если мы исчерпали количество попыток
            :param checks: Словарь с выполняемыми проверками
            """
            if attempts_to_load - attempt_counter == 1:
                break_page_loading()
            assert attempt_counter < attempts_to_load, (
                f"The page attempt to load more than {attempts_to_load} times!\n"
                f"{checks or ''}"
            )

        def is_javascript_complete(*_, **__):
            try:
                script_done = self.driver.execute_script(
                    f"return {ready_state}.includes(document.readyState);"
                )
            except Exception:
                script_done = False
            return script_done

        def does_element_found(item: Union[str, BaseElement]):
            """
            Проверка успешности нахождения элемента
            :param item: базовый элемент или xpath-локатор
            """
            if isinstance(item, BaseElement):
                return item.find()
            elif isinstance(item, str) and isinstance(
                    self,
                    (
                            BaseElement,
                            BasePage,
                    ),
            ):
                page: BasePage = getattr(self, "_page", None) or self
                if elem := getattr(
                        page, item,
                        BaseElement(locator=item, page=page)
                ):
                    return does_element_found(elem)
                else:
                    raise UserWarning(f"Current {page=} has not element {item}")

        def does_element_disappeared(item: Union[str, BaseElement]):
            """
            Проверка исчезновения элемента
            :param item: базовый элемент или xpath-локатор
            """
            disappear = False

            if isinstance(item, BaseElement):
                locator = getattr(item, "_locator")[1]
                driver = self.driver
                with contextlib.suppress(Exception):
                    disappear = WebDriverWait(driver, DEFAULT_TIMEOUT).until_not(
                        EC.presence_of_element_located((By.XPATH, locator))
                    )
            elif isinstance(item, str) and isinstance(self, BaseElement):
                if hasattr(self._page, item):
                    item = getattr(self._page, item)
                    return does_element_disappeared(item)

            else:
                raise TypeError(
                    f"Unexpected {type(item)=}. Expect one of str, BaseElement")

            return bool(disappear)

        checks_we_ask = {
            "js_completion": check_js_complete,
            "element_presence": wait_until_find,
            "element_disappearance": wait_until_not_find,
        }
        checks_to_do = {check: run for check, run in checks_we_ask.items() if run}

        make_this = {
            "js_completion": is_javascript_complete,
            "element_presence": does_element_found,
            "element_disappearance": does_element_disappeared,
        }

        page_load_checklist = {check: False for check in checks_to_do}
        attempt_counter = 0
        while not all(page_load_checklist.values()):
            time.sleep(0.5)

            for check, with_value in checks_to_do.items():
                result = make_this[check](with_value)
                page_load_checklist[check] = result

            do_we_try_again(checks=page_load_checklist)

            attempt_counter += 1

        if sleep_after_execute and isinstance(sleep_after_execute, (int, float)):
            time.sleep(sleep_after_execute)

    @allure.step("Создать базовый элемент с локатором {xpath}")
    def make_base_element(self, xpath: str) -> BaseElement:
        """
        :param xpath: локатор будущего элемента
        :return: базовый элемент
        """
        return BaseElement(locator=xpath, page=self)

    @allure.step("Получить дерево элементов из html-исходника страницы")
    def get_etree(self) -> _ElementTree:
        return etree.parse(StringIO(self.driver.page_source), HTML_PARSER)


class BaseElement:
    """Базовый элемент используемый в Page Object"""

    _locator: Tuple[str, str] = ("", "")
    _page: BasePage = None
    _timeout: Union[float, int] = 0.1
    _elem_name: str = ""
    _action: ActionChains

    def __init__(
            self,
            locator: Union[tuple, str],
            page=None,
    ):
        self._driver = SingletonDriver()
        self._page = page or BasePage()

        if isinstance(locator, tuple):
            locator_type, locator_path = locator
        elif isinstance(locator, str):
            locator_type, locator_path = "xpath", locator
        else:
            raise TypeError(
                f"Unexpected type of locator: {type(locator)}."
                f"\nLocator value: {locator=}"
            )
        self._locator = By.XPATH, locator_path
        stack_ = stack()
        try:
            frame = next(filter(lambda x: "locator" in x.code_context[0], stack_))
            self._elem_name = frame.code_context[0].strip().split()[0]
        except StopIteration:
            self._elem_name = "custom made fake element"
        except TypeError:
            pass

    def __repr__(self):
        return "%s :%s" % self.locator_with_type

    def __getitem__(self, item: int) -> WebElement:
        return self.find_all(DEFAULT_TIMEOUT)[item]

    @property
    def locator(self):
        return self._locator[1]

    @property
    def locator_with_type(self):
        return self._locator

    @property
    def page(self):
        return self._page

    @property
    def driver(self):
        return SingletonDriver()

    @property
    def elem_name(self):
        return self._elem_name or self.__name__

    @property
    def action(self):
        return ActionChains(SingletonDriver())

    @allure.step("Найти элемент")
    def find(self, timeout: Union[int, float] = 0) -> Optional[WebElement]:
        """
        Поиск элемента с условием ожидания
        :param timeout: максимальное время ожидания на поиск элемента
        """
        element = None
        allure.attach(name=self.locator, body=self.locator)
        timeout = timeout or self._timeout
        with contextlib.suppress(Exception):
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self._locator)
            )
        return element

    @allure.step("Дождаться интерактивности элемента {0}")
    def _wait_to_be_clickable(
            self,
            timeout: Union[int, float] = 0
    ) -> Optional[WebElement]:
        """
        :param timeout: максимальное время ожидания на поиск элемента
        """
        element = None
        try:
            element = WebDriverWait(
                driver=self.driver,
                timeout=timeout or self._timeout,
                ignored_exceptions=[InvalidArgumentException],
            ).until(EC.element_to_be_clickable(self.locator_with_type))

        except TimeoutException as timeout_exception:
            raise timeout_exception

        except Exception:
            pass
        return element

    @allure.step("Нажать кнопку клавиатуры")
    def press_key(self, key: Union[Keys, str]):
        """
        :param key: символ буквы или строка равная значению кнопки клавиатуры
        """
        if key not in Keys.__dict__.values() and len(key) > 1:
            raise UserWarning(f"Unexpected value of {key=}")
        self.action.key_down(key).key_up(key).perform()

    def _build_keys_input(self, keys: str) -> ActionChains:
        """
        Метод сборки последовательности клавиатурного ввода
        :param keys: строка, которую требуется ввести в элемент
        """
        result = self.action
        for k in keys:
            result.key_down(k).key_up(k)
        return result

    @allure.step("Заполнить элемент {0} значением {keys}")
    def send_keys(
            self,
            keys: Optional[str],
            timeout_to_find: Union[int, float] = 0,
            **kw
    ) -> bool:
        """
        :param keys: строковый инпут, ожидаемый к вводу в элемент
        :param timeout_to_find: максимальное время ожидания на поиск элемента
        :param kw: ключевые слова для управления ожиданиями загрузки страницы
        :return: подтверждение успеха ввода
        :raises: Ошибка поиска элемента
        """
        keys = keys if isinstance(keys, str) else str(keys)
        keys = keys.replace("\n", "\ue007")
        if element := self.find(timeout=timeout_to_find or self._timeout):
            element.click()
            (
                self.action
                .key_down(Keys.CONTROL)
                .key_down("a")
                .key_up(Keys.CONTROL)
                .perform()
            )
            self.press_key(Keys.DELETE)
            self._build_keys_input(keys).perform()
            wait_kwargs_dict = {
                "attempts_to_load": kw.get("attempts_to_load", 0),
                "wait_until_find": kw.get("wait_until_find"),
                "wait_until_not_find": kw.get("wait_until_not_find"),
            }
            wait_kwargs_dict = {
                key: value for key, value in wait_kwargs_dict.items() if value
            }

            self._page.wait_page_loaded(**wait_kwargs_dict)
        else:
            msg = "BaseElement with locator {0} not found"
            raise AttributeError(msg.format(self.locator))

        return True

    @allure.step("Получить текст из элемента {0}")
    def get_text(self, timeout: Union[int, float] = 0) -> str:
        """
        :param timeout: максимальное время ожидания на поиск элемента
        """
        return element.text if (
            element := self.find(timeout=timeout or self._timeout)
        ) else ""

    @allure.step("Кликнуть по элементу {0}")
    def click(self, timeout_to_find: Union[int, float] = 0, **kw):
        """
        :param timeout_to_find: максимальное время ожидания на поиск элемента
        :param kw: ключевые слова для управления ожиданиями загрузки страницы
        """
        if not (
                element := (
                        self._wait_to_be_clickable(
                            timeout=timeout_to_find or self._timeout
                        )
                )
        ):
            raise AttributeError(f"BaseElement with locator {self._locator} not found")

        action = ActionChains(self.driver)

        action.move_to_element(element).click(on_element=element).perform()

        wait_kwargs_dict = {
            "attempts_to_load": kw.get("attempts_to_load", 0),
            "wait_until_find": kw.get("wait_until_find"),
            "wait_until_not_find": kw.get("wait_until_not_find"),
        }
        wait_kwargs_dict = {
            key: value for key, value in wait_kwargs_dict.items() if value
        }

        self._page.wait_page_loaded(**wait_kwargs_dict)

    @allure.step("Найти все элементы по локатору: {0}")
    def find_all(self, timeout: Union[int, float] = 0) -> List[WebElement, ...]:
        """
        :param timeout: максимальное время ожидания на поиск элемента
        :return: список веб-элементов
        """
        allure.attach(name=self.locator, body=self.locator)
        with contextlib.suppress(Exception):
            elements = WebDriverWait(
                driver=self.driver,
                timeout=timeout or self._timeout
            ).until(
                EC.presence_of_all_elements_located(self.locator_with_type)
            )
        return elements or []

    @allure.step("Подсчитать количество элементов по локатору: {0}")
    def count(self, timeout: Union[int, float] = 0) -> int:
        """
        :param timeout: максимальное время ожидания на поиск элемента
        :return: число найденных веб-элементов
        """
        elements = self.find_all(timeout or self._timeout)
        result = len(elements)
        allure.attach(name=f"Найдено элементов: {result}", body=str(result))
        return result

    @allure.step("Получить текст всех элементов найденных по локатору: {0}")
    def get_text_of_all(self, timeout: Union[int, float] = 0) -> List[str, ...]:
        """
        :param timeout: максимальное время ожидания на поиск элемента
        :return: список строк из атрибута `text` содержащегося в найденных веб-элементах
        """
        result = []
        if elements := self.find_all(timeout=timeout or self._timeout):
            for element in elements:
                with contextlib.suppress(Exception):
                    text = element.text
                result.append("" or text)
        return result
