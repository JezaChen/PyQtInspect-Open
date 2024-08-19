import contextlib


@contextlib.contextmanager
def log_exception(*, suppress=False):
    from PyQtInspect._pqi_bundle import pqi_log

    try:
        yield
    except Exception as e:
        pqi_log.error(f'Detect exception: {e}', exc_info=True)
        if not suppress:
            raise

