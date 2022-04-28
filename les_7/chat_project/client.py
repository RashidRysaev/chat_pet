import logging
import logs.config_client_log
import argparse
import sys
import os
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from lib.variables import *
from lib.errors import ServerError
from lib.decoration import log
from client.client_db import ClientDatabase
from client.transport import ClientTransport
from client.client_gui import ClientMainWindow, UI_StartLoginDlg
from lib.utils import *

client_logger = logging.getLogger('client')


@log
def arg_parser():
    '''
    Функция парсинга аргументов командной строки:
    -port 7777 - порт
    -addr 127.0.0.1 - ip адрес сервера
    -n имя клиента
    -p пароль клиента
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    # проверим подходящий номер порта
    check_port = validate_port(server_port)
    if not check_port:
        client_logger.critical(f'Некорректный порт соединения: {server_port}')
        print(f'Некорректный порт соединения: {server_port}')
        exit(1)

    check_server_ip = validate_ip(server_address)
    if not check_server_ip:
        client_logger.critical(f'Некорректный адрес соединения: {server_address}')
        print(f'Некорректный адрес соединения: {server_address}')
        exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    ''' Основная функция, запускающая клиентскую часть. '''
    # Загружаем параметры командной строки
    server_address, server_port, client_name, client_passwd = arg_parser()
    client_logger.debug(f'Args loaded: {server_address, server_port, client_name, client_passwd}')

    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    # start_dialog = UI_StartLoginDlg()

    if not client_name:
        start_dialog = UI_StartLoginDlg()
        if not client_name or not client_passwd:
            client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            client_logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
            client_logger.info(f'авторизация успешна: {client_name}')
            # авторизация пройдена, стартовое окно больше не нужно
            del start_dialog
        else:
            client_logger.info(f'Не пройдена авторизация - нажата отмена. Выход.')
            exit(0)

    client_logger.info(f'start client on: {server_address}:{server_port} | имя пользователя: {client_name}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path, 'client')
    dir_path = os.path.join(dir_path, 'key')
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    # !!!keys.publickey().export_key()
    client_logger.debug("Keys sucsessfully loaded.")

    database = ClientDatabase(client_name)
    client_logger.debug((f'database={database}'))
    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, database, client_name, client_passwd, keys)
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()
    # авторизация пройдена, стартовое окно больше не нужно
    # del start_dialog

    client_main_window = ClientMainWindow(database, transport, keys)
    client_main_window.make_connection(transport)
    client_main_window.setWindowTitle(f'{client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
