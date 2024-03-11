# -*- coding: utf-8 -*-
from random import choice

import allure
from faker import Faker

from src.page_objects.sql_page import SQLPage

QUERY_EXEC_FAILED = "Запрос (%s) не выполнен или выполнен неудачно"
EMPTY_TABLE = "Таблица пустая"
fake = Faker()
PAGE_URL = "https://www.w3schools.com/sql/trysql.asp?filename=trysql_select_all"


@allure.description(
    "Вывести все строки таблицы Customers и убедиться, что запись с ContactName равной "
    "'Giovanni Rovelli' имеет Address = 'Via Ludovico il Moro 22'"
)
def test_1(sql_page: SQLPage):
    expected_address = "Via Ludovico il Moro 22"
    expected_contact_name = "Giovanni Rovelli"
    query = "select * from Customers"

    sql_page.get(PAGE_URL)
    with allure.step("Вывести все строки таблицы Customers"):
        assert sql_page.send_and_confirm_query(query), QUERY_EXEC_FAILED % query
        assert (table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE

    with allure.step(
            "Убедиться, что запись с ContactName равной 'Giovanni Rovelli' имеет "
            "Address = 'Via Ludovico il Moro 22"
    ):
        assert (
            line := next(
                filter(
                    lambda row: row.ContactName == expected_contact_name,
                    table
                ),
                None
            )
        ), f"Не найдена строка со значением ContactName равным {expected_contact_name}"
        assert (actual_address := line.Address) == expected_address, (
            f"{actual_address=} != {expected_address=}"
        )


@allure.description(
    "Вывести только те строки таблицы Customers, где city='London'\n"
    "Проверить, что в таблице ровно 6 записей"
)
def test_2(sql_page: SQLPage):
    expected_length = 6
    query = "select * from Customers where city = 'London'"
    count_query = "select count(*) as count from Customers where city = 'London'"

    sql_page.get(PAGE_URL)

    with allure.step("Вывести только те строки таблицы Customers, где city='London'"):
        assert sql_page.send_and_confirm_query(query), QUERY_EXEC_FAILED % query
        assert (table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE

    with allure.step("Проверить, что в таблице ровно 6 записей"):
        assert (actual_length := len(table)) == expected_length, (
            f"{actual_length=} != {expected_length=}"
        )
        assert sql_page.send_and_confirm_query(count_query), (
                QUERY_EXEC_FAILED % count_query
        )
        assert (new_table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE
        assert (table_count := int(new_table[0][0])) == expected_length, (
            f"{table_count=} != {expected_length=}"
        )


@allure.description(
    "Добавить новую запись в таблицу Customers и проверить, что эта запись добавилась"
)
def test_3(sql_page: SQLPage):
    assert_query = "select * from Customers order by 1 desc limit 1"

    sql_page.get(PAGE_URL)
    fields = "CustomerName, ContactName, Address, City, PostalCode, Country"
    values_list = [
        fake.name(),
        fake.name(),
        fake.street_address(),
        fake.city(),
        fake.postcode(),
        fake.country(),
    ]
    values_str = ", ".join(f'"{_}"' for _ in values_list)
    insert_query = f"insert into Customers ({fields}) values ({values_str})"

    with allure.step("Добавить новую запись в таблицу Customers"):
        assert sql_page.send_and_confirm_query(insert_query), (
                QUERY_EXEC_FAILED % insert_query
        )

    with allure.step("Проверить, что эта запись добавилась"):
        assert sql_page.send_and_confirm_query(assert_query), (
                QUERY_EXEC_FAILED % assert_query
        )
        assert (table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE
        assert not (
            diff := (set(table[0][1:]) - set(values_list))
        ), f"{diff=}"


@allure.description(
    "Обновить все поля (кроме CustomerID) в любой записи таблицы Customers и проверить, "
    "что изменения записались в базу"
)
def test_4(sql_page: SQLPage):
    full_query = "select CustomerID from Customers"
    sql_page.get(PAGE_URL)

    assert sql_page.send_and_confirm_query(full_query), QUERY_EXEC_FAILED % full_query
    assert (table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE
    random_row = choice(table)
    assert (selected_customer_id := random_row.CustomerID), (
        f"CustomerID отсутствует в строке таблицы \n{random_row=}"
    )

    random_row_query = (
        f"select * from Customers where CustomerID = {selected_customer_id} "
        f"order by CustomerID asc limit 1"
    )
    assert sql_page.send_and_confirm_query(random_row_query), (
            QUERY_EXEC_FAILED % random_row_query
    )
    assert (new_table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE
    selected_row = new_table[0]

    update_query = (
        "update Customers set "
        f"CustomerName = '{fake.name()}', "
        f"ContactName = '{fake.name()}', "
        f"Address = '{fake.street_address()}', "
        f"City = '{fake.city()}', "
        f"PostalCode = '{fake.postcode()}', "
        f"Country = '{fake.country()}' "
        f"where CustomerID = '{selected_customer_id}';"
    )

    with allure.step(
            "Обновить все поля (кроме CustomerID) в любой записи таблицы Customers"
    ):
        assert sql_page.send_and_confirm_query(update_query), (
                QUERY_EXEC_FAILED % update_query
        )

    with allure.step("Проверить, что изменения записались в базу"):
        assert sql_page.send_and_confirm_query(random_row_query), (
                QUERY_EXEC_FAILED % random_row_query
        )
        assert (updated_table := sql_page.result_table.get_table_as_matrix()), EMPTY_TABLE
        updated_row = updated_table[0]
        assert updated_row != selected_row, f"{updated_row=} == {selected_row=}"

# @allure.description(
#     "Придумать собственный автотест и реализовать "
#     "(тут все ограничивается только вашей фантазией)"
# )
# def test_5(sql_page: SQLPage):
#     pass
