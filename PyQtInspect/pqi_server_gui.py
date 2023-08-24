# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/24 17:36
# Description: 
# ==============================================
import time

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


class Dispatcher(QtCore.QObject):
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
        ReaderThread.__init__(self, self.dispatcher.sock)
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


class BrowserHandler(QtCore.QObject):
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
                dispatcher = BrowserHandler()
                # dispatcher.sigMsg.connect(self.widgetInfoRecv)
                t = QtCore.QThread()
                dispatcher.moveToThread(t)
                t.started.connect(dispatcher.run)
                self.dispatchers.append(dispatcher)
                self.threads.append(t)

                t.start()

        except:
            sys.stderr.write("Could not bind to port: %s\n" % (self.port,))
            sys.stderr.flush()
            traceback.print_exc()


class PQIWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQtInspect")
        self.resize(800, 600)

        self._infoLabel = QtWidgets.QLabel(self)
        self._infoLabel.setText("PyQtInspect")
        self._infoLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(self._infoLabel)

        # self._worker.widgetInfoRecv.connect(self.on_widget_info_recv)
        self._worker = PQYWorker(None, 19394)
        self._workerThread = QtCore.QThread()

        self._worker.moveToThread(self._workerThread)
        self._workerThread.started.connect(self._worker.run)

        self._btn = QtWidgets.QPushButton(self)
        self._btn.setText("Click")
        self._btn.clicked.connect(self.runWorker)
        self._btn.move(100, 100)

    def runWorker(self):
        self._workerThread.start()

    def on_widget_info_recv(self, info):
        print(info)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = PQIWindow()
    window.show()
    sys.exit(app.exec())

