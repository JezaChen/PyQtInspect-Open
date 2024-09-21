# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2024/8/20 15:25
# Description: Utils for logging
# ==============================================

class log_exception:
    def __init__(self, *, suppress=False):
        self.suppress = suppress

    def __enter__(self):
        from PyQtInspect._pqi_bundle import pqi_log
        self.pqi_log = pqi_log

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.pqi_log.error(f'Detect exception: {exc_val}', exc_info=True)
            if not self.suppress:
                return False
        return True
