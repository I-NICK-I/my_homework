# -*- coding: utf-8 -*-
from math import ceil

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
from pytest_selenium import drivers, split_class_and_test_names
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.remote.webdriver import WebDriver

from src.core import SingletonDriver


@pytest.fixture
def selenium(selenium: WebDriver, request: FixtureRequest):
    """
    Фикстура веб-драйвера в которой мы обогощаем драйвер настройками и инициализируем
    синглтон веб-драйвера
    :param selenium: инициализированный библиотекой pytest-selenium веб-драйвер
    :param request: фикстура контекста подзапроса тестовой сессии
    :return: веб-драйвер
    """
    SingletonDriver(selenium)
    size = request.config.getoption("--size")
    selenium.set_window_size(*size)
    selenium.implicitly_wait(3)
    selenium.set_page_load_timeout(time_to_wait=30)
    if not getattr(selenium, "element_timeout", None):
        selenium.element_timeout = ceil(selenium.timeouts.page_load / 5)
    return selenium


@pytest.fixture
def chrome_options(request: FixtureRequest, chrome_options: ChromiumOptions):
    """
    Более строгая настройка веб-дарйвера для Chrome браузера
    :param request: фикстура контекста подзапроса тестовой сессии
    :param chrome_options: объект с опциями запуска веб-драйвера
    """
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.set_capability(
        "goog:loggingPrefs",
        {
            "performance": "ALL",
            "browser": "ALL",
            "driver": "ALL",
        },
    )
    if request.config.getoption("--headless"):
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument("headless=new")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("no-sandbox")
    chrome_options.add_argument("enable-javascript")
    chrome_options.add_argument("disable-blink-features=AutomationControlled")
    chrome_options.add_argument("allow-insecure-localhost")
    chrome_options.add_argument("allow-running-insecure-content")
    chrome_options.add_argument("ignore-certificate-errors")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-dev-shm-usage")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("disable-extensions")
    return chrome_options


@pytest.fixture(autouse=True)
def driver_closure(selenium: WebDriver, request: FixtureRequest):
    """
    Teardown фикстура закрытия сессии внутри синглтона веб-драйвера
    :param selenium: инициализированный библиотекой pytest-selenium веб-драйвер
    :param request: фикстура контекста подзапроса тестовой сессии
    """
    def close():
        SingletonDriver.clear_instance()

    yield selenium
    request.addfinalizer(close)


@pytest.fixture
def driver_kwargs(
        request: FixtureRequest,
        capabilities,
        chrome_options,
        driver_args,
        driver_class,
        driver_log,
        driver_path,
        firefox_options,
        edge_options,
        pytestconfig,
        base_url,
):
    """
    Переопределённая фикстура общих настроек дравйвера подменяющая библиотечную
    `driver_kwargs` из pytest-selenium
    """
    kwargs = {}
    driver = getattr(drivers, pytestconfig.getoption("driver").lower())
    kwargs |= driver.driver_kwargs(
        capabilities=capabilities,
        chrome_options=chrome_options,
        driver_args=driver_args,
        driver_log=driver_log,
        driver_path=driver_path,
        firefox_options=firefox_options,
        edge_options=edge_options,
        host=pytestconfig.getoption("selenium_host"),
        port=pytestconfig.getoption("selenium_port"),
        request=request,
        test=".".join(split_class_and_test_names(request.node.nodeid)),
    )
    kwargs.pop("service_log_path")
    pytestconfig._driver_log = driver_log
    chrome_options._caps |= kwargs.pop('desired_capabilities', {})
    kwargs["options"] = chrome_options
    return kwargs


@pytest.fixture(scope="session")
def session_capabilities(pytestconfig: Config):
    """Сессионные настройки браузера, с указанием предварительной загрузки страницы"""
    driver = pytestconfig.getoption("driver").lower()
    capabilities = getattr(DesiredCapabilities, driver, {}).copy()
    capabilities["pageLoadStrategy"] = "eager"
    capabilities.update(pytestconfig._capabilities)
    return capabilities
