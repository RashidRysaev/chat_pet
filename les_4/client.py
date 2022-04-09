import sys
import json
import socket
import time
import argparse
import logging
import threading
import re
import logs.config_client_log
from lib.variables import *
from lib.utils import *
from lib.errors import *
from logs.decoration_log import log
from lib.metaclasses import ClientMaker
from client_db import ClientDatabase

client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()

class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # словарь сообщения выхода клиента
    def create_exit_message(self):
        out = {ACTION: EXIT,TIME: time.time(),ACCOUNT_NAME: self.account_name}
        return out

    # функция отправки сообшений
    def create_message(self):
        recipient = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(recipient):
                client_logger.error(f'Попытка отправить сообщение незарегистрированому пользователю: {recipient}')
                return
        message_dict = {ACTION: MESSAGE,SENDER: self.account_name,DESTINATION: recipient,
                        TIME: time.time(),MESSAGE_TEXT: message}
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        # Сохраняем сообщения в истории
        with database_lock:
            self.database.save_message(self.account_name, recipient, message)
        with sock_lock:
            try:
                client_logger.info(f'Отправка сообщения пользователю: {recipient} | {message_dict}')
                send_message(self.sock, message_dict)
            except OSError as err:
                if err.errno:
                    client_logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    client_logger.error('Не удалось передать сообщение. Таймаут соединения')

    def run(self):
        while True:
            self.print_help()
            command = input('Введите команду: ')
            if command in ('message', 'm'):
                self.create_message()
            elif command in ('help', 'h'):
                self.print_help()
            elif command in ('exit', 'q'):
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    client_logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            elif command in ('contacts', 'c'):
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command in ('edit', 'e'):
                self.edit_contacts()
            elif command in ('history', 'mh'):
                self.print_history()
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message (m) - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history (mh) - история сообщений')
        print('contacts (c) - список контактов')
        print('edit (e) - редактирование списка контактов')
        print('help (h) - вывести подсказки по командам')
        print('exit (q) - выход из программы')


    # история сообщений
    def print_history(self):
        client_logger.debug(f'запрошена история сообшений')
        what_msg = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if what_msg == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'{message[3]} | {message[0]} | {message[2]}')
            elif what_msg == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'{message[3]} | {message[1]} | {message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'{message[3]} | {message[0]} -> {message[1]} | {message[2]}')

    # изменение списка контактов
    def edit_contacts(self):
        ans = input('Для удаления введите -, для добавления +: ')
        if ans == '-':
            edit = input('имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_logger.error('Попытка удаления несуществующего контакта.')
        elif ans == '+':
            # Проверка на возможность такого контакта
            edit = input('имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        client_logger.error('Не удалось отправить информацию на сервер.')



class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    client_logger.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    client_logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message \
                            and DESTINATION in message and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.account_name, message[MESSAGE_TEXT])
                            except:
                                client_logger.error('Ошибка взаимодействия с БД')
                        client_logger.info(f'Получено сообщение от {message[SENDER]} | {message[MESSAGE_TEXT]}')
                    else:
                        client_logger.error(f'Получено некорректное сообщение с сервера: {message}')


@log
def create_presence(account_name):
    out = {ACTION: PRESENCE,TIME: time.time(),USER: {ACCOUNT_NAME: account_name}}
    client_logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_response_ans(message):
    client_logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


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


def contacts_list_request(sock, name):
    client_logger.debug(f'Запрос контакт листа для пользователся {name}')
    req = {ACTION: GET_CONTACTS, TIME: time.time(), USER: name}
    client_logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    answer = get_message(sock)
    client_logger.debug(f'Получен ответ {answer}')
    if RESPONSE in answer and answer[RESPONSE] == 202:
        return answer[LIST_INFO]
    else:
        raise ServerError


def user_list_request(sock, username):
    client_logger.debug(f'Запрос списка известных пользователей {username}')
    req = {ACTION: USERS_REQUEST, TIME: time.time(), ACCOUNT_NAME: username}
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {ACTION: ADD_CONTACT, TIME: time.time(), USER: username, ACCOUNT_NAME: contact}
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print(f'{contact} добавлен в контакты')


def remove_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {ACTION: REMOVE_CONTACT, TIME: time.time(), USER: username, ACCOUNT_NAME: contact}
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print(f'{contact} удален из контактов')

# запрос имени пользователя
def get_user():
    while True:
        account = input("введите имя пользователя >>> ")
        if not re.match(r"[A-Za-z]", account) or len(account) > 25 or len(account) < 3:
            client_logger.info(f"недопустимое имя пользователя: {account}")
            print("Имя пользователя должно быть от 3 до 25 латинских символов")
        elif account.lower().strip() == 'guest':
            client_logger.info(f"недопустимое имя пользователя: {account}")
            print("Недоспустимое имя пользователя")
        else:
            break
    return account


# инициализация БД
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    server_address, server_port, client_name = arg_parser()
    print(f"start client on: {server_address}:{server_port}")

    if not client_name:
        client_name=get_user()
        #client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    client_logger.info(f'start client on: {server_address}:{server_port} | имя пользователя: {client_name}')

    try:
        #transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport = create_socket()
        transport.settimeout(1) # Таймаут 1 секунда, необходим для освобождения сокета.
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        client_logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        client_logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except ServerError as error:
        client_logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        client_logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}:'
                               f' конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:
        # Инициализация БД
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        # Если соединение с сервером установлено корректно, запускаем поток взаимодействия с пользователем
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        client_logger.debug(f'запущен поток отправки сообщений')

        # затем запускаем поток - приёмник сообщений.
        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()
        client_logger.debug(f'запущен поток приемки сообщений')

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
