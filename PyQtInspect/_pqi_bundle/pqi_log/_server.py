# -*- encoding:utf-8 -*-
# PyQtInspect Logger for Server
import logging

from PyQtInspect._pqi_bundle.pqi_log.base_logger import getLogger


def _get_console_log_level():
    return logging.WARNING


def _get_file_log_level():
    return logging.INFO


logger = getLogger(
    logger_name='pqi_server',
    console_log_level=_get_console_log_level(),
    file_log_level=_get_file_log_level()
)
