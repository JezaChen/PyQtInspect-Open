# -*- encoding:utf-8 -*-


class _DummyLogger:
    def _func(self, *args, **kwargs): pass

    def __getattr__(self, item):
        return self._func


def _get_trace_level():
    from PyQtInspect._pqi_bundle.pqi_contants import DebugInfoHolder

    return DebugInfoHolder.LOG_TO_FILE_LEVEL, DebugInfoHolder.LOG_TO_CONSOLE_LEVEL


def get_logger():
    from PyQtInspect._pqi_common.pqi_setup_holder import SetupHolder

    if SetupHolder.setup is None:
        return _DummyLogger

    if SetupHolder.setup.get('server'):
        from ._server import logger
    else:
        from ._client import logger

    file_log_level, console_log_level = _get_trace_level()
    logger.set_console_log_level(file_log_level)
    logger.set_file_log_level(console_log_level)
    return logger


def debug(msg, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    get_logger().critical(msg, *args, **kwargs)
