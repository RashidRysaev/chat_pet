Серверная часть
================

Серверный модуль приложения.

При запуске можно указывать аргументы командной строки:

    * указание порта для соединения:

    ``python server.py -p 7777``

    * указание адреса, с которого принимаюатся соединения:

    ``python server.py -a 192.168.0.100``

    * флаг запуска в консольном режиме. В нем поддерживается только одна команда: exit - завершение работы

    ``python server.py --no-gui``


    Главное окно приложения:

.. image:: _static/server_main_window.png
   :alt: main window
   :align: center

----

server.ini
----------

Файл с настройками запуска сервера. Находится в директории с основным файлом server.py:
    [SETTINGS]
    database_path =

    database_file = server_db.db3

    default_port = 7777

    listen_address =

    Эти настройки можно задать как в самом файле, так и с помощью графического модуля.

.. image:: _static/server_config_window.png
   :alt: config window
   :align: center

----


server.py
---------
.. automodule:: server

Модуль, запускающий серверную часть. Содержит:
    * парсер аргументов командной строки
        Функция парсинга аргументов командной строки:

        -p 7777 - порт

        -a 127.0.0.1 - ip адрес с которого принимаются сообщения клиентов. Если не задано - то любой адрес.

        --no_gui  старт сервера в консольном режиме.

    * парсер значений из настроечного файла server.ini

    * функционал инициализации приложения

        Загружает конфигурацию из командной строки / server.ini
        Инициализирует базу данных.
        Запускает демон.

----

core.py
~~~~~~~

Ядро сервера. В модуле описана основная логика серверной части.

Содержит класс-поток обрабатывающий сообщения.

Удяляет, добавляет пользователей.



.. autoclass:: server.core.MessageProcessor
	:members:

----

server_db.py
~~~~~~~~~~~~

Модуль, описывающий работу с базой данных.


.. autoclass:: server.server_db.ServerStorage
	:members:

----

server_gui.py
~~~~~~~~~~~~~

Модуль оконного интерфейса серверной части.

.. autoclass:: server.server_gui.MainWindow
	:members:

.. autoclass:: server.server_gui.StatWindow
	:members:

.. autoclass:: server.server_gui.LoginHistoryWindow
	:members:

.. autoclass:: server.server_gui.DelUserDialog
	:members:

.. autoclass:: server.server_gui.RegisterUser
	:members:

.. autoclass:: server.server_gui.ConfigWindow
	:members:

