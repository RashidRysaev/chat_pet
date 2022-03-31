"""Декораторы"""

import sys
import logging
import inspect
import logs.config_server_log
import logs.config_client_log

if sys.argv[0].rfind('server') > 0:
    # имя скрипта содержит server, значит это сервер
    DEC_LOGGER = logging.getLogger('server')
else:
    # =-1, не найдено, значит клент
    DEC_LOGGER = logging.getLogger('client')


def log(called_func):
    """Функция-декоратор"""

    def log_saver(*args, **kwargs):
        """Обертка"""
        ret_log_saver = called_func(*args, **kwargs)
        DEC_LOGGER.debug(f'Called function:{called_func.__module__}.{called_func.__name__}:({args}, {kwargs}). '
                         f'Called from function: {inspect.stack()[1][3]}')
        return ret_log_saver

    return log_saver
