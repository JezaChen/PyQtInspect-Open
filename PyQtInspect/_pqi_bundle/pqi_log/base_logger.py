# -*- coding:utf-8 _*-

import logging
import os
import pathlib
import time
import traceback
import io
import sys
import contextlib

__logger_cache = {}
_PROGRAM_DIR_PATH = pathlib.Path.home() / '.PyQtInspect'
_LOG_DIR_PATH = _PROGRAM_DIR_PATH / 'logs'
if not _LOG_DIR_PATH.exists():
    _LOG_DIR_PATH.mkdir(parents=True)


def getLogDirPath() -> pathlib.Path:
    return _LOG_DIR_PATH


def getOldLogDirPath() -> pathlib.Path:
    # For old versions, log files were stored in a different directory.
    return _PROGRAM_DIR_PATH / 'log'

# Bugfix #45: Incorrect filename and lineno in logs
# Ref: https://github.com/JezaChen/PyQtInspect-Open/issues/45
# When encapsulating the logging module with a custom wrapper module pqi_log,
# the log output incorrectly records the source file and line number of the wrapper itself,
# rather than the actual caller's location.
# So we need to create a custom Logger class that skips internal frames of pqi_log module.
#
# Actually, for Python 3.8+, logging module provides `stacklevel` parameter to logging functions,
# which can be used to adjust the stack frame level for caller information.
# However, to maintain compatibility with older Python versions (3.7), we implement a custom Logger class here.

@contextlib.contextmanager
def _use_custom_logger_class(new_logger_class):
    """ A context manager to temporarily set a custom logger class. """
    orig_logger_class = logging.getLoggerClass()
    logging.setLoggerClass(new_logger_class)
    try:
        yield
    finally:
        logging.setLoggerClass(orig_logger_class)  # Restore original logger class

# vvv Copied from logging module vvv

# _srcfile in logging module, renamed to `_logging_module_init_srcfile`
_logging_module_init_srcfile = os.path.normcase(logging.addLevelName.__code__.co_filename)
# Additionally, we add pqi_log module path to be skipped
_pqi_log_module_path = os.path.normcase(str(pathlib.Path(getLogDirPath.__code__.co_filename).parent.resolve()))

# Copied verbatim
if hasattr(sys, "_getframe"):
    _currentframe = lambda: sys._getframe(1)
else:  # pragma: no cover
    def _currentframe():
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except Exception:
            return sys.exc_info()[2].tb_frame.f_back


def _is_internal_frame(frame):
    """Signal whether the frame is a CPython or logging module internal.
    Copying from logging module
    """
    filename = os.path.normcase(frame.f_code.co_filename)
    return filename == _logging_module_init_srcfile or (
            filename.startswith(_pqi_log_module_path)  # Newly added to also skip pqi_log internal frames, not just logging module ones
    ) or (
            "importlib" in filename and "_bootstrap" in filename
    )


class _PqiCustomLogger(logging.Logger):
    # Copied from logging module's Logger.findCaller, with slight modifications (use custom `_is_internal_frame` function)
    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = _currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is None:
            return "(unknown file)", 0, "(unknown function)", None
        while stacklevel > 0:
            next_f = f.f_back
            if next_f is None:
                ## We've got options here.
                ## If we want to use the last (deepest) frame:
                break
                ## If we want to mimic the warnings module:
                # return ("sys", 1, "(unknown function)", None)
                ## If we want to be pedantic:
                # raise ValueError("call stack is not deep enough")
            f = next_f
            if not _is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = None
        if stack_info:
            with io.StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
        return co.co_filename, f.f_lineno, co.co_name, sinfo


def getLogger(logger_name='PyQtInspect', console_log_level=logging.INFO, file_log_level=logging.INFO):
    if logger_name in __logger_cache:
        return __logger_cache[logger_name]

    with _use_custom_logger_class(_PqiCustomLogger):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # 1. Console
        sh = logging.StreamHandler()
        sh.setLevel(console_log_level)
        # 2. File
        t = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime((time.time())))
        log_name = f'{logger_name}_{os.getpid()}_{t}.log'
        log_path = _LOG_DIR_PATH.joinpath(log_name)
        # Fix issue #18: use UTF-8 encoding for log files to avoid garbled characters
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setLevel(file_log_level)

        # Format
        shFormatter = logging.Formatter(
            '[PyQtInspect][%(asctime)s][%(filename)s - %(funcName)s: line %(lineno)d][%(levelname)s] %(message)s'
        )
        sh.setFormatter(shFormatter)

        fhFormatter = logging.Formatter(
            '[%(asctime)s][%(filename)s - %(funcName)s: line %(lineno)d][%(levelname)s] %(message)s')
        fh.setFormatter(fhFormatter)

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
