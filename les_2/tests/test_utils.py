""" тесты утилит"""

import sys
import os
import unittest
import json

sys.path.append(os.path.join(os.getcwd(), '..'))
from lib.variables import *
from lib.utils import *


class TestSocket:
    '''
    Тестовый класс для тестирования отправки и получения,
    при создании требует словарь, который будет прогонятся
    через тестовую функцию
    '''

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        """
        Тестовая функция отправки, корретно  кодирует сообщение,
        так-же сохраняет что должно было отправлено в сокет.
        message_to_send - то, что отправляем в сокет
        :param message_to_send:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        # кодирует сообщение
        self.encoded_message = json_test_message.encode(ENCODING)
        # сохраняем что должно было отправлено в сокет
        self.receved_message = message_to_send

    def recv(self, max_len):
        """
        Получаем данные из сокета
        :param max_len:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):
    ''' тестовый класс, собственно выполняющий тестирование '''
    test_dict_send = {ACTION: PRESENCE, TIME: 2, USER: {ACCOUNT_NAME: 'NEW_USER'}}
    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_err = {RESPONSE: 400, ERROR: ERR400}

    def test_validate_ip_success(self):
        """ проверяет что в строке есть правильный IP адрес """
        self.assertEqual(validate_ip('127.0.0.1'), True)

    def test_validate_ip_fail_str_is_long(self):
        """ проверяет что в строке есть правильный IP адрес """
        self.assertEqual(validate_ip('127.0.0.1.1.1.1'), False)

    def test_validate_ip_fail_str_is_not_digit(self):
        """ проверяет что в строке есть правильный IP адрес """
        self.assertEqual(validate_ip('127.0.Q.1'), False)

    def test_validate_ip_fail_ipport(self):
        """ проверяет что в строке есть правильный IP адрес """
        self.assertEqual(validate_ip('127.0.0.1:8080'), False)

    def test_validate_ip_fail_incorrect_number(self):
        """ проверяет что в строке есть правильный IP адрес """
        self.assertEqual(validate_ip('127.555.0.0'), False)

    def test_validate_port_ok(self):
        """ проверка что строка может являться разрешенным портом """
        self.assertEqual(validate_port('8080'), True)

    def test_validate_port_forbidden(self):
        """ проверка что строка может являться разрешенным портом """
        self.assertEqual(validate_port('1010'), False)

    def test_validate_port_not_number(self):
        """ проверка что строка может являться разрешенным портом """
        self.assertEqual(validate_port('port'), False)

    def test_server_settings_default(self):
        """ проверка запуска командной строки """
        self.assertEqual(server_settings(), [DEFAULT_IP, DEFAULT_PORT])

    def test_send_message(self):
        """
        Тестируем корректность работы фукции отправки,
        создадим тестовый сокет и проверим корректность отправки словаря
        :return:
        """
        # экземпляр тестового словаря, хранит собственно тестовый словарь
        test_socket = TestSocket(self.test_dict_send)
        # вызов тестируемой функции, результаты будут сохранены в тестовом сокете
        send_message(test_socket, self.test_dict_send)
        # проверка корретности кодирования словаря.
        # сравниваем результат довренного кодирования и результат от тестируемой функции
        self.assertEqual(test_socket.encoded_message, test_socket.receved_message)
        # дополнительно, проверим генерацию исключения, при не словаре на входе.
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)

    def test_get_message(self):
        """
        Тест функции приёма сообщения
        :return:
        """
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)
        # тест корректной расшифровки корректного словаря
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)
        # тест корректной расшифровки ошибочного словаря
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


if __name__ == '__main__':
    unittest.main()
