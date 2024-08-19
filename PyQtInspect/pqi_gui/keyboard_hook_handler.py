# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2024/8/19 21:24
# Description:
# ==============================================
from PyQt5 import QtCore


class WindowsKeyboardHookHandler(QtCore.QObject):
    sigKeyboardEvent = QtCore.pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()

    def hook(self):
        from . import keyboard_hook

        keyboard_hook.hook(self._onKeyboardEvent)

    def unhook(self):
        from . import keyboard_hook

        keyboard_hook.unhook()

    def _onKeyboardEvent(self, nCode, wParam, lParam):
        self.sigKeyboardEvent.emit(nCode, wParam, lParam)
