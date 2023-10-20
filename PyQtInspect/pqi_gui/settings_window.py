# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 16:00
# Description: 
# ==============================================
import os
import contextlib
import io
import threading

from PyQt5 import QtWidgets, QtGui, QtCore

from PyQtInspect.pqi_gui.settings import getPyCharmPath, findDefaultPycharmPath, setPyCharmPath
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET
import PyQtInspect.pqi_gui.data_center as DataCenter

import wingrab


class SimpleSettingLineEdit(QtWidgets.QWidget):
    def __init__(self, parent, key: str, defaultValue: str = ""):
        super().__init__(parent)
        self.setFixedHeight(32)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(10)

        self._keyLabel = QtWidgets.QLabel(self)
        self._keyLabel.setText(key)
        self._keyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._keyLabel.setWordWrap(True)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QLineEdit(self)
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)

    def getValue(self) -> str:
        return self._valueLineEdit.text()


class SimpleComboBox(QtWidgets.QWidget):
    def __init__(self, parent, key: str, defaultValue: str = ""):
        super().__init__(parent)
        self.setFixedHeight(32)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(10)

        self._keyLabel = QtWidgets.QLabel(self)
        self._keyLabel.setText(key)
        self._keyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._keyLabel.setWordWrap(True)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QComboBox(self)
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)

    def getValue(self) -> str:
        return self._valueLineEdit.text()


class PycharmPathSettingLineEdit(SimpleSettingLineEdit):
    def __init__(self, parent):
        super().__init__(parent, "PyCharm Path: ")

        self._openButton = QtWidgets.QPushButton(self)
        self._openButton.setText("...")
        self._openButton.setFixedSize(40, 30)
        self._openButton.clicked.connect(self._openPycharmPath)

        self._layout.addWidget(self._openButton)

        pycharmPathInSettings = getPyCharmPath()
        if not pycharmPathInSettings:
            pycharmPathInSettings = findDefaultPycharmPath()

        self._valueLineEdit.setText(pycharmPathInSettings)

    def _openPycharmPath(self):
        pycharmPath = QtWidgets.QFileDialog.getOpenFileName(self, "Select PyCharm Path",
                                                            self._valueLineEdit.text(),
                                                            "PyCharm Executable Program (*.exe)")
        if pycharmPath:
            self._valueLineEdit.setText(pycharmPath[0])

    def isValueValid(self) -> bool:
        path = self._valueLineEdit.text()
        if not path:
            return False
        return os.path.exists(path) and os.path.isfile(path)


class SettingWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowIcon(QtGui.QIcon("..\\icon.png"))
        self.resize(500, 300)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._pycharmPathLine = PycharmPathSettingLineEdit(self)
        pycharmPathInSettings = getPyCharmPath()
        if not pycharmPathInSettings:
            pycharmPathInSettings = findDefaultPycharmPath()
        self._pycharmPathLine.setValue(pycharmPathInSettings)
        self._mainLayout.addWidget(self._pycharmPathLine)

        self._mainLayout.addStretch()

        self._buttonLayout = QtWidgets.QHBoxLayout()
        self._buttonLayout.setContentsMargins(0, 0, 0, 0)
        self._buttonLayout.setSpacing(5)

        self._saveButton = QtWidgets.QPushButton(self)
        self._saveButton.setFixedSize(100, 40)
        self._saveButton.setText("Save")
        self._saveButton.clicked.connect(self.saveSettings)
        self._buttonLayout.addWidget(self._saveButton)

        self._cancelButton = QtWidgets.QPushButton(self)
        self._cancelButton.setFixedSize(100, 40)
        self._cancelButton.setText("Cancel")
        self._cancelButton.clicked.connect(self.close)
        self._buttonLayout.addWidget(self._cancelButton)

        self._mainLayout.addLayout(self._buttonLayout)

    def saveSettings(self):
        if self._pycharmPathLine.isValueValid():
            setPyCharmPath(self._pycharmPathLine.getValue())
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid PyCharm Path")
            return
        self.close()


class PidLineEdit(SimpleSettingLineEdit):
    sigAttachButtonClicked = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent, "Pid: ")

        self._attachButton = QtWidgets.QPushButton(self)
        self._attachButton.setText("Attach")
        self._attachButton.setFixedHeight(30)
        self._attachButton.clicked.connect(self.sigAttachButtonClicked)

        self._layout.addWidget(self._attachButton)

        self._grabAction = self._valueLineEdit.addAction(QtGui.QIcon(":/cursors/cursor.png"),
                                                         QtWidgets.QLineEdit.TrailingPosition)
        self._grabAction.triggered.connect(self._tryGrab)
        self._grabAction.setToolTip("Get pid from cursor")

    def _tryGrab(self):
        pid = wingrab.grab()
        self._valueLineEdit.setText(str(pid))


class AttachInfoTextBrowser(QtWidgets.QTextBrowser):
    def write(self, text):
        self.append(text)


class AttachWorker(QtCore.QObject):
    sigStdOut = QtCore.pyqtSignal(str)
    sigAttachFinished = QtCore.pyqtSignal()
    sigAttachError = QtCore.pyqtSignal(str)

    class _StdOutGetter(io.StringIO):
        def __init__(self, worker):
            super().__init__()
            self._worker = worker

        def write(self, text):
            super().write(text)
            self._worker.sigStdOut.emit(text)

    def __init__(self, parent, pidToAttach: int):
        super().__init__(parent)
        self._pidToAttach = pidToAttach

    def doWork(self):
        from PyQtInspect.pqi_attach.attach_pydevd import main as attach_main_func

        with contextlib.redirect_stdout(AttachWorker._StdOutGetter(self)):
            try:
                print('Attaching...')
                attach_main_func(
                    {
                        'port': DataCenter.instance.port,
                        'pid': self._pidToAttach,
                        'host': '127.0.0.1',
                        'protocol': '', 'debug_mode': ''
                    }
                )
                print('==================')

                self.sigAttachFinished.emit()
            except Exception as e:
                print(f'Attach Error: {e}\n==================')
                self.sigAttachError.emit(str(e))


class AttachWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Attach to Process")
        self.setWindowIcon(QtGui.QIcon("..\\icon.png"))
        self.resize(500, 300)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(10, 10, 10, 10)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._pidLine = PidLineEdit(self)
        self._pidLine.sigAttachButtonClicked.connect(self._onAttachButtonClicked)
        self._mainLayout.addWidget(self._pidLine)

        self._mainLayout.addSpacing(4)

        self._consoleOutputTextBrowser = AttachInfoTextBrowser(self)
        self._consoleOutputTextBrowser.setReadOnly(True)
        self._mainLayout.addWidget(self._consoleOutputTextBrowser)

        self._thread = None
        self._worker = None

    def _onAttachButtonClicked(self):
        try:
            self._tryAttachToProcess(int(self._pidLine.getValue()))
        except ValueError:
            # todo 如果pid不存在呢??
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid Pid!")
            return

    def _tryAttachToProcess(self, pid: int):
        """ Attach放在这个控件实现吧 """
        from PyQtInspect.pqi_attach.attach_pydevd import main as attach_main_func

        self._pidLine.setEnabled(False)

        self._worker = AttachWorker(None, pid)

        self._thread = QtCore.QThread(None)
        # must move to thread before connect
        self._worker.moveToThread(self._thread)

        self._worker.sigStdOut.connect(self._consoleOutputTextBrowser.write)
        self._worker.sigAttachError.connect(self._onAttachError)
        self._thread.started.connect(self._worker.doWork)
        self._thread.finished.connect(lambda: self._pidLine.setEnabled(True))

        self._worker.sigAttachFinished.connect(self._thread.quit)
        self._thread.start()

    def _onAttachError(self, errMsg):
        QtWidgets.QMessageBox.critical(self, "Error", errMsg)
        self._pidLine.setEnabled(True)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = AttachWindow()
    window.show()
    sys.exit(app.exec())
