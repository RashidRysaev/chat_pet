.. Mini Chat documentation master file, created by
   sphinx-quickstart on Tue Apr 13 18:45:09 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   https://sphinx-ru.readthedocs.io/ru/latest/rst-markup.html#id5

Документация к приложению "Mini Chat".
=======================================

   Приложение обеспечивает зашифрованную передачу текстовых сообщений между клиентами.
   Состоит из 2-х частей: сервер и клиент.

   Обмен сообщениями происходит с помощью словарей.

   Например первоначальное приветствие.

   **{ACTION:presence, TIME:time, USER:user}**

   Все поля в сообщении описаны в модуле variables.py

   Сервер и клиенты используют собственные базы данных sqllite.
   Пароли от логинов на стороне сервера хранятся в зашифрованном хэшированном виде.

   Имя клиента может состоять из латинских букв и цифр, длина до 25 символом.Первый символ не может быть цифрой.

   Пароль, также как и логин, может состоять из латинских букв и цифр, длина до 12 символов. Первый символ не может быть цифрой.



.. toctree::
   :maxdepth: 4
   :caption: Contents:

   server
   client
   logger
   libs
   vatiable


Индексы и таблицы
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
