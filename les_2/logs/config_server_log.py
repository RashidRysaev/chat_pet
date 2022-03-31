""" Конфиг серверного логгера"""

import sys
import os
from datetime import datetime
# import logging
import logging.handlers

sys.path.append('../')
from lib.variables import LOG_LEVEL, ENCODING, LOG_FORMATTER

# создаём формировщик логов (formatter):
# SERVER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
SERVER_FORMATTER = logging.Formatter(LOG_FORMATTER)

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server_' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.log')

# создаём потоки вывода логов
# STREAM_HANDLER = logging.StreamHandler(sys.stderr)
# STREAM_HANDLER.setFormatter(SERVER_FORMATTER)
# STREAM_HANDLER.setLevel(logging.ERROR)
LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding=ENCODING, interval=1, when='midnight')
LOG_FILE.setFormatter(SERVER_FORMATTER)

# создаём регистратор и настраиваем его
LOGGER = logging.getLogger('server')
# LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOG_LEVEL)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
