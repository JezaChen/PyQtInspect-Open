# -*- encoding:utf-8 -*-

import contextlib
import io
import typing

from PyQt5 import QtWidgets, QtGui, QtCore

from PyQtInspect.pqi_gui._pqi_res import get_icon
from PyQtInspect.pqi_gui.components.simple_kv_line_edit import SimpleSettingLineEdit
import PyQtInspect.pqi_gui.data_center as DataCenter

import wingrab

PYTHON_NAMES = ['python', ]


def _getAllPySubprocess(parent_pid):
    import psutil

    parent_process = psutil.Process(parent_pid)
    children = parent_process.children(recursive=True)
    for child in children:
        for pyName in PYTHON_NAMES:
            if pyName in child.name():
                yield child


class PidLineEdit(SimpleSettingLineEdit):
    sigAttachButtonClicked = QtCore.pyqtSignal()
    sigAttachAllPySubprocessButtonClicked = QtCore.pyqtSignal()  # parent_pid

    def __init__(self, parent):
        super().__init__(parent, "Pid: ")

        self._attachButton = QtWidgets.QPushButton(self)
        self._attachButton.setText("Attach")
        self._attachButton.setFixedHeight(30)
        self._attachButton.clicked.connect(self.sigAttachButtonClicked)

        self._layout.addWidget(self._attachButton)

        self._attachAllPySubButton = QtWidgets.QPushButton(self)
        self._attachAllPySubButton.setText("Attach All Python Subprocesses")
        self._attachAllPySubButton.setFixedHeight(30)
        self._attachAllPySubButton.clicked.connect(self.sigAttachAllPySubprocessButtonClicked)

        self._layout.addWidget(self._attachAllPySubButton)

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
            self._worker.sigStdOut.emit(f"({self._worker.pidToAttach}) {text}")

    def __init__(self, parent, pidToAttach: int):
        super().__init__(parent)
        self._pidToAttach = pidToAttach

    @property
    def pidToAttach(self):
        return self._pidToAttach

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
                # print('==================')

                self.sigAttachFinished.emit()
            except Exception as e:
                print(f'Attach Error: {e}\n')
                self.sigAttachError.emit(str(e))


class AttachMultipleWorker(QtCore.QObject):
    sigStdOut = QtCore.pyqtSignal(str)
    sigAttachFinished = QtCore.pyqtSignal(int)  # errCount

    class _StdOutGetter(io.StringIO):
        def __init__(self, worker):
            super().__init__()
            self._worker = worker

        def write(self, text):
            super().write(text)
            self._worker.sigStdOut.emit(text)

    def __init__(self, parent, pidsToAttach: typing.List[int]):
        super().__init__(parent)
        self._pidsToAttach = pidsToAttach

        self._subWorkers = []
        self._subThreads = set()
        self._errCount = 0

    def _onSubThreadQuit(self, thread):
        thread.quit()
        self._subThreads.remove(thread)
        if not self._subThreads:
            self.sigAttachFinished.emit(self._errCount)

    def _onSubWorkerAttachError(self, pid, errMsg):
        with contextlib.redirect_stdout(AttachMultipleWorker._StdOutGetter(self)):
            print(f'Attach {pid} Error: {errMsg}\n')
            self._errCount += 1

    def doWork(self):
        for pid in self._pidsToAttach:
            worker = AttachWorker(None, pid)
            self._subWorkers.append(worker)
            thread = QtCore.QThread(None)
            worker.moveToThread(thread)

            thread.started.connect(worker.doWork)
            thread.finished.connect(lambda _thread=thread: self._onSubThreadQuit(_thread))

            worker.sigAttachFinished.connect(thread.quit)
            worker.sigAttachError.connect(lambda msg, _pid=pid: self._onSubWorkerAttachError(_pid, msg))
            worker.sigStdOut.connect(self.sigStdOut)

            self._subThreads.add(thread)
            thread.start()


class AttachWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Attach to Process")
        self.setWindowIcon(get_icon())
        self.resize(500, 300)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(10, 10, 10, 10)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        self._pidLine = PidLineEdit(self)
        self._pidLine.sigAttachButtonClicked.connect(self._onAttachButtonClicked)
        self._pidLine.sigAttachAllPySubprocessButtonClicked.connect(self._onAttachAllPySubprocessButtonClicked)
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

    def _onAttachAllPySubprocessButtonClicked(self):
        try:
            self._tryAttachToAllPySubprocess(int(self._pidLine.getValue()))
        except ValueError:
            # todo 如果pid不存在呢??
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid Pid!")
            return

    def _doWorkerImpl(self, worker):
        worker.sigAttachFinished.connect(self._thread.quit)
        worker.sigAttachError.connect(self._onAttachError)
        worker.sigStdOut.connect(self._consoleOutputTextBrowser.write)
        self._thread.started.connect(worker.doWork)
        self._thread.finished.connect(lambda: self._pidLine.setEnabled(True))

    def _tryAttachToProcess(self, pid: int):
        """ Attach放在这个控件实现吧 """
        if self._thread is not None and self._thread.isRunning():  # guard
            QtWidgets.QMessageBox.information(self, "Info", "Already Attaching")
            return

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

    def _tryAttachToAllPySubprocess(self, parent_pid: int):
        if self._thread is not None and self._thread.isRunning():  # guard
            QtWidgets.QMessageBox.information(self, "Info", "Already Attaching")
            return

        childPids = [childProcess.pid for childProcess in _getAllPySubprocess(parent_pid)]
        if not childPids:
            QtWidgets.QMessageBox.information(self, "Info", "No Python Subprocess Found")
            return

        self._pidLine.setEnabled(False)

        self._thread = QtCore.QThread(None)
        self._worker = AttachMultipleWorker(None, childPids)
        self._worker.moveToThread(self._thread)
        self._worker.sigStdOut.connect(self._consoleOutputTextBrowser.write)
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
