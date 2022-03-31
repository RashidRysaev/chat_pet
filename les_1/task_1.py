"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping
будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять
их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес
сетевого узла должен создаваться с помощью функции ip_address().
"""
import ipaddress
import socket
import os
from platform import system
import subprocess
import chardet


def os_ping(ip_adr):
    oper = system()  # версия ОС, для определения метода ping

    DNULL = open(os.devnull, "w")

    if (oper == "Windows"):
        try:
            # status = subprocess.call(["ping", "-n", "1", str(ip_adr)], stdout=DNULL)
            res_bytes = subprocess.check_output(f'ping -n 1 {str(ip_adr)}')
            code_dic = chardet.detect(res_bytes)
            res_str = res_bytes.decode(code_dic['encoding']).encode('utf-8')
            res = res_str.decode('utf-8')
            status = res.find('TTL=')
            if status >= 0:
                status = 0
            else:
                status = 1  # подстрока TTL не найдена
        except:
            status = 1
    else:
        status = subprocess.call(["ping", "-c", "1", str(ip_adr)], stdout=DNULL)
    # print(f"{ip_adr} | status={status}")
    return status


def host_ping(v_loop_ip):
    """ функция создаст словари доступности адресов """
    succes_request = "Узел доступен"
    fail_request = "Узел недоступен"
    fail_ip_adr = "Имя узла задано некорректно"

    columns = ['адрес', 'результат']
    result = []

    print("Сканер запущен...")

    i = 0  # счетчик для отображения статуса
    for ip in v_loop_ip:
        request_dic = dict()
        try:
            ip_adr = ipaddress.ip_address(ip)
            status = os_ping(ip_adr)
            if status == 0:
                request_dic[columns[0]] = str(ip_adr)
                request_dic[columns[1]] = succes_request
            else:
                request_dic[columns[0]] = str(ip_adr)
                request_dic[columns[1]] = fail_request
        except:
            try:
                ip_adr = socket.gethostbyname(ip)
                status = os_ping(ip_adr)
                if status == 0:
                    request_dic[columns[0]] = str(ip)  # внесём доменное имя
                    request_dic[columns[1]] = succes_request
                else:
                    request_dic[columns[0]] = str(ip)  # внесём доменное имя
                    request_dic[columns[1]] = fail_request
            except:
                request_dic[columns[0]] = str(ip)  # внесем ip, хоть это и не является адресом
                request_dic[columns[1]] = fail_ip_adr
        result.append(request_dic)
        print(f"{result[i][columns[0]]} | {result[i][columns[1]]}")
        i += 1
    return result

# список адресов на проверку
loop_ip = ['192.168.1.1', '192.168.1.2', '127.0.0.1', '192.168.0.1', '192.168.1.126', '127', 'ya.ru']
host_ping(loop_ip)
print("Готово.")

"""
Сканер запущен...
192.168.1.1 | Узел доступен
192.168.1.2 | Узел недоступен
127.0.0.1 | Узел доступен
192.168.0.1 | Узел недоступен
192.168.1.126 | Узел недоступен
127 | Имя узла задано некорректно
ya.ru | Узел доступен
Готово.

"""