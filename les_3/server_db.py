from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from lib.variables import *
import datetime

import logs.config_server_log

SERVER_LOGGER = logging.getLogger('server')


# Класс - серверная база данных:
class ServerStorage:
    # Класс - отображение таблицы всех пользователей
    # Экземпляр этого класса = запись в таблице AllUsers
    class AllUsers:
        def __init__(self, username):
            self.login_name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    # Класс - отображение таблицы активных пользователей:
    # Экземпляр этого класса = запись в таблице ActiveUsers
    class OnLineUsers:
        def __init__(self, user_id, ip_address, ip_port, login_time):
            self.user_id = user_id
            self.ip_address = ip_address
            self.ip_port = ip_port
            self.login_time = login_time
            self.id = None

    # Класс - отображение таблицы истории входов
    # Экземпляр этого класса = запись в таблице LoginHistory
    class LoginHistory:
        def __init__(self, user_id, date, ip_address, ip_port):
            self.id = None
            self.user_id = user_id
            self.date_time = date
            self.ip_address = ip_address
            self.ip_port = ip_port

    def __init__(self):
        # Создаём движок базы данных
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=3600)

        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаём таблицу пользователей
        all_users_table = Table('All_Users', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('login_name', String, unique=True),
                                Column('last_login', DateTime)
                                )

        # Создаём таблицу активных пользователей
        online_users_table = Table('Online_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('All_Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('ip_port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # Создаём таблицу истории входов
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('All_Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip_address', String),
                                   Column('ip_port', String)
                                   )

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        # Связываем класс в ORM с таблицей
        mapper(self.AllUsers, all_users_table)
        mapper(self.OnLineUsers, online_users_table)
        mapper(self.LoginHistory, user_login_history)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.OnLineUsers).delete()
        self.session.commit()

    # Функция выполняющяяся при входе пользователя, записывает в базу факт входа
    def user_login(self, username, ip_address, ip_port):
        SERVER_LOGGER.info(f"user login: {username} {ip_address}:{ip_port}")
        # print(f"подключился пользователь: {username} {ip_address} {ip_port}")
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        result = self.session.query(self.AllUsers).filter_by(login_name=username)
        SERVER_LOGGER.debug(f"user_login result query:{result}")
        # print(type(rez))
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаём нового пользователя
        else:
            SERVER_LOGGER.info(f"new user, add to DB {username} {ip_address}:{ip_port}")
            # Создаем экземпляр класса self.AllUsers, через который передаем данные в таблицу
            user = self.AllUsers(username)
            self.session.add(user)
            # Коммит здесь нужен, чтобы присвоился ID
            self.session.commit()

        # добавляем пользователя в таблицу активных и в таблицу истории входа
        new_active_user = self.OnLineUsers(user.id, ip_address, ip_port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, ip_port)
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

    # Функция фиксирующая отключение пользователя
    def user_logout(self, username):
        # username=username.upper()
        # Запрашиваем пользователя, что покидает нас
        # получаем запись из таблицы AllUsers
        user = self.session.query(self.AllUsers).filter_by(login_name=username).first()
        print(f"logout username {username} | {user}")

        # Удаляем его из таблицы активных пользователей.
        # Удаляем запись из таблицы ActiveUsers
        self.session.query(self.OnLineUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    # Функция возвращает список известных пользователей со временем последнего входа.
    def users_list(self):
        query = self.session.query(
            self.AllUsers.login_name,
            self.AllUsers.last_login,
        )
        # Возвращаем список кортежей
        return query.all()

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = self.session.query(
            self.AllUsers.login_name,
            self.OnLineUsers.ip_address,
            self.OnLineUsers.ip_port,
            self.OnLineUsers.login_time
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()

    # Функция возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        # Запрашиваем историю входа
        query = self.session.query(self.AllUsers.login_name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip_address,
                                   self.LoginHistory.ip_port
                                   ).join(self.AllUsers)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.login_name == username)
        return query.all()


# Отладка
if __name__ == '__main__':
    test_db = ServerStorage()

    # старт сервера, активных пользователей не должно быть
    print("---- start server. active_users_list ----")
    print(test_db.active_users_list())

    # 'подключение' пользователя
    print("---- добавление пользователей client_1 client_2 client_3 client_4 ----")
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    test_db.user_login('client_3', '192.168.0.0', 9999)
    test_db.user_login('client_4', '192.168.4.4', 4444)
    # выводим список активных пользователей
    print("---- active_users_list ----")
    print(test_db.active_users_list())

    # 'отключение' пользователя
    print("---- отключили пользователя client_1 -- active_users_list ----")
    test_db.user_logout('client_1')
    print(test_db.active_users_list())

    # запрашиваем историю входов по пользователю
    print("---- login_history  ----")
    print(test_db.login_history('client_1'))

    # выводим список известных пользователей
    print(test_db.users_list())

    # 'отключение' пользователя
    test_db.user_logout('client_4')
    print("---- отключили пользователя client_4 -- active_users_list ----")
    print(test_db.active_users_list())
