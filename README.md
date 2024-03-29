# my_homework

Используя любой язык программирования необходимо написать следующие автотесты для сайта https://www.w3schools.com/sql/trysql.asp?filename=trysql_select_all
1. Вывести все строки таблицы Customers и убедиться, что запись с ContactName равной 'Giovanni Rovelli' имеет Address = 'Via Ludovico il Moro 22'.
2. Вывести только те строки таблицы Customers, где city='London'. Проверить, что в таблице ровно 6 записей.
3. Добавить новую запись в таблицу Customers и проверить, что эта запись добавилась.
4. Обновить все поля (кроме CustomerID) в любой записи таблицы Customersи проверить, что изменения записались в базу.
5. Придумать собственный автотест и реализовать (тут все ограничивается только вашей фантазией).
Заполнить поле ввода можно с помощью js кода, используя объект window.editor. [его использование можете увидеть вот тут](https://github.com/I-NICK-I/my_homework/blob/main/src/page_objects/sql_page.py#L33)

Требования:
- Для реализации обязательно использовать Selenium WebDriver ([у меня используется фикстурой из библиотеки pytest-selenium](https://github.com/I-NICK-I/my_homework/blob/main/src/fixtures/selenium.py#L16))
- Тесты должны запускаться в docker контейнере ([dockerfile тут](https://github.com/I-NICK-I/my_homework/blob/main/dockerfile))
- Код автотестов нужно выложить в любой git-репозиторий

### Для локального запуска на windows (у автора таковая) нужно:
1) установить python >=3.9;
2) [создать виртуальное окружение](https://habr.com/ru/articles/491916/), активировать его и из корневой директории установить библиотеки `pip install -r requirements.txt`;
3) если у вас нет локально скачанного chromedriver, то скачать его в зависимости от вашей версии [здесь](https://chromedriver.chromium.org/downloads/version-selection) и положить по пути системной переменной `PATH`;
4) запустить тесты командой `pytest tests` - они запустятся в соответствии с конфиг файлом `pytest.ini` в безголовом режиме в 4 потока.
   Если нужно запустить их с отрисовкой, то можно убрать/закомментирвоать в `pytest.ini` опцию `--headless`, а для запуска в один поток повторить действия для опции `-n`.

### Для локального запуска в докере нужно из корня проекта запустить `run.sh`