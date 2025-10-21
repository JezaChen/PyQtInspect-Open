# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2025/10/21 23:57
# Description: Common operators for GUI, simplify the connection between modules
# ==============================================
from PyQt5 import QtCore


class CommonOperators(QtCore.QObject):
    _instance = None

    sigOpenSettings = QtCore.pyqtSignal()

    @classmethod
    def instance(cls):
        return cls._instance

    @classmethod
    def initInstance(cls, parent):
        """ Initialize the singleton instance, this method MUST be called before `instance()`
        :param parent: MUST be the main window
        :return: the singleton instance
        """
        if cls._instance is None:
            cls._instance = CommonOperators(parent)
        return cls._instance

    def openSettings(self):
        self.sigOpenSettings.emit()
