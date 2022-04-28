# import sys
import os
import argparse
# import logging
import configparser
import logs.config_server_log
from lib.utils import *
from lib.decoration import log
from server.core import MessageProcessor
from server.server_db import ServerStorage
from server.server_gui import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Инициализация логирования сервера.
server_logger = logging.getLogger('server')


# Парсер аргументов командной строки.
@log
def arg_parser(default_port, default_address):
    '''
    Функция парсинга аргументов командной строки:
    -p 7777 - порт
    -a 127.0.0.1 - ip адрес с которого принимаются сообщения клиентов. Если не задано - то любой адрес.
    --no_gui  старт сервера в консольном режиме.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    return listen_address, listen_port, gui_flag


def config_load():
    '''
    Функция парсинга конфигурационного ini файла: server.ini
    Файл должен лежать в директории запуска
    Файл включает в себя секции:
        [SETTINGS]
        default_port = 7777
        listen_address =
        database_path =
        database_file = server_database.db3
    '''
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def start_server():
    '''
    Основная функция, запускающая серверную часть.
    '''
    config = config_load()
    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = ServerStorage(os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Если  указан параметр без GUI то запускаем консольный  режим
    if gui_flag:
        while True:
            command = input('Введите exit (e) для завершения работы сервера.')
            if command in ('exit', 'e'):
                server.running = False
                server.join()
                break
    # иначе запускаем GUI:
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        server_app.exec_()
        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    start_server()
