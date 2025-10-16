# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/9/7 16:00
# Description: 
# ==============================================
import os

from PyQt5 import QtWidgets, QtCore

from PyQtInspect.pqi_gui._pqi_res import get_icon
from PyQtInspect.pqi_gui.components.simple_kv_line_edit import SimpleSettingLineEdit

from PyQtInspect.pqi_gui.settings import findDefaultPycharmPath, SettingsController
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET


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

    def _openPycharmPath(self):
        pycharmPath = QtWidgets.QFileDialog.getOpenFileName(self, "Select PyCharm Path",
                                                            self._valueLineEdit.text(),
                                                            "PyCharm Executable Program (*.exe)")
        if pycharmPath:
            self._valueLineEdit.setText(os.path.normpath(pycharmPath[0]))

    def isValueValid(self) -> bool:
        path = self._valueLineEdit.text()
        if not path:
            return True  # Updated 20240820: Empty path is valid
        return os.path.exists(path) and os.path.isfile(path)


class SettingWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowIcon(get_icon())
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(500)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 10, 0, 0)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._pycharmPathLine = PycharmPathSettingLineEdit(self)
        pycharmPathInSettings = SettingsController.instance().pyCharmPath
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

        self._mainLayout.addSpacing(4)

    def saveSettings(self):
        if self._pycharmPathLine.isValueValid():
            SettingsController.instance().pyCharmPath = self._pycharmPathLine.getValue()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid PyCharm Path")
            self._pycharmPathLine.clearValue()
            return

        self.close()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = SettingWindow()
    window.show()
    sys.exit(app.exec())
