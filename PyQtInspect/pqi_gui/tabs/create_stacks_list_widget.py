import os

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect.pqi_gui.common_operators import CommonOperators
from PyQtInspect.pqi_gui.settings.ide_jumpers import jump_to_ide


class CreateStacksListWidget(QtWidgets.QListWidget):
    tab_name = "Create Stack"

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Message box
        self._messageBox = QtWidgets.QMessageBox(self)
        self._messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        self._messageBox.setWindowTitle('Error')

        self._messageBoxConfigureBtn = self._messageBox.addButton('Configure IDE', QtWidgets.QMessageBox.ButtonRole.ActionRole)
        self._messageBoxOkBtn = self._messageBox.addButton('OK', QtWidgets.QMessageBox.ButtonRole.ActionRole)

    def setStacks(self, stacks: list):
        self.clear()
        for index, stack in enumerate(stacks):
            fileName = stack.get("filename", "")
            normalizedFileName = os.path.normpath(fileName)
            isSrc = os.path.exists(normalizedFileName)

            lineNo = stack.get("lineno", "")
            funcName = stack.get("function", "")
            item = QtWidgets.QListWidgetItem()
            item.setText(f"{index + 1}. {'' if isSrc else '<?> '}File {normalizedFileName}, line {lineNo}: {funcName}")
            # set property
            item.setData(QtCore.Qt.UserRole, (isSrc, normalizedFileName, lineNo))
            self.addItem(item)

    def clearStacks(self):
        self.clear()

    # double click to open file
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None:
                isSrc, fileName, lineNo = item.data(QtCore.Qt.UserRole)
                if isSrc:
                    if fileName:
                        self.openFile(fileName, lineNo)
                else:  # we need to map to our local directory
                    # todo add a dialog to ask user to map the file
                    ...

    def openFile(self, fileName: str, lineNo: int):
        # open in IDE
        try:
            pqi_log.info(f'Opening file: {fileName} at line {lineNo}...')
            jump_to_ide(fileName, lineNo)
        except Exception as e:
            pqi_log.error(f"Failed to jump to IDE: {e}")
            # show message box
            self._messageBox.setText(f"{e}")
            self._messageBox.exec()
            if self._messageBox.clickedButton() == self._messageBoxConfigureBtn:
                CommonOperators.instance().openSettings()

