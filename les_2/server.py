""" серверная часть """
import logging
import select
from lib.variables import *
from lib.utils import server_settings, create_socket, get_message, send_message
from lib.descriptors import PortValidate, IPValidate
from lib.metaclasses import ServerMaker

SERVER_LOGGER = logging.getLogger('server')


class Server(metaclass=ServerMaker):
    srv_port = PortValidate()
    srv_adr = IPValidate()

    def __init__(self, server_address, server_port):
        # ip адрес и порт для подключения
        self.srv_adr = server_address
        self.srv_port = server_port
        # список клиентов
        self.clients = []
        # список сообщений для отправки
        self.messages = []
        # словарь связей имя_клиента:сокет
        self.names = dict()

    def init_socket(self):
        transport = create_socket()
        # transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.srv_adr, self.srv_port))
        transport.settimeout(SERVER_TIMEOUT)
        transport.listen(MAX_CONNECTIONS)
        print(f"server start on: {self.srv_adr}:{self.srv_port}")
        SERVER_LOGGER.info(f"server started on {self.srv_adr}:{self.srv_port}")

        self.socket_transport = transport
        self.socket_transport.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.socket_transport.accept()
                SERVER_LOGGER.debug(f'client | {client_address}')
            except OSError:
                pass
            else:
                print(f"Получен запрос на соединение от {str(client_address)}")
                SERVER_LOGGER.info(f"установлено соедниение с клиентом {client_address}")
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.client_message_handler(get_message(client_with_message), client_with_message)
                    except Exception:
                        SERVER_LOGGER.info(f"клиент {client_with_message.getpeername()} отключился")
                        print(f"клиент {client_with_message.getpeername()} отключился")
                        self.clients.remove(client_with_message)
                        print(self.clients)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    SERVER_LOGGER.info(f'Связь с клиентом  {message[DESTINATION]} потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
                self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                               f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                                f'отправка сообщения невозможна.')

    def client_message_handler(self, message, client):
        SERVER_LOGGER.debug(f'функция разбора message от клиента: {message}')
        if ACTION not in message:
            SERVER_LOGGER.error(f"сообщение от клиента не содержит обязательного поля ACTION: {message}")
            print(f"сообщение от клиента не содержит обязательного поля ACTION: {message}")
            send_message(client, {RESPONSE: 400, ERROR: ERR400})
            return
        elif TIME not in message:
            SERVER_LOGGER.error(f"сообщение от клиента не содержит обязательного поля TIME: {message}")
            print(f"сообщение от клиента не содержит обязательного поля TIME: {message}")
            send_message(client, {RESPONSE: 400, ERROR: ERR400})
            return
        elif message[ACTION] == PRESENCE and str(message[USER][ACCOUNT_NAME]).lower() == 'guest':
            SERVER_LOGGER.debug(f"сформировано PRESENCE сообщение:{message}")
            # names[message[USER][ACCOUNT_NAME]] = client # пользователь гость, не добавляем в словарь пользователей
            send_message(client, {RESPONSE: 200, ERROR: ERR200, MSG: str(f"Welcome, {message[USER][ACCOUNT_NAME]}")})
            return
        elif message[ACTION] == AUTH and USER in message and str(message[USER][ACCOUNT_NAME]).lower() != 'guest':
            SERVER_LOGGER.info(f"Получено AUTH сообщение: {message}")
            if str(message[USER][ACCOUNT_NAME]).lower() not in str(
                    self.names.keys()).lower():  # нет такого, можно регать
                SERVER_LOGGER.info(f"сформировано AUTH сообщение: {message}. Пользователь занесен в список")
                self.names[message[USER][ACCOUNT_NAME]] = client
                # send_message(client, {RESPONSE: 200, ERROR: ERR200, MSG: str(f"Welcome, {message[USER][ACCOUNT_NAME]}")})
                # send_message(client, RESPONSE_200)
                send_message(client,
                             {RESPONSE: 200, ERROR: ERR200, MSG: str(f"Welcome, {message[USER][ACCOUNT_NAME]}")})
                return
            else:
                SERVER_LOGGER.error(f"{ERR_USER_ALREADY_EXIST}: {message}")
                response = RESPONSE_400
                response[ERROR] = ERR_USER_ALREADY_EXIST
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif message[ACTION] == MSG and DESTINATION in message and SENDER in message and MSG_TEXT in message:
            SERVER_LOGGER.debug(f"сформировано MSG сообщение: {message}")
            # messages_list.append((message[ACCOUNT_NAME], message[MSG_TEXT]))
            self.messages.append((message))
            return
        elif ACTION in message and message[ACTION] == WHO:
            SERVER_LOGGER.debug(f"сформировано WHO сообщение: {message}")
            # messages_list.append((message[ACCOUNT_NAME], message[MSG_TEXT]))
            message[DESTINATION] = message[SENDER]  # отправить список самому себе
            all_names = ''
            for el in self.names:
                all_names = all_names + ' | ' + el
            all_names = f"пользователи в сети:\n{all_names[3:]}"
            message[MSG_TEXT] = all_names
            self.messages.append((message))
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            SERVER_LOGGER.info(f"пользователь {message[ACCOUNT_NAME]} вышел")
            print(f"пользователь {message[ACCOUNT_NAME]} вышел")
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            print(self.names)
            return
        else:
            SERVER_LOGGER.error(f"функция разбора message от клиента, ни одно из условий не подошло: {message}")
            print(f"функция разбора message от клиента, ни одно из условий не подошло: {message}")
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    def start_server():
        srv_settings = server_settings()
        server_address = srv_settings[0]
        server_port = srv_settings[1]
        SERVER_LOGGER.debug(f"srv_settings:{server_address}:{server_port}")
        server = Server(server_address, server_port)
        # print(f"server start on: {server_address}:{server_port}")
        server.main_loop()


if __name__ == '__main__':
    Server.start_server()
