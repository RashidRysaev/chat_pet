""" Служебный скрипт запуска/останова нескольких клиентских приложений """
from subprocess import Popen, CREATE_NEW_CONSOLE

P_LIST = []

while True:
    USER = input("Запустить клиентов (s) / Закрыть клиентов (k) / Выйти (q) ")

    if USER == 'q':
        break

    elif USER == 's':
        P_LIST.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))
        P_LIST.append(Popen('python client.py', creationflags=CREATE_NEW_CONSOLE))
        P_LIST.append(Popen('python client.py -l', creationflags=CREATE_NEW_CONSOLE))
        P_LIST.append(Popen('python client.py -l', creationflags=CREATE_NEW_CONSOLE))

        print(' Запущены  несколько listen клиентов и клиент-писатель')
    elif USER == 'k':
        for p in P_LIST:
            p.kill()
        P_LIST.clear()
