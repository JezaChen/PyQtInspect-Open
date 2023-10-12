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

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread, WriterThread, NetCommandFactory
from PyQtInspect._pqi_bundle.pqi_comm_constants import CMD_WIDGET_INFO, CMD_INSPECT_FINISHED, CMD_EXEC_CODE_ERROR, \
    CMD_EXEC_CODE_RESULT, CMD_CHILDREN_INFO
from PyQtInspect._pqi_bundle.pqi_override import overrides

import ctypes

from PyQtInspect.pqi_gui.code_window import CodeWindow
from PyQtInspect.pqi_gui.hierarchy_bar import HierarchyBar
from PyQtInspect.pqi_gui.settings import getPyCharmPath, findDefaultPycharmPath
from PyQtInspect.pqi_gui.settings_window import SettingWindow
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET
from PyQtInspect.pqi_gui._pqi_res import resources

myappid = 'jeza.tools.pyqt_inspect.0.0.1alpha'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class DispatcherThread(QtCore.QThread):
    def run(self) -> None:
        super().run()


class Dispatcher(QtCore.QThread):
    sigMsg = QtCore.pyqtSignal(int, dict)  # dispatcher_id, info
    sigDelete = QtCore.pyqtSignal(int)

    def __init__(self, parent, sock, id):
        super().__init__(parent)
        self.sock = sock
        self.id = id
        self.net_command_factory = NetCommandFactory()
        self.reader = None
        self.writer = None

    def run(self):
        self.writer = WriterThread(self.sock)
        self.writer.pydev_do_not_trace = False  # We run writer in the same thread so we don't want to loose tracing.
        self.writer.start()

        self.reader = DispatchReader(self)
        self.reader.pydev_do_not_trace = False  # We run reader in the same thread so we don't want to loose tracing.
        self.reader.run()

    def close(self):
        try:
            self.reader.do_kill_pydev_thread()
        except:
            pass

    def notify(self, cmd_id, seq, text):
        self.sigMsg.emit(self.id, {"cmd_id": cmd_id, "seq": seq, "text": text})

    def sendEnableInspect(self):
        self.writer.add_command(self.net_command_factory.make_enable_inspect_message())

    def sendDisableInspect(self):
        self.writer.add_command(self.net_command_factory.make_disable_inspect_message())

    def sendExecCodeEvent(self, code: str):
        self.writer.add_command(self.net_command_factory.make_exec_code_message(code))

    def sendHighlightWidgetEvent(self, widgetId: int, isHighlight: bool):
        self.writer.add_command(self.net_command_factory.make_set_widget_highlight_message(widgetId, isHighlight))

    def sendSelectWidgetEvent(self, widgetId: int):
        self.writer.add_command(self.net_command_factory.make_select_widget_message(widgetId))

    def sendRequestWidgetInfoEvent(self, widgetId: int, extra: dict = None):
        self.writer.add_command(self.net_command_factory.make_req_widget_info_message(widgetId, extra))

    def sendRequestChildrenInfoEvent(self, widgetId: int):
        self.writer.add_command(self.net_command_factory.make_req_children_info_message(widgetId))

    def notifyDelete(self):
        self.reader.do_kill_pydev_thread()
        self.writer.do_kill_pydev_thread()

        self.sigDelete.emit(self.id)


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
        self.dispatcher.notifyDelete()

    def process_command(self, cmd_id, seq, text):
        # unquote text
        from urllib.parse import unquote
        text = unquote(text)
        self.dispatcher.notify(cmd_id, seq, text)


class PQYWorker(QtCore.QObject):
    start = QtCore.pyqtSignal()
    widgetInfoRecv = QtCore.pyqtSignal(dict)
    sigNewDispatcher = QtCore.pyqtSignal(Dispatcher)
    socketError = QtCore.pyqtSignal(str)

    def __init__(self, parent, port):
        super().__init__(parent)
        self.port = port

        self.dispatchers = []
        self.idToDispatcher = {}

        self.start.connect(self.run)

    def run(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(None)

        # try:
        #     from socket import SO_REUSEPORT
        #     s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        # except ImportError:
        #     s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            s.bind(('', self.port))
            s.listen(1)

            dispatcherId = 0

            while True:
                newSock, _addr = s.accept()
                # 新建个线程来处理
                dispatcher = Dispatcher(None, newSock, dispatcherId)
                dispatcher.sigDelete.connect(self._onDispatcherDelete)
                self.dispatchers.append(dispatcher)
                self.idToDispatcher[dispatcherId] = dispatcher

                self.sigNewDispatcher.emit(dispatcher)
                dispatcher.start()
                dispatcherId += 1

        except Exception as e:
            sys.stderr.write("Could not bind to port: %s\n" % (self.port,))
            sys.stderr.flush()
            traceback.print_exc()
            self.socketError.emit(str(e))

    def onMsg(self, info: dict):
        self.widgetInfoRecv.emit(info)

    def sendEnableInspect(self):
        for dispatcher in self.dispatchers:
            dispatcher.sendEnableInspect()

    def sendDisableInspect(self):
        for dispatcher in self.dispatchers:
            dispatcher.sendDisableInspect()

    def sendExecCodeEvent(self, dispatcherId: int, code: str):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendExecCodeEvent(code)

    def sendHighlightWidgetEvent(self, dispatcherId: int, widgetId: int, isHighlight: bool):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendHighlightWidgetEvent(widgetId, isHighlight)

    def sendSelectWidgetEvent(self, dispatcherId: int, widgetId: int):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendSelectWidgetEvent(widgetId)

    def sendRequestWidgetInfoEvent(self, dispatcherId: int, widgetId: int, extra: dict = None):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendRequestWidgetInfoEvent(widgetId, extra)

    def sendRequestChildrenInfoEvent(self, dispatcherId: int, widgetId: int):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendRequestChildrenInfoEvent(widgetId)

    def _onDispatcherDelete(self, id: int):
        dispatcher = self.idToDispatcher.pop(id)
        self.dispatchers.remove(dispatcher)
        dispatcher.close()
        dispatcher.deleteLater()


class BriefLine(QtWidgets.QWidget):
    def __init__(self, parent, key: str, defaultValue: str = ""):
        super().__init__(parent)
        self.setFixedHeight(30)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(5)

        self._keyLabel = QtWidgets.QLabel(self)
        self._keyLabel.setText(key)
        self._keyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._keyLabel.setWordWrap(True)
        self._keyLabel.setMinimumWidth(80)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QLineEdit(self)
        self._valueLineEdit.setObjectName("codeStyleLineEdit")
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._valueLineEdit.setReadOnly(True)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)


class BriefLineWithEditButton(BriefLine):
    sigEditButtonClicked = QtCore.pyqtSignal(str)  # new value

    def __init__(self, parent, key: str = None, defaultValue: str = None, buttonText: str = "Edit"):
        super().__init__(parent, key, defaultValue)

        self._valueLineEdit.setReadOnly(False)

        self._editButton = QtWidgets.QPushButton(self)
        self._editButton.setText(buttonText)
        self._editButton.setFixedHeight(30)
        self._editButton.clicked.connect(lambda: self.sigEditButtonClicked.emit(self._valueLineEdit.text()))

        self._layout.addWidget(self._editButton)


class WidgetBriefWidget(QtWidgets.QWidget):
    sigOpenCodeWindow = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)

        self._classNameLine = BriefLine(self, "class name")
        self._mainLayout.addWidget(self._classNameLine)

        self._objectNameLine = BriefLine(self, "object name")
        self._mainLayout.addWidget(self._objectNameLine)

        self._sizeLine = BriefLine(self, "size")
        self._mainLayout.addWidget(self._sizeLine)

        self._posLine = BriefLine(self, "pos")
        self._mainLayout.addWidget(self._posLine)

        self._styleSheetLine = BriefLine(self, "stylesheet")
        self._mainLayout.addWidget(self._styleSheetLine)

        self._executionButtonsLayout = QtWidgets.QHBoxLayout()
        self._executionButtonsLayout.setContentsMargins(4, 0, 4, 0)
        self._executionButtonsLayout.setSpacing(5)

        self._execCodeButton = QtWidgets.QPushButton(self)
        self._execCodeButton.setText("Run Code")
        self._execCodeButton.setFixedHeight(30)
        self._execCodeButton.clicked.connect(self.sigOpenCodeWindow)

        self._executionButtonsLayout.addWidget(self._execCodeButton)

        self._mainLayout.addLayout(self._executionButtonsLayout)

        self._mainLayout.addStretch(1)

    def setInfo(self, info):
        self._classNameLine.setValue(info["class_name"])
        objName = info["object_name"]
        self._objectNameLine.setValue(objName)
        width, height = info["size"]
        self._sizeLine.setValue(f"{width}, {height}")
        posX, posY = info["pos"]
        self._posLine.setValue(f"{posX}, {posY}")
        self._styleSheetLine.setValue(info["stylesheet"])


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
        pycharmPath = getPyCharmPath()
        if not pycharmPath:
            pycharmPath = findDefaultPycharmPath()
        return pycharmPath

    def openFile(self, fileName: str, lineNo: int):
        # open in Pycharm
        import subprocess
        pycharm = self.findPycharm()
        if pycharm:
            try:
                subprocess.Popen(f"{pycharm} --line {lineNo} {fileName}")
            except Exception as e:
                # message box
                QtWidgets.QMessageBox.critical(self, "Error", f"Error occurred when opening file: {e}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Pycharm not found")
        # subprocess.Popen(f"pycharm64.exe --line {lineNo} {fileName}")


class PQIWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQtInspect")
        self.setWindowIcon(QtGui.QIcon("..\\icon.png"))
        self.resize(700, 1000)

        self._menuBar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menuBar)

        self._moreMenu = QtWidgets.QMenu(self._menuBar)
        self._moreMenu.setTitle("More")
        self._menuBar.addMenu(self._moreMenu)

        self._settingAction = QtWidgets.QAction(self)
        self._settingAction.setText("Settings")
        self._moreMenu.addAction(self._settingAction)
        self._settingAction.triggered.connect(self._openSettingWindow)

        self._settingWindow = None
        self._codeWindow = None

        self._mainContainer = QtWidgets.QWidget(self)
        self.setCentralWidget(self._mainContainer)
        self._mainLayout = QtWidgets.QVBoxLayout(self._mainContainer)
        self._mainLayout.setContentsMargins(4, 4, 4, 4)
        self._mainLayout.setSpacing(0)

        # ====================
        # Top Container
        # ====================
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

        self._inspectButton = QtWidgets.QPushButton(self)
        self._inspectButton.setText("Inspect")
        self._inspectButton.setFixedHeight(30)
        self._inspectButton.setCheckable(True)
        self._inspectButton.clicked.connect(self._onInspectButtonClicked)
        self._inspectButton.setEnabled(False)

        self._topLayout.addWidget(self._inspectButton)

        self._mainLayout.addWidget(self._topContainer)

        self._widgetInfoGroupBox = QtWidgets.QGroupBox(self)
        self._widgetInfoGroupBox.setTitle("Widget Brief Info")

        self._widgetInfoGroupBoxLayout = QtWidgets.QVBoxLayout(self._widgetInfoGroupBox)
        self._widgetInfoGroupBoxLayout.setContentsMargins(0, 4, 0, 6)
        self._widgetInfoGroupBoxLayout.setSpacing(0)

        self._widgetBriefWidget = WidgetBriefWidget(self)
        self._widgetBriefWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._widgetBriefWidget.sigOpenCodeWindow.connect(self._openCodeWindow)

        self._widgetInfoGroupBoxLayout.addWidget(self._widgetBriefWidget)

        self._mainLayout.addSpacing(3)
        self._mainLayout.addWidget(self._widgetInfoGroupBox)

        # ====================
        # Create Stack
        # ====================
        self._createStackGroupBox = QtWidgets.QGroupBox(self)
        self._createStackGroupBox.setTitle("Create Stacks")

        self._createStackGroupBoxLayout = QtWidgets.QVBoxLayout(self._createStackGroupBox)
        self._createStackGroupBoxLayout.setContentsMargins(4, 4, 4, 6)
        self._createStackGroupBoxLayout.setSpacing(0)

        self._createStacksListWidget = CreateStacksListWidget(self)
        self._createStacksListWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._createStackGroupBoxLayout.addWidget(self._createStacksListWidget)

        self._mainLayout.addSpacing(3)
        self._mainLayout.addWidget(self._createStackGroupBox)

        self._hierarchyBar = HierarchyBar(self)
        self._hierarchyBar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._hierarchyBar.sigAncestorItemHovered.connect(self._onAncestorWidgetItemHighlight)
        self._hierarchyBar.sigAncestorItemChanged.connect(self._onAncestorWidgetItemClicked)
        self._hierarchyBar.sigChildMenuItemHovered.connect(self._onChildWidgetItemHighlight)
        self._hierarchyBar.sigChildMenuItemClicked.connect(self._onChildWidgetItemClicked)
        self._hierarchyBar.sigReqChildWidgetsInfo.connect(self._reqChildWidgetsInfo)
        self._hierarchyBar.sigMouseLeaveBarAndMenu.connect(self._unhighlightPrevWidget)

        self._mainLayout.addSpacing(3)
        self._mainLayout.addWidget(self._hierarchyBar)

        self._worker = None
        self._currDispatcherIdForSelectedWidget = None

        self._curWidgetId = -1
        self._curHighlightedWidgetId = -1

        self.setStyleSheet(GLOBAL_STYLESHEET)

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
        self._inspectButton.setEnabled(True)

        self._worker = PQYWorker(None, port)
        self._worker.widgetInfoRecv.connect(self.on_widget_info_recv)
        self._worker.sigNewDispatcher.connect(self.onNewDispatcher)
        self._worker.socketError.connect(self._onWorkerSocketError)
        self._workerThread = QtCore.QThread()

        self._worker.moveToThread(self._workerThread)
        self._workerThread.started.connect(self._worker.run)

        self._workerThread.start()

    def _onWorkerSocketError(self, msg):
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._portLineEdit.setEnabled(True)
        self._serveButton.setEnabled(True)
        self._inspectButton.setEnabled(False)
        self._workerThread.quit()
        self._worker.deleteLater()
        self._worker = None

    def on_widget_info_recv(self, dispatcherId: int, info: dict):
        cmdId = info.get("cmd_id")
        if cmdId == CMD_WIDGET_INFO:
            self.handleWidgetInfoMsg(json.loads(info["text"]))
        elif cmdId == CMD_INSPECT_FINISHED:
            self._currDispatcherIdForSelectedWidget = dispatcherId
            self.handle_inspect_finished_msg()
            self.windowHandle().requestActivate()
        elif cmdId == CMD_EXEC_CODE_ERROR:
            errMsg = info.get("text", "")
            self._notifyResultToCodeWindow(True, errMsg)
        elif cmdId == CMD_EXEC_CODE_RESULT:
            result = info.get("text", "")
            self._notifyResultToCodeWindow(False, result)
        elif cmdId == CMD_CHILDREN_INFO:
            childrenInfoDict = json.loads(info["text"])
            widgetId = childrenInfoDict["widget_id"]
            self._hierarchyBar.setMenuData(widgetId, childrenInfoDict["child_classes"],
                                           childrenInfoDict["child_object_names"],
                                           childrenInfoDict["child_ids"])
        # self._bottomStatusTextBrowser.append(f"recv: {info}")

    def handleWidgetInfoMsg(self, info):
        self._curWidgetId = info["id"]
        self._widgetBriefWidget.setInfo(info)
        self._createStacksListWidget.setStacks(info.get("stacks_when_create", []))

        # set hierarchy
        if info.get("extra", {}).get("from",
                                     "") != "ancestor":  # 如果为"ancestor", 则意味着用户是通过bar来点击回溯获取祖先控件的信息, 此时无需覆盖祖先控件信息
            classes = [*reversed(info["parent_classes"]), info["class_name"]]
            objNames = [*reversed(info["parent_object_names"]), info["object_name"]]
            ids = [*reversed(info["parent_ids"]), info["id"]]
            self._hierarchyBar.setData(classes, objNames, ids)

    def handle_inspect_finished_msg(self):
        self._inspectButton.setChecked(False)
        self._worker.sendDisableInspect()  # disable inspect for all dispatchers

    def onNewDispatcher(self, dispatcher):
        dispatcher.sigMsg.connect(self.on_widget_info_recv)

    def _onInspectButtonClicked(self, checked: bool):
        if self._worker is None:
            return
        if checked:
            self._worker.sendEnableInspect()
        else:
            self._worker.sendDisableInspect()
            self._currDispatcherIdForSelectedWidget = None

    def _notifyExecCodeInSelectedWidget(self, code: str):
        if self._worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        self._worker.sendExecCodeEvent(self._currDispatcherIdForSelectedWidget, code)

    def _onAncestorWidgetItemHighlight(self, widgetId: str):
        widgetId = int(widgetId)
        if self._worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        # unhighlight prev widget, and highlight current widget
        self._unhighlightPrevWidget()
        self._worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId, True)
        self._curHighlightedWidgetId = widgetId

    def _onAncestorWidgetItemClicked(self, widgetId: str):
        widgetId = int(widgetId)
        if self._worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        self._worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        self._worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId, {
            "from": "ancestor"
        })  # 通过bar来点击回溯获取祖先控件的信息, 带上from字段, 避免覆盖祖先控件信息(即点击导航条前面的类后, 该类后面的类全都无了, 因为此时显示的是该类的祖先控件信息)
        self._worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)  # todo 会不会有时序问题

    def _onChildWidgetItemHighlight(self, widgetId: str):
        widgetId = int(widgetId)
        if self._worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        # unhighlight prev widget, and highlight current widget
        self._unhighlightPrevWidget()
        self._worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId, True)
        self._curHighlightedWidgetId = widgetId

    def _onChildWidgetItemClicked(self, widgetId: str):
        widgetId = int(widgetId)
        if self._worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        self._worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        self._worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)

    def _openSettingWindow(self):
        if self._settingWindow is None:
            self._settingWindow = SettingWindow(self)
        self._settingWindow.show()

    def _openCodeWindow(self):
        if self._codeWindow is None:
            self._codeWindow = CodeWindow(self)
            self._codeWindow.sigExecCode.connect(self._notifyExecCodeInSelectedWidget)
        self._codeWindow.show()

    def _notifyResultToCodeWindow(self, isErr: bool, result: str):
        if self._codeWindow is None:
            return
        self._codeWindow.notifyResult(isErr, result)

    def _reqChildWidgetsInfo(self, widgetIdStr: str):
        if self._worker is not None and self._currDispatcherIdForSelectedWidget is not None:
            widgetId = int(widgetIdStr)
            self._worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)

    def _unhighlightPrevWidget(self):
        conditions_met = (
            self._worker is not None,
            self._currDispatcherIdForSelectedWidget is not None,
            self._curHighlightedWidgetId != -1
        )

        if all(conditions_met):
            self._worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget,
                                                  self._curHighlightedWidgetId,
                                                  False)
            self._curHighlightedWidgetId = -1


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = PQIWindow()
    window.show()
    sys.exit(app.exec())
