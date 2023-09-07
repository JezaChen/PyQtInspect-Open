# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 20:49
# Description: 
# ==============================================
from PyQt5 import QtWidgets, QtGui, QtCore
from io import StringIO
from contextlib import redirect_stdout

from PyQtInspect.pqi_gui.syntax import PythonHighlighter

CODE_TEXT_EDIT_STYLESHEET = """
QTextEdit#CodeTextEdit {
    font: 14px "Consolas";
}

QTextEdit#ResultTextBrowser {
    font: 14px "Consolas";
}
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exec Code For Selected Widget")
        self.setWindowIcon(QtGui.QIcon("..\\icon.png"))
        self.resize(500, 300)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._codeTextEdit = CodeTextEdit(self)
        self._codeTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

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
        self._cancelButton.setText("Cancel")
        self._cancelButton.clicked.connect(self.close)
        self._buttonLayout.addWidget(self._cancelButton)

        self._mainLayout.addLayout(self._buttonLayout)

        self.setStyleSheet(CODE_TEXT_EDIT_STYLESHEET)

    def _runCode(self):
        code = self._codeTextEdit.toPlainText()
        try:
            f = StringIO()
            with redirect_stdout(f):
                exec(code)
            self._resultTextBrowser.setText(f.getvalue())
        except Exception as e:
            self._resultTextBrowser.setText(str(e))


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = CodeWindow()
    window.show()
    sys.exit(app.exec())
