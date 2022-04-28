import sys
# import time
from PyQt5.QtWidgets import QMainWindow, qApp, QDialog, QMessageBox, QLineEdit, QFileDialog
# QWidget, , QAction, , QApplication, QLabel, QTableView, QPushButton, QComboBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QValidator, QRegExpValidator
from PyQt5 import uic
import os
import logging
from lib.variables import RE_LOGIN_MASK, RE_PASWD_MASK, RE_IPV4_VALIDATOR, RE_PORT_VALIDATOR
import hashlib
import binascii


class MainWindow(QMainWindow):
    ''' Класс описания главного окна серверной части '''

    def __init__(self, database, server, config):
        # Конструктор предка
        super().__init__()

        # База данных сервера
        self.database = database
        self.server_thread = server
        self.config = config

        uic.loadUi('server/ui/server_main_window.ui', self)

        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        self.statusbar.showMessage('сервер трудится...')

        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.show_login_history_button.triggered.connect(self.show_login_history)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)
        # Последним параметром отображаем окно.
        self.show()

    def create_users_model(self):
        '''Метод заполняющий таблицу активных пользователей.'''
        list_users = self.database.active_users_list()
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            # Уберём милисекунды из строки времени, т.к. такая точность не требуется
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(list)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        '''Метод создающий окно со статистикой клиентов.'''
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def show_login_history(self):
        '''Метод создающий окно с историей входов клиентов.'''
        global history_window
        history_window = LoginHistoryWindow(self.database)
        history_window.show()

    def server_config(self):
        '''Метод создающий окно с настройками сервера.'''
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        '''Метод создающий окно регистрации пользователя.'''
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        '''Метод создающий окно удаления пользователя.'''
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()


class StatWindow(QDialog):
    ''' Класс описания окна со статистикой сообщений пользователей '''

    def __init__(self, database):
        super().__init__()
        self.database = database
        uic.loadUi('server/ui/stat_window.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setModal(True)
        self.close_button.clicked.connect(self.close)
        self.create_stat_model()

    def create_stat_model(self):
        '''Метод реализующий заполнение таблицы статистикой сообщений.'''
        # Список записей из базы
        stat_list = self.database.message_history()
        # Объект модели данных:
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
        for row in stat_list:
            user, last_seen, sent, recvd = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(recvd))
            recvd.setEditable(False)
            list.appendRow([user, last_seen, sent, recvd])
        self.stat_table.setModel(list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()


class LoginHistoryWindow(QDialog):
    ''' Класс описания окна истории входов пользователей '''

    def __init__(self, database):
        super().__init__()
        self.database = database
        uic.loadUi('server/ui/login_history_window.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setModal(True)
        self.close_button.clicked.connect(self.close)
        self.create_history_model()

    def create_history_model(self):
        '''Метод реализующий заполнение таблицы историей входов пользователей.'''
        # Список записей из базы
        stat_list = self.database.login_history()
        # Объект модели данных:
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(['Имя Клиента', 'Последний раз входил', 'IP адрес', 'Порт'])
        for row in stat_list:
            user, last_seen, ip, port = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            ip = QStandardItem(str(ip))
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            list.appendRow([user, last_seen, ip, port])
        self.stat_table.setModel(list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()


class DelUserDialog(QDialog):
    ''' Класс описания окна удаления пользователя '''

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        uic.loadUi('server/ui/remove_user.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.btn_ok.clicked.connect(self.remove_user)
        self.btn_cancel.clicked.connect(self.close)
        self.all_users_fill()

        self.messages = QMessageBox()

        self.show()

    def all_users_fill(self):
        ''' метод получения списка всех пользователей '''
        self.selector.addItems([item[0] for item in self.database.users_list()])

    def remove_user(self):
        '''
        метод удаления пользователя:
        удаляет из БД
        рассылает служебное сообщение клиентам для обновления списка контактов
         '''
        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)
        # Рассылаем клиентам сообщение о необходимости обновить справочники
        self.messages.information(self, 'Успех', 'Пользователь удален')
        self.server.service_update_lists()
        self.close()


class RegisterUser(QDialog):
    ''' Класс описания окна создания нового пользователя '''

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        uic.loadUi('server/ui/add_user.ui', self)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # прячем символы в набирамоем пароле
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.client_conf.setEchoMode(QLineEdit.Password)

        client_name_regex = QRegExp(RE_LOGIN_MASK)
        client_pasw_regex = QRegExp(RE_PASWD_MASK)
        client_name_validator = QRegExpValidator(client_name_regex, self.client_name)
        self.client_name.setValidator(client_name_validator)
        passwd_validator = QRegExpValidator(client_pasw_regex, self.client_passwd)
        self.client_passwd.setValidator(passwd_validator)

        self.btn_ok.clicked.connect(self.save_data)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        ''' Метод проверки правильности ввода и сохранения в базу нового пользователя. '''
        if not self.client_name.text():
            self.messages.critical(
                self, 'Ошибка', 'Не указано имя пользователя.')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(
                self, 'Ошибка', 'Введённые пароли не совпадают.')
            return
        elif self.database.check_user(self.client_name.text()):
            self.messages.critical(
                self, 'Ошибка', 'Пользователь уже существует.')
            return
        else:
            # Генерируем хэш пароля, в качестве соли будем использовать логин в
            # нижнем регистре.
            passwd_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac(
                'sha512', passwd_bytes, salt, 10000)
            self.database.add_user(
                self.client_name.text(),
                binascii.hexlify(passwd_hash))
            self.messages.information(
                self, 'Успех', 'Пользователь успешно зарегистрирован.')
            # Рассылаем клиентам сообщение о необходимости обновить справичники
            self.server.service_update_lists()
            self.close()


class ConfigWindow(QDialog):
    '''Класс окна настроек.'''

    def __init__(self, config):
        super().__init__()
        self.config = config
        uic.loadUi('server/ui/config_window.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)
        # self.db_path.setReadOnly(True)

        self.close_button.clicked.connect(self.close)
        self.db_path_select.clicked.connect(self.open_file_dialog)

        ip_regex = QRegExp(RE_IPV4_VALIDATOR)
        ip_validator = QRegExpValidator(ip_regex, self.ip)
        self.ip.setValidator(ip_validator)

        port_regex = QRegExp(RE_PORT_VALIDATOR)
        port_validator = QRegExpValidator(port_regex, self.port)
        self.port.setValidator(port_validator)

        self.show()

        self.db_path.insert(self.config['SETTINGS']['Database_path'])
        self.db_file.insert(self.config['SETTINGS']['Database_file'])
        self.port.insert(self.config['SETTINGS']['Default_port'])
        self.ip.insert(self.config['SETTINGS']['Listen_Address'])
        self.save_btn.clicked.connect(self.save_server_config)

    def open_file_dialog(self):
        global dialog
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_config(self):
        '''
        Метод сохранения настроек. Проверяет правильность введённых данных
        и если всё правильно сохраняет ini файл.
        '''
        global config_window
        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '..')
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    self.config.write(conf)
                    message.information(self, 'OK', 'Настройки успешно сохранены!')
                    self.close()
            else:
                message.warning(self, 'Ошибка', 'Порт должен быть от 1024 до 65536')
