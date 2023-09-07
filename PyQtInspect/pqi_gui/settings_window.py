# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 16:00
# Description: 
# ==============================================
import os

from PyQt5 import QtWidgets, QtGui, QtCore

from PyQtInspect.pqi_gui.settings import getPyCharmPath, findDefaultPycharmPath, setPyCharmPath
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET


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

    def _isValueValid(self) -> bool:
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
        if self._pycharmPathLine._isValueValid():
            setPyCharmPath(self._pycharmPathLine.getValue())
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid PyCharm Path")
            return
        self.close()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = SettingWindow()
    window.show()
    sys.exit(app.exec())
