# -*- coding: utf-8 -*-
from functools import wraps

from allure import attach, attachment_type


def is_page_url_change(func):
    """Декоратор проверяющий смену урла страницы"""
    from src.helpers.singletons import SingletonDriver

    @wraps(func)
    def wrapped(*args, **kwargs):

        driver = SingletonDriver()
        if not driver:
            raise UserWarning(
                f"Instance of Page is not found. Wrapped {func}" f"is not executed"
            )
        url_before = driver.current_url
        func(*args, **kwargs)
        url_after = driver.current_url
        body = f"{url_before=}\n{url_after= }"
        attach(
            name="url before → url after",
            attachment_type=attachment_type.TEXT,
            body=body,
        )
        return url_after != url_before

    return wrapped
