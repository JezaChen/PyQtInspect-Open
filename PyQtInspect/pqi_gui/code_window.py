# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 20:49
# Description: 
# ==============================================
from PyQt5 import QtWidgets, QtGui, QtCore
from io import StringIO
from contextlib import redirect_stdout

from PyQtInspect.pqi_gui._pqi_res import get_icon
from PyQtInspect.pqi_gui.syntax import PythonHighlighter

CODE_TEXT_EDIT_STYLESHEET = """
QTextEdit#CodeTextEdit {
    font: 14px "Consolas";
}

QTextEdit#ResultTextBrowser {
    font: 14px "Consolas";
}
"""

PROMPT = """# In the following code, self refers to the selected widget. 
# For example, if you want to resize the widget, you can type self.setFixedSize(10, 10).
"""


class CodeTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeTextEdit")

    def event(self, e: QtCore.QEvent) -> bool:
        if e.type() == QtCore.QEvent.KeyPress:
            if e.key() == QtCore.Qt.Key_Tab:
                self.insertPlainText("    ")
                return True
        return super().event(e)


class ResultTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultTextBrowser")
        self.setReadOnly(True)


class CodeWindow(QtWidgets.QDialog):
    sigExecCode = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exec Code For Selected Widget")
        self.setWindowIcon(get_icon())
        self.resize(800, 500)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._codeTextEdit = CodeTextEdit(self)
        self._codeTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._codeTextEdit.setText(PROMPT)
        self._codeTextEdit.setWordWrapMode(QtGui.QTextOption.NoWrap)

        self._highlight = PythonHighlighter(self._codeTextEdit.document())
        self._mainLayout.addWidget(self._codeTextEdit)

        self._resultTextBrowser = ResultTextBrowser(self)
        self._resultTextBrowser.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._mainLayout.addWidget(self._resultTextBrowser)

        self._buttonLayout = QtWidgets.QHBoxLayout()
        self._buttonLayout.setContentsMargins(0, 0, 0, 0)
        self._buttonLayout.setSpacing(5)

        self._runButton = QtWidgets.QPushButton(self)
        self._runButton.setFixedSize(100, 40)
        self._runButton.setText("Run")
        self._runButton.clicked.connect(self._runCode)
        self._buttonLayout.addWidget(self._runButton)

        self._cancelButton = QtWidgets.QPushButton(self)
        self._cancelButton.setFixedSize(100, 40)
        self._cancelButton.setText("Close")
        self._cancelButton.clicked.connect(self.close)
        self._buttonLayout.addWidget(self._cancelButton)

        self._mainLayout.addLayout(self._buttonLayout)

        self._mainLayout.addSpacing(4)

        self.setStyleSheet(CODE_TEXT_EDIT_STYLESHEET)

    def _runCode(self):
        code = self._codeTextEdit.toPlainText()
        self.sigExecCode.emit(code)

    def notifyResult(self, isErr: bool, result: str):
        """ if isErr is True, print the result with the color red, else green. """
        if isErr:
            self._resultTextBrowser.setTextColor(QtGui.QColor(255, 0, 0))
        else:
            self._resultTextBrowser.setTextColor(QtGui.QColor(0, 0, 0))
        self._resultTextBrowser.setText(result)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = CodeWindow()
    window.show()
    sys.exit(app.exec())
