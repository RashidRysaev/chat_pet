Дополнительные модули
=====================

decoration.py
-------------

Описан в разделе логирования.

----

descryptors.py
---------------

Добавляет проверку на попытку запуска клиента и сервера с неподходящими параметрами порта и ip-адреса

----

errors.py
--------------

.. autoclass:: lib.errors.ServerError
	:members:

----

metaclasses.py
---------------

.. autoclass:: lib.metaclasses.ServerMaker
	:members:

.. autoclass:: lib.metaclasses.ClientMaker
	:members:

----

utils.py
---------------

.. automodule:: lib.utils.get_message
    :members:

.. automodule:: lib.utils.send_message
    :members:

.. automodule:: lib.utils.validate_ip
    :members:

.. automodule:: lib.utils.validate_port
    :members:


start_scripts.py
----------------

    Служебный скрипт запуска/остановки сервера и нескольких клиентских приложений.

    Служит для быстрого запуска модулей при тестировании / отладки.
