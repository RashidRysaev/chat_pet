import sys
import logging
from PyQt5.QtWidgets import QWidget, QApplication, qApp, QMainWindow, QDialog, QLineEdit, QMessageBox, QListView
from PyQt5 import uic
from PyQt5.QtGui import QValidator, QRegExpValidator, QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import QRegExp, pyqtSlot, QEvent, Qt
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
import base64
import json
from lib.variables import *
from lib.errors import ServerError
logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    '''
    Класс - основное окно пользователя.
    Содержит всю основную логику работы клиентского модуля.
    Конфигурация окна создана в QTDesigner и загружается из
    конвертированого файла main_window_conv.py
    '''

    def __init__(self, database, transport, keys):
        super().__init__()
        # основные переменные
        self.database = database
        self.transport = transport

        # объект - дешифорвщик сообщений с предзагруженным ключём
        self.decrypter = PKCS1_OAEP.new(keys)

        # Загружаем конфигурацию окна из дизайнера
        self.ui = uic.loadUi('client/ui/client_main_gui.ui', self)
        # self.ui = Ui_MainClientWindow()
        # self.ui.setupUi(self)

        # Кнопка "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)
        # отправить сообшщение по Enter
        # self.text_message.returnPressed.connect(self.send_message)


        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        # Кнопка стереть набранное сообщение
        self.ui.btn_clear.clicked.connect(self.clear_message)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        ''' Метод делающий поля ввода неактивными'''
        # Надпись  - получатель.
        self.ui.label_new_message.setText(
            'Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def history_list_update(self):
        '''
        Метод заполняющий соответствующий QListView
        историей переписки с текущим собеседником.
        '''
        # Получаем историю сортированную по дате
        list = sorted(
            self.database.get_history(
                self.current_chat),
            key=lambda item: item[3])
        # Если модель не создана, создадим.
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 20 последних записей.
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так-же стоит разделить входящие
        # и исходящие выравниванием и разным фоном.
        # отображает только последие 20 сообщений
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        '''Метод обработчик события двойного клика по списку контактов.'''
        # Выбранный пользователем (даблклик) находится в выделеном элементе в
        # QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # вызываем основную функцию
        self.set_active_user()

    def set_active_user(self):
        '''Метод активации чата с собеседником.'''
        # Запрашиваем публичный ключ пользователя и создаём объект шифрования
        try:
            self.current_chat_key = self.transport.key_request(
                self.current_chat)
            logger.debug(f'Загружен открытый ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(
                    RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            logger.debug(f'Не удалось получить ключ для {self.current_chat}')

        # Если ключа нет то ошибка, что не удалось начать чат с пользователем
        if not self.current_chat_key:
            self.messages.warning(
                self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        # Ставим надпись и активируем кнопки
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    def clients_list_update(self):
        '''Метод обновляющий список контактов.'''
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        '''Метод создающий окно - диалог добавления контакта'''
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        '''Метод обработчк нажатия кнопки "Добавить"'''
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        '''
        Метод добавляющий контакт в серверную и клиентсткую BD.
        После обновления баз данных обновляет и содержимое окна.
        '''
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    def delete_contact_window(self):
        '''Метод создающий окно удаления контакта.'''
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        '''
        Метод удаляющий контакт из серверной и клиентсткой BD.
        После обновления баз данных обновляет и содержимое окна.
        '''
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def clear_message(self):
        self.ui.text_message.clear()


    def send_message(self):
        '''
        Функция отправки сообщения текущему собеседнику.
        Реализует шифрование сообщения и его отправку.
        '''
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение
        # и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.clear_message()
        #self.ui.text_message.clear()
        if not message_text:
            return
        # Шифруем сообщение ключом получателя и упаковываем в base64.
        message_text_encrypted = self.encryptor.encrypt(message_text.encode(ENCODING))
        message_text_encrypted_base64 = base64.b64encode(
            message_text_encrypted)
        try:
            self.transport.send_message(
                self.current_chat,
                message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(
                self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            logger.debug(
                f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(dict)
    def message(self, message):
        '''
        Слот обработчик поступаемых сообщений, выполняет дешифровку
        поступаемых сообщений и их сохранение в истории сообщений.
        Запрашивает пользователя если пришло сообщение не от текущего
        собеседника. При необходимости меняет собеседника.
        '''
        # Получаем строку байтов
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        # Декодируем строку, при ошибке выдаём сообщение и завершаем функцию
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(
                self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return
        # Сохраняем сообщение в базу и обновляем историю сообщений или
        # открываем новый чат.
        self.database.save_message(
            self.current_chat,
            'in',
            decrypted_message.decode(ENCODING))

        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                # Если есть, спрашиваем о желании открыть с ним чат
                if self.messages.question(self,'Новое сообщение',
                    f'Получено новое сообщение от {sender}, открыть чат с ним?',
                    QMessageBox.Yes,QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    # теряется сообщение если чат был не открыт
                    self.database.save_message(self.current_chat, 'in', decrypted_message.decode(ENCODING))
                    self.set_active_user()
            else:
                # print('NO')
                # Раз нету,спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(self,'Новое сообщение',
                    f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.'
                    f'\n Добавить в контакты и открыть чат с ним?',
                    QMessageBox.Yes,QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    # Нужно заново сохранить сообщение, иначе оно будет потеряно,
                    # т.к. на момент предыдущего вызова контакта не было.
                    self.database.save_message(self.current_chat, 'in', decrypted_message.decode(ENCODING))
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        '''
        Слот обработчик потери соеднинения с сервером.
        Выдаёт окно предупреждение и завершает работу приложения.
        '''
        self.messages.warning(self,'Сбой соединения','Потеряно соединение с сервером. ')
        self.close()

    @pyqtSlot()
    def sig_205(self):
        '''
        Слот выполняющий обновление баз данных по команде сервера.
        '''
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(self,'Внимание.',
                'К сожалению собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        '''Метод обеспечивающий соединение сигналов и слотов.'''
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)


class UI_StartLoginDlg(QDialog):
    ''' Класс реализующий стартовый диалог с запросом логина и пароля пользователя. '''
    def __init__(self):
        super().__init__()
        self.ok_pressed = False
        uic.loadUi('client/ui/client_start_dialog.ui', self)
        client_name_regex = QRegExp(RE_LOGIN_MASK)
        client_pasw_regex = QRegExp(RE_PASWD_MASK)

        client_name_validator=QRegExpValidator(client_name_regex, self.client_name)
        self.client_name.setValidator(client_name_validator)

        passwd_validator=QRegExpValidator(client_pasw_regex, self.client_passwd)
        self.client_passwd.setValidator(passwd_validator)

        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.btn_ok.clicked.connect(self.ok_click)
        self.btn_cancel.clicked.connect(qApp.exit)
        self.show()

    def ok_click(self):
        ''' Метод обрабтчик кнопки ОК. '''
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()


class AddContactDialog(QDialog):
    '''
    Класс окна добавления пользователя в список контактов.
    Предлагает пользователю список возможных контактов и
    добавляет выбранный в контакты.
    '''
    def __init__(self, transport, database):
        super().__init__()
        self.database = database
        self.transport = transport
        # Загружаем конфигурацию окна из дизайнера
        self.ui = uic.loadUi('client/ui/client_add_contact_dialog.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)
        # связываем кнопки
        self.btn_cancel.clicked.connect(self.close)
        self.btn_refresh.clicked.connect(self.update_possible_contacts)
        # Заполняем список возможных контактов
        self.possible_contacts_update()

    # Заполняем список возможных контактов разницей между всеми пользователями и
    def possible_contacts_update(self):
        '''
        Метод заполнения списка возможных контактов.
        Создаёт список всех зарегистрированных пользователей
        за исключением уже добавленных в контакты и самого себя.
        '''
        self.selector.clear()
        # множества всех контактов и контактов клиента
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        # Удалим сами себя из списка пользователей, чтобы нельзя было добавить самого себя
        users_list.remove(self.transport.username)
        # Добавляем список возможных контактов
        self.selector.addItems(users_list - contacts_list)

    # Обновлялка возможных контактов. Обновляет таблицу известных пользователей,
    # затем содержимое предполагаемых контактов
    def update_possible_contacts(self):
        '''
        Метод обновления списка возможных контактов. Запрашивает с сервера
        список известных пользователей и обносляет содержимое окна.
        '''
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()


class DelContactDialog(QDialog):
    ''' Класс окна удаления контакта. Предлагает текущий список контактов '''
    def __init__(self, database):
        super().__init__()
        self.database = database
        # Загружаем конфигурацию окна из дизайнера
        self.ui = uic.loadUi('client/ui/client_del_contact_dialog.ui', self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)
        # связываем кнопки
        self.btn_cancel.clicked.connect(self.close)
        # заполнитель контактов для удаления
        self.selector.addItems(sorted(self.database.get_contacts()))



if __name__ == '__main__':
    APP = QApplication(sys.argv)

    WINDOW_OBJ = DelContactDialog()
    WINDOW_OBJ.show()

    a = WINDOW_OBJ.client_name.text()

    print(a)

    WINDOW_OBJ.client_name.setText(a)

    sys.exit(APP.exec_())


