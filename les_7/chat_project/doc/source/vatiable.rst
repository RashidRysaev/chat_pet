Константы
================

Константы описаны в модуле  **lib.variables**

    * указание порта для соединений по умолчанию:

    ``DEFAULT_PORT = 7777``

    * указание ip-адреса по умолчанию:

    ``DEFAULT_IP_ADDRESS = '127.0.0.1'``

    * максимальное количество коннектов к серверу:

    ``MAX_CONNECTIONS = 5``

    * длина сетевого пакета:

    ``PACKAGE_LENGTH = 1024``

    * кодировка проекта:

    ``ENCODING = 'utf-8'``

    * уровень логирования:

    ``LOGGING_LEVEL = logging.DEBUG``

    * база данных сервера:

    ``SERVER_DATABASE = 'sqlite:///server_db.db3'``

    * ini-файл для настроек сервера:

    ``SERVER_CONFIG = 'server.ini'``

    * таймаут сервера для опроса сокетов:

    ``SERVER_TIMEOUT = 1/2``

    * масимальный возраст соединения

    ``POOL_RECYCLE = 7200``

    * валидаторы символов для полей (логин / пароль / IPv4 / порт)

    ``RE_LOGIN_MASK='[a-zA-Z][a-zA-Z0-9]{1,25}'``

    ``RE_PASWD_MASK='[a-zA-Z][a-zA-Z0-9]{1,12}'``

    ``RE_IPV4_VALIDATOR='((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)'``

    ``RE_PORT_VALIDATOR='[0-9]{0,5}'``

    * флаг для использования клиента только в режиме прослушивания. использовался в ранних версиях
    ``CLIENT_LISTEN = False  # используется для определения, клиент пишет или слушает``


Прококол JIM основные ключи
----------------------------

    ``ACTION = 'action'``

    ``TIME = 'time'``

    ``USER = 'user'``

    ``ACCOUNT_NAME = 'account_name'``

    ``SENDER = 'from'``

    ``DESTINATION = 'to'``

    ``DATA = 'bin'``

    ``PUBLIC_KEY = 'pubkey'``

Прочие ключи, используемые в протоколе
---------------------------------------

    ``PRESENCE = 'presence'``

    ``RESPONSE = 'response'``

    ``ERROR = 'error'``

    ``MESSAGE = 'message'``

    ``MESSAGE_TEXT = 'mess_text'``

    ``EXIT = 'exit'``

    ``LISTEN = 'listen'  # ключ для словаря, отправка от клиента запрос на прослушивание``

    ``GET_CONTACTS = 'get_contacts'``

    ``LIST_INFO = 'data_list'``

    ``REMOVE_CONTACT = 'remove'``

    ``ADD_CONTACT = 'add'``

    ``USERS_REQUEST = 'get_users'``

    ``PUBLIC_KEY_REQUEST = 'pubkey_need'``


Словари - ответы:
------------------
    ``RESPONSE_200 = {RESPONSE: 200}``

    ``RESPONSE_202 = {RESPONSE: 202, LIST_INFO: None}``

    ``RESPONSE_400 = {RESPONSE: 400, ERROR: None}``

    ``RESPONSE_205 = {RESPONSE: 205}``

    ``RESPONSE_511 = {RESPONSE: 511,DATA: None}``

