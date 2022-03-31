""" Unit-тесты клиента """

import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from lib.variables import *
from client import get_user, create_presence, create_action, process_handler, transport_send


class Test_Client(unittest.TestCase):
    '''  Класс с тестами '''

    def test_get_user_success(self):
        """ Возвращает имя пользователя для авторизации. Только латинские символы, длина от 3 до 25. """
        self.assertEqual("NEW_USER", "NEW_USER")

    def test_presense_guest(self):
        """ проверка присутствия Гостя (Guest)
        {ACTION: PRESENCE,TIME: time.time(), USER: {ACCOUNT_NAME: account_name}}
        """
        test = create_presence()
        test[TIME] = 2  # принудительно меняем ключ в словаре для дальнейшего сравнения
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 2, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_presense_user(self):
        """ проверка присутствия пользователя (не Гостя)
        {ACTION: PRESENCE,TIME: time.time(), USER: {ACCOUNT_NAME: account_name}}
        """
        test = create_presence(account_name='NEW_USER')
        test[TIME] = 2  # принудительно меняем ключ в словаре для дальнейшего сравнения
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 2, USER: {ACCOUNT_NAME: 'NEW_USER'}})

    def test_create_action(self):
        """ Функция отдает словарь с текстом сообщения
         account_name и action обязательны, msg по умолчанию None, в данном тесте заполнен:
         """
        test = create_action(account_name='NEW_USER', action='action', msg='New_Message')
        test[TIME] = 2  # принудительно меняем ключ в словаре для дальнейшего сравнения
        self.assertEqual(test, {ACTION: 'action', TIME: 2, USER: {ACCOUNT_NAME: 'NEW_USER'}, MSG: "New_Message"})

    def test_create_action_none_msg(self):
        """ Функция отдает словарь с текстом сообщения
         account_name и action обязательны, msg по умолчанию None:
         """
        test = create_action(account_name='NEW_USER', action='action')
        test[TIME] = 2  # принудительно меняем ключ в словаре для дальнейшего сравнения
        self.assertEqual(test, {ACTION: 'action', TIME: 2, USER: {ACCOUNT_NAME: 'NEW_USER'}, MSG: None})

    def test_process_handler_not_200ok(self):
        """ проверка ответа от сервера, при отсутствии обязательного поля RESPONCE должна быть ошибка 400"""
        self.assertEqual(process_handler({MSG: 'msg_srv'}), '400:Bad request')

    def test_process_handler_ok(self):
        """ проверка ответа от сервера, корректный ответ - код 200 для {RESPONSE:200, MSG:"не пустое сообщение"}"""
        self.assertEqual(process_handler({RESPONSE: 200, MSG: 'msg_srv'}), "msg_srv")


if __name__ == '__main__':
    unittest.main()
