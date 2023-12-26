# -*- coding:utf-8 _*-

import logging
import os
import pathlib
import time

__logger_cache = {}
_PROGRAM_DIR_PATH = pathlib.Path.home() / '.PyQtInspect'
_LOG_DIR_PATH = _PROGRAM_DIR_PATH / 'log'
if not _LOG_DIR_PATH.exists():
    _LOG_DIR_PATH.mkdir(parents=True)


def getLogger(logger_name='PyQtInspect', console_log_level=logging.INFO, file_log_level=logging.INFO):
    if logger_name in __logger_cache:
        return __logger_cache[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # 1. Console
    sh = logging.StreamHandler()
    sh.setLevel(console_log_level)
    # 2. File
    rq = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime((time.time())))
    log_name = f'{logger_name}_{os.getpid()}_{rq}.log'
    log_path = _LOG_DIR_PATH.joinpath(log_name)
    fh = logging.FileHandler(log_path)
    fh.setLevel(file_log_level)

    # Format
    formatter = logging.Formatter('[%(asctime)s][%(filename)s: line %(lineno)d][%(levelname)s] %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(sh)

    # Monkey patch for dynamic log level setting
    def set_console_log_level(level):
        if sh.level == level:
            return
        sh.setLevel(level)

    def set_file_log_level(level):
        if fh.level == level:
            return
        fh.setLevel(level)

    logger.set_console_log_level = set_console_log_level
    logger.set_file_log_level = set_file_log_level

    __logger_cache[logger_name] = logger
    return logger
