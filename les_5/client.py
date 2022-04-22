import argparse
import sys
import logging
import logs.config_client_log
from logs.decoration_log import log
from lib.variables import *
from lib.errors import *
from lib.utils import *
from PyQt5.QtWidgets import QApplication
from client.client_db import ClientDatabase
from client.transport import ClientTransport
from client.client_gui import UI_StartLoginDlg
#from client.client_gui import UI_MainClientWindow
from client.client_main_window import ClientMainWindow


client_logger = logging.getLogger('client')

@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

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

    return server_address, server_port, client_name


if __name__ == '__main__':
    # Загружаем параметы командной строки
    server_address, server_port, client_name = arg_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog=UI_StartLoginDlg()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
            client_logger.info(f'авторизация успешна: {client_name}')
        else:
            client_logger.info(f'Не пройдена авторизация - нажата отмена. Выход.')
            exit(0)

    client_logger.info(f'start client on: {server_address}:{server_port} | имя пользователя: {client_name}')
    database = ClientDatabase(client_name)
    client_logger.debug((f'database={database}'))

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    client_main_window = ClientMainWindow(database, transport)
    client_main_window.make_connection(transport)
    client_main_window.setWindowTitle(f'{client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()


