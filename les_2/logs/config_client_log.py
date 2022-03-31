""" Конфиг клиентского логгера """

import sys
import os
from datetime import datetime
import logging

sys.path.append('../')
from lib.variables import LOG_LEVEL, ENCODING, LOG_FORMATTER

# создаём формировщик логов (formatter):
CLIENT_FORMATTER = logging.Formatter(LOG_FORMATTER)

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.log')

# создаём потоки вывода логов
# STREAM_HANDLER = logging.StreamHandler(sys.stderr)
# STREAM_HANDLER.setFormatter(CLIENT_FORMATTER)
# STREAM_HANDLER.setLevel(logging.ERROR)
# STREAM_HANDLER.setLevel(LOG_LEVEL)
LOG_FILE = logging.FileHandler(PATH, encoding=ENCODING)
LOG_FILE.setFormatter(CLIENT_FORMATTER)

# создаём регистратор и настраиваем его
LOGGER = logging.getLogger('client')
# LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOG_LEVEL)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
