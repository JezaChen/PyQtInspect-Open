# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2024/8/19 21:24
# Description:
# ==============================================
import abc

from PyQt5 import QtCore


class KeyboardHookHandler(QtCore.QObject):
    sigDisableInspectKeyPressed = QtCore.pyqtSignal()

    @classmethod
    def __new__(cls, *args, **kwargs):
        """ Factory method to create a proper instance according to the platform. """

        import sys
        if sys.platform == 'win32':
            class_ = WindowsKeyboardHookHandler
        else:
            class_ = DummyKeyboardHookHandler
        ins = super().__new__(class_)
        return ins

    def __init__(self, parent=None):
        super().__init__(parent)

    def isValid(self) -> bool:
        return True

    @abc.abstractmethod
    def onInspectFinished(self): ...

    @abc.abstractmethod
    def onInspectBegin(self): ...

    @abc.abstractmethod
    def onInspectDisabled(self): ...

    @abc.abstractmethod
    def setEnable(self, enable: bool): ...


class WindowsKeyboardHookHandler(KeyboardHookHandler):
    """ Keyboard hook handler for Windows platform. """
    sigKeyboardEvent = QtCore.pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._keyboardHookThread = self._generateKeyboardHookThread()
        self._enabled = True  # default enabled
        self._inspecting = False

    def _generateKeyboardHookThread(self):
        """ Initialize a thread to grab keyboard event. """
        from PyQtInspect._pqi_bundle.pqi_keyboard_hook_win import GrabFlag

        def _inSubThread():
            import PyQtInspect._pqi_bundle.pqi_keyboard_hook_win as kb_hook
            kb_hook.grab(0x77, flag, lambda: self.sigDisableInspectKeyPressed.emit())

        thread = QtCore.QThread(self)
        flag = GrabFlag()  # Flag to indicate the internal grab thread to stop, used to solve the issue where grab thread still cannot exit after GUI program exits
        thread.started.connect(_inSubThread)
        thread.stop_flag = flag
        return thread

    def _stopKeyboardHookThread(self):
        if self._keyboardHookThread.isRunning():
            self._keyboardHookThread.stop_flag.mark_stop()
            self._keyboardHookThread.quit()

    def _onKeyboardEvent(self, nCode, wParam, lParam):
        self.sigKeyboardEvent.emit(nCode, wParam, lParam)

    def _startKeyboardHookThread(self):
        # start keyboard hook thread if user wants to disable inspect by pressing F8
        # TODO: 1) Custom hotkeys; 2) When user turns on the switch and is in inspect mode, immediately run the thread
        self._keyboardHookThread.stop_flag.clear_flag()
        self._keyboardHookThread.start()

    # region Override methods
    def onInspectFinished(self):
        self._inspecting = False
        self._stopKeyboardHookThread()

    def onInspectBegin(self):
        self._inspecting = True
        if not self._enabled:
            return
        self._startKeyboardHookThread()

    def onInspectDisabled(self):
        self._inspecting = False
        self._stopKeyboardHookThread()

    def setEnable(self, enable: bool):
        self._enabled = enable
        if not enable:
            self._stopKeyboardHookThread()
        elif self._inspecting:  # enable and inspecting
            # start keyboard hook thread during inspecting
            self._startKeyboardHookThread()
    # endregion


class DummyKeyboardHookHandler(KeyboardHookHandler):
    """  For non-windows platform, do nothing. """
    def _dummy(self): ...

    onInspectFinished = onInspectBegin = onInspectDisabled = setEnable = _dummy

    def isValid(self) -> bool:
        return False