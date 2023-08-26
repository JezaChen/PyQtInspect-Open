# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/24 17:36
# Description: 
# ==============================================
import json
import time
import queue

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import threading
import traceback
from socket import socket, AF_INET, SOCK_STREAM
from ssl import SOL_SOCKET

from PyQt5.QtGui import QColor
from _socket import SO_REUSEADDR

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread
from PyQtInspect._pqi_bundle.pqi_override import overrides


class DispatcherThread(QtCore.QThread):
    def run(self) -> None:
        super().run()


class Dispatcher(QtCore.QThread):
    sigMsg = QtCore.pyqtSignal(dict)

    def __init__(self, parent, sock):
        super().__init__(parent)
        self.sock = sock

    def run(self):
        print("run")
        self.reader = DispatchReader(self)
        self.reader.pydev_do_not_trace = False  # We run reader in the same thread so we don't want to loose tracing.
        self.reader.run()

    def close(self):
        try:
            self.reader.do_kill_pydev_thread()
        except:
            pass

    def notify(self, cmd_id, seq, text):
        self.sigMsg.emit({"cmd_id": cmd_id, "seq": seq, "text": text})


class DispatchReader(ReaderThread):
    def __init__(self, dispatcher):
        ReaderThread.__init__(self, dispatcher.sock)
        self.dispatcher = dispatcher

    @overrides(ReaderThread._on_run)
    def _on_run(self):
        dummy_thread = threading.current_thread()
        dummy_thread.is_pydev_daemon_thread = False
        return ReaderThread._on_run(self)

    def handle_except(self):
        ReaderThread.handle_except(self)

    def process_command(self, cmd_id, seq, text):
        # unquote text
        from urllib.parse import unquote
        text = unquote(text)
        print(cmd_id, seq, text)
        self.dispatcher.notify(cmd_id, seq, text)


class BrowserHandler(QtCore.QThread):
    running = False
    newTextAndColor = QtCore.pyqtSignal(str, object)

    # method which will execute algorithm in another thread
    def run(self):
        print("acaa")
        while True:
            # send signal with new text and color from aonther thread
            self.newTextAndColor.emit(
                '{} - thread 2 variant 1.\n'.format(str(time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime()))),
                QColor(0, 0, 255)
            )
            QtCore.QThread.msleep(1000)

            # send signal with new text and color from aonther thread
            self.newTextAndColor.emit(
                '{} - thread 2 variant 2.\n'.format(str(time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime()))),
                QColor(255, 0, 0)
            )
            QtCore.QThread.msleep(1000)


class PQYWorker(QtCore.QObject):
    start = QtCore.pyqtSignal()

    widgetInfoRecv = QtCore.pyqtSignal(dict)

    sigNewDispatcher = QtCore.pyqtSignal(Dispatcher)

    def __init__(self, parent, port):
        super().__init__(parent)
        self.port = port
        self.dispatchers = []
        self.threads = []
        self.start.connect(self.run)

    def run(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(None)

        try:
            from socket import SO_REUSEPORT
            s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        except ImportError:
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        s.bind(('', self.port))
        s.listen(1)

        try:
            while True:
                newSock, _addr = s.accept()
                # 新建个线程来处理
                dispatcher = Dispatcher(None, newSock)
                # dispatcher.sigMsg.connect(self.onMsg)
                # t = QtCore.QThread()
                # dispatcher.moveToThread(t)
                # t.started.connect(dispatcher.run)
                self.dispatchers.append(dispatcher)
                # self.threads.append(t)
                self.sigNewDispatcher.emit(dispatcher)
                dispatcher.start()

        except:
            sys.stderr.write("Could not bind to port: %s\n" % (self.port,))
            sys.stderr.flush()
            traceback.print_exc()

    def onMsg(self, info: dict):
        self.widgetInfoRecv.emit(info)


class BriefLine(QtWidgets.QWidget):
    def __init__(self, parent, key: str, defaultValue: str = ""):
        super().__init__(parent)
        self.setFixedHeight(30)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(3)

        self._keyLabel = QtWidgets.QLabel(self)
        self._keyLabel.setText(key)
        self._keyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._keyLabel.setWordWrap(True)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QLineEdit(self)
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)


class WidgetBriefWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)

        self._classNameLine = BriefLine(self, "class_name")
        self._mainLayout.addWidget(self._classNameLine)

        self._objectNameLine = BriefLine(self, "object_name")
        self._mainLayout.addWidget(self._objectNameLine)

        self._sizeLine = BriefLine(self, "size")
        self._mainLayout.addWidget(self._sizeLine)

        self._posLine = BriefLine(self, "pos")
        self._mainLayout.addWidget(self._posLine)

        self._parentLine = BriefLine(self, "parent")
        self._mainLayout.addWidget(self._parentLine)

        self._styleSheetLine = BriefLine(self, "style_sheet")
        self._mainLayout.addWidget(self._styleSheetLine)

        self._mainLayout.addStretch(1)

    def setInfo(self, info):
        self._classNameLine.setValue(info["class_name"])
        self._objectNameLine.setValue(info["object_name"])
        self._sizeLine.setValue(str(info["size"]))
        self._posLine.setValue(str(info["pos"]))
        self._parentLine.setValue(str(info["parent_classes"]))


class CreateStacksListWidget(QtWidgets.QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def setStacks(self, stacks: list):
        self.clear()
        for index, stack in enumerate(stacks):
            fileName = stack.get("filename", "")
            lineNo = stack.get("lineno", "")
            funcName = stack.get("function", "")
            item = QtWidgets.QListWidgetItem()
            item.setText(f"{index + 1}. File {fileName}, line {lineNo}: {funcName}")
            # set property
            item.setData(QtCore.Qt.UserRole, (fileName, lineNo))
            self.addItem(item)

    # double click to open file
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None:
                fileName, lineNo = item.data(QtCore.Qt.UserRole)
                if fileName:
                    self.openFile(fileName, lineNo)

    def findPycharm(self):
        import os
        for path in os.environ["PATH"].split(";"):
            if "pycharm" in path.lower():
                return path + "\\pycharm64.exe"
        return None

    def openFile(self, fileName: str, lineNo: int):
        # open in Pycharm
        import subprocess
        pycharm = self.findPycharm()
        subprocess.Popen(f"pycharm64.exe --line {lineNo} {fileName}")



class PQIWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQtInspect")
        self.resize(700, 1000)

        self._mainContainer = QtWidgets.QWidget(self)
        self.setCentralWidget(self._mainContainer)
        self._mainLayout = QtWidgets.QVBoxLayout(self._mainContainer)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(0)

        self._topContainer = QtWidgets.QWidget(self)
        self._topContainer.setFixedHeight(30)
        self._topContainer.move(0, 0)

        self._topLayout = QtWidgets.QHBoxLayout(self._topContainer)
        self._topLayout.setContentsMargins(0, 0, 0, 0)
        self._topLayout.setSpacing(0)

        self._portLineEdit = QtWidgets.QLineEdit(self._topContainer)
        self._portLineEdit.setFixedHeight(30)
        self._portLineEdit.setText("19394")
        self._portLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._topLayout.addWidget(self._portLineEdit)

        self._serveButton = QtWidgets.QPushButton(self)
        self._serveButton.setText("Serve")
        self._serveButton.setFixedHeight(30)
        self._serveButton.clicked.connect(self.runWorker)

        self._topLayout.addWidget(self._serveButton)

        self._mainLayout.addWidget(self._topContainer)

        self._widgetBriefWidget = WidgetBriefWidget(self)
        self._widgetBriefWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._mainLayout.addWidget(self._widgetBriefWidget)

        self._createStacksListWidget = CreateStacksListWidget(self)
        self._createStacksListWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._mainLayout.addWidget(self._createStacksListWidget)

        self._bottomStatusTextBrowser = QtWidgets.QTextBrowser(self)
        self._bottomStatusTextBrowser.setFixedHeight(100)
        self._bottomStatusTextBrowser.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._mainLayout.addWidget(self._bottomStatusTextBrowser)

        self._worker = None

    def runWorker(self):
        if self._worker is not None:
            return

        try:
            port = int(self._portLineEdit.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "PyQtInspect", "Port must be a number")
            return

        self._portLineEdit.setEnabled(False)
        self._serveButton.setEnabled(False)

        self._worker = PQYWorker(None, port)
        self._worker.widgetInfoRecv.connect(self.on_widget_info_recv)
        self._worker.sigNewDispatcher.connect(self.onNewDispatcher)
        self._workerThread = QtCore.QThread()

        self._worker.moveToThread(self._workerThread)
        self._workerThread.started.connect(self._worker.run)

        self._workerThread.start()

    def on_widget_info_recv(self, info: dict):
        if info.get("cmd_id") == 1001:
            self.handle_widget_info_msg(json.loads(info["text"]))
        self._bottomStatusTextBrowser.append(f"recv: {info}")

    def handle_widget_info_msg(self, info):
        self._widgetBriefWidget.setInfo(info)
        self._createStacksListWidget.setStacks(info.get("stacks_when_create", []))

    def onNewDispatcher(self, dispatcher):
        dispatcher.sigMsg.connect(self.on_widget_info_recv)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = PQIWindow()
    window.show()
    sys.exit(app.exec())
