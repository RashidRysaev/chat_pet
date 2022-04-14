""" описание классов окон клиента """
import sys
import logging
from PyQt5.QtWidgets import QWidget, QApplication, qApp, QMainWindow, QDialog
from PyQt5 import uic

logger = logging.getLogger('client')

# функция перенесена
#class UI_MainClientWindow(QMainWindow):
#    def __init__(self):
#        super().__init__()
#        uic.loadUi('client/client_main_gui.ui', self)
#        #self.show()


class UI_StartLoginDlg(QDialog):
    def __init__(self):
        super().__init__()
        self.ok_pressed = False
        uic.loadUi('client/client_start_dialog.ui', self)

        self.btn_ok.clicked.connect(self.ok_click)
        self.btn_cancel.clicked.connect(qApp.exit)
        self.show()

    def ok_click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()

# Диалог выбора контакта для добавления
class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.database = database
        self.transport = transport
        # Загружаем конфигурацию окна из дизайнера
        self.ui = uic.loadUi('client/client_add_contact_dialog.ui', self)
        # связываем кнопки
        self.btn_cancel.clicked.connect(self.close)
        self.btn_refresh.clicked.connect(self.update_possible_contacts)
        # Заполняем список возможных контактов
        self.possible_contacts_update()

    # Заполняем список возможных контактов разницей между всеми пользователями и
    def possible_contacts_update(self):
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
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()


# Диалог выбора контакта для удаления
class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        # Загружаем конфигурацию окна из дизайнера
        self.ui = uic.loadUi('client/client_del_contact_dialog.ui', self)
        # заполнитель контактов для удаления
        self.selector.addItems(sorted(self.database.get_contacts()))
        # связываем кнопки
        self.btn_cancel.clicked.connect(self.close)



if __name__ == '__main__':
    APP = QApplication(sys.argv)

    WINDOW_OBJ = StartLoginDlg()
    WINDOW_OBJ.show()

    a = WINDOW_OBJ.client_name.text()

    print(a)

    WINDOW_OBJ.client_name.setText(a)

    sys.exit(APP.exec_())


