import sys
import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor

import time

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import threading
import traceback
from socket import socket, AF_INET, SOCK_STREAM
from ssl import SOL_SOCKET

from _socket import SO_REUSEADDR

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread
from PyQtInspect._pqi_bundle.pqi_override import overrides


class Dispatcher(QtCore.QObject):
    sigMsg = QtCore.pyqtSignal(dict)

    def __init__(self, parent, sock):
        super().__init__(parent)
        self.sock = sock

    def run(self):
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
        # s = socket(AF_INET, SOCK_STREAM)
        # s.settimeout(None)
        #
        # try:
        #     from socket import SO_REUSEPORT
        #     s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        # except ImportError:
        #     s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        #
        # s.bind(('', self.port))
        # s.listen(1)

        try:
            while True:
                print("Aaa")
                time.sleep(1)
                # newSock, _addr = s.accept()
                # # 新建个线程来处理
                # dispatcher = Dispatcher(self, newSock)
                # dispatcher.sigMsg.connect(self.widgetInfoRecv)
                # t = QtCore.QThread(self)
                # dispatcher.moveToThread(t)
                # t.started.connect(dispatcher.run)
                # t.start()
                # self.dispatchers.append(dispatcher)
                # self.threads.append(t)

        except:
            sys.stderr.write("Could not bind to port: %s\n" % (self.port,))
            sys.stderr.flush()
            traceback.print_exc()


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(453, 408)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Example"))
        self.pushButton.setText(_translate("Form", "Input"))


# Object, which will be moved to another thread
class BrowserHandler(QtCore.QObject):
    running = False
    newTextAndColor = QtCore.pyqtSignal(str, object)

    # method which will execute algorithm in another thread
    def run(self):
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


class MyWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # use button to invoke slot with another text and color
        self.ui.pushButton.clicked.connect(self.addAnotherTextAndColor)

        # create thread
        self.thread = QtCore.QThread()
        # create object which will be moved to another thread
        self.browserHandler = PQYWorker(None, 19394)
        # move object to another thread
        self.browserHandler.moveToThread(self.thread)
        # after that, we can connect signals from this object to slot in GUI thread
        # self.browserHandler.newTextAndColor.connect(self.addNewTextAndColor)
        # connect started signal to run method of object in another thread
        self.thread.started.connect(self.browserHandler.run)
        # start thread
        self.thread.start()

    @QtCore.pyqtSlot(str, object)
    def addNewTextAndColor(self, string, color):
        self.ui.textBrowser.setTextColor(color)
        self.ui.textBrowser.append(string)

    def addAnotherTextAndColor(self):
        self.ui.textBrowser.setTextColor(QColor(0, 255, 0))
        self.ui.textBrowser.append(
            '{} - thread 2 variant 3.\n'.format(str(time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime()))))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
