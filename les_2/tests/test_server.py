""" Unit-тесты сервера """

import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from lib.variables import *
from server import client_message_handler


class Test_Server(unittest.TestCase):
    '''
    В server.py только 1 функция, возвращающая результат: client_message_handler
    на вход подается словарь с обязательными ключами: ACTION, TIME, USER
        {ACTION: PRESENCE,TIME: time.time(), USER: {ACCOUNT_NAME: 'Guest'}}
    ACTION может быть только из списка (PRESENCE,AUTH,MSG)
    '''
    failed_dict = {RESPONSE: 400, ERROR: ERR400}
    success_dict_guest = {'error': '200:OK', 'msg': 'Welcome, Гость', 'response': 200}
    success_dict_auth_user = {'error': '200:OK', 'msg': 'Welcome, AUTH_USER', 'response': 200}

    def test_fail_message_object(self):
        """ на вход функции подали не словарь """
        self.assertEqual(client_message_handler('AUTH_USER'), self.failed_dict)

    def test_no_key_action(self):
        """ Отсутствие обязательноо ключа ACTION """
        self.assertEqual(client_message_handler({TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.failed_dict)

    def test_no_key_time(self):
        """ Отсутствие обязательноо ключа TIME """
        self.assertEqual(client_message_handler({ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.failed_dict)

    def test_no_key_user(self):
        """ Отсутствие обязательноо ключа USER """
        self.assertEqual(client_message_handler({ACTION: PRESENCE, TIME: '2'}), self.failed_dict)

    def test_wrong_action_value(self):
        """ Для ключа ACTION задано значение не из списка (PRESENCE,AUTH,MSG) """
        self.assertEqual(client_message_handler(
            {ACTION: 'abrakadabra', TIME: '2', USER: {ACCOUNT_NAME: 'Guest'}}), self.failed_dict)

    def test_Guest_with_AUTH(self):
        """ Если ACTION:AUTH и USER='Guest' (для аутентификации должно быть конечное имя). """
        self.assertEqual(client_message_handler(
            {ACTION: AUTH, TIME: '2', USER: {ACCOUNT_NAME: 'Guest'}}), self.failed_dict)

    def test_Guest_with_MSG(self):
        """ Если ACTION:AUTH и USER='Guest' (сообщение гость слать не может). """
        self.assertEqual(client_message_handler(
            {ACTION: MSG, TIME: '2', USER: {ACCOUNT_NAME: 'Guest'}}), self.failed_dict)

    def test_Success_PRESENCE_Guest(self):
        """ Если ACTION:PRESENCE и USER='Guest'"""
        self.assertEqual(client_message_handler(
            {ACTION: PRESENCE, TIME: '2', USER: {ACCOUNT_NAME: 'Guest'}}), self.success_dict_guest)

    def test_Success_PRESENCE_not_Guest(self):
        """ Если ACTION:PRESENCE и USER!='Guest' """
        self.assertEqual(client_message_handler(
            {ACTION: PRESENCE, TIME: '2', USER: {ACCOUNT_NAME: 'AUTH_USER'}}), self.success_dict_guest)

    def test_Success_AUTH_not_Guest(self):
        """ Если ACTION:AUTH и USER!='Guest' """
        self.assertEqual(client_message_handler(
            {ACTION: AUTH, TIME: '2', USER: {ACCOUNT_NAME: 'AUTH_USER'}}), self.success_dict_auth_user)

    def test_Success_MSG_not_Guest(self):
        """ Если ACTION:AUTH и USER!='Guest' """
        self.assertEqual(client_message_handler(
            {ACTION: AUTH, TIME: '2', USER: {ACCOUNT_NAME: 'AUTH_USER'}}), self.success_dict_auth_user)


if __name__ == '__main__':
    unittest.main()
