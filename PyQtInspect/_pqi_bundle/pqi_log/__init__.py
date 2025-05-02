# -*- encoding:utf-8 -*-

from .base_logger import getLogDirPath

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

    if SetupHolder.setup.get(SetupHolder.KEY_SERVER):
        from ._server import logger
    else:
        from ._client import logger

    file_log_level, console_log_level = _get_trace_level()
    logger.set_console_log_level(console_log_level)
    logger.set_file_log_level(file_log_level)
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


def clear_logs():
    from PyQtInspect._pqi_bundle.pqi_log.base_logger import getLogDirPath, getOldLogDirPath

    log_dir = getLogDirPath()
    old_log_dir = getOldLogDirPath()

    for d in (log_dir, old_log_dir):
        if not d.exists():
            info(f"Log directory {d} does not exist.")
            continue
        for file in d.glob('*.log'):
            try:
                file.unlink()
            except Exception as e:
                # occurs when the file is in use (by the current process) or permission denied
                info(f"Failed to delete log file {file}: {e}")
        info("All log files cleared.")

    # Try to delete the old log directory if it exists
    if old_log_dir.exists():
        try:
            old_log_dir.rmdir()
            info(f"Old log directory {old_log_dir} deleted.")
        except Exception as e:
            info(f"Failed to delete old log directory {old_log_dir}: {e}")
    else:
        info(f"Old log directory {old_log_dir} does not exist.")
