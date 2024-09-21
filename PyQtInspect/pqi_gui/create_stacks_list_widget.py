import os

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQtInspect.pqi_gui.settings import getPyCharmPath, findDefaultPycharmPath, setPyCharmPath


class CreateStacksListWidget(QtWidgets.QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("stacksListWidget")
        self.setMinimumHeight(200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

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

    def findPycharm(self):
        pycharmPath = getPyCharmPath()
        if not pycharmPath:
            pycharmPath = findDefaultPycharmPath()
            if pycharmPath:
                setPyCharmPath(pycharmPath)
        return pycharmPath

    def openFile(self, fileName: str, lineNo: int):
        # open in Pycharm
        import subprocess
        pycharm = self.findPycharm()
        if pycharm:
            try:
                subprocess.Popen(f'"{pycharm}" --line {lineNo} "{fileName}"', shell=True)
            except Exception as e:
                # message box
                QtWidgets.QMessageBox.critical(self, "Error", f"Error occurred when opening file: {e}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Pycharm not found")
        # subprocess.Popen(f"pycharm64.exe --line {lineNo} {fileName}")
