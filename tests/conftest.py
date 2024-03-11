# -*- coding: utf-8 -*-

import os

from _pytest.config import Config
from _pytest.config.argparsing import Parser

WINDOW_DEFAULT_SIZE = (1600, 900)

pytest_plugins = ["src.fixtures.selenium", "src.fixtures.pages"]


def pytest_addoption(parser: Parser):
    parser.addoption("--headless", action="store_true", default=False)
    parser.addoption("--rerun", default=0, type=int)
    parser.addoption("--size", default=WINDOW_DEFAULT_SIZE)


def pytest_configure(config: Config):
    os.environ["HEADLESS"] = str(config.getoption("--headless", False))
    os.environ["PYTEST_BASE_URL"] = config.getini("base_url")
