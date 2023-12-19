# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/24 17:36
# Description: 
# ==============================================
import pathlib
import sys

pyqt_inspect_module_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if pyqt_inspect_module_dir not in sys.path:
    sys.path.insert(0, pyqt_inspect_module_dir)

import json

from PyQt5 import QtWidgets, QtCore, QtGui
import threading
import traceback
from socket import socket, AF_INET, SOCK_STREAM
from ssl import SOL_SOCKET

from PyQtInspect.pqi_gui.attach_window import AttachWindow
from PyQtInspect.pqi_gui.create_stacks_list_widget import CreateStacksListWidget
from _socket import SO_REUSEADDR

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread, WriterThread, NetCommandFactory
from PyQtInspect._pqi_bundle.pqi_comm_constants import CMD_WIDGET_INFO, CMD_INSPECT_FINISHED, CMD_EXEC_CODE_ERROR, \
    CMD_EXEC_CODE_RESULT, CMD_CHILDREN_INFO, CMD_QT_PATCH_SUCCESS
from PyQtInspect._pqi_bundle.pqi_override import overrides

import ctypes

from PyQtInspect.pqi_gui.code_window import CodeWindow
from PyQtInspect.pqi_gui.hierarchy_bar import HierarchyBar
from PyQtInspect.pqi_gui.settings import getPyCharmPath, findDefaultPycharmPath
from PyQtInspect.pqi_gui.settings_window import SettingWindow
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET
import PyQtInspect.pqi_gui.data_center as DataCenter
from PyQtInspect.pqi_gui._pqi_res import resources, get_icon

myappid = 'jeza.tools.pyqt_inspect.0.0.1alpha2'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


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

        # 由于dispatcher刚创建的时候, 主界面还来不及处理立即到来的信息(PQYWorker未发出新dispatcher创建的信号)
        # 所以需要在主界面准备好之后再处理
        # 此前的消息都缓存起来
        self._mainUIReady = False
        self._msg_buffer = []

    def run(self):
        self.writer = WriterThread(self.sock)
        self.writer.pydev_do_not_trace = False  # We run writer in the same thread so we don't want to loose tracing.
        self.writer.start()

        self.reader = DispatchReader(self)
        self.reader.pydev_do_not_trace = False  # We run reader in the same thread so we don't want to loose tracing.
        self.reader.run()

    def close(self):
        try:
            self.writer.do_kill_pydev_thread()
            self.reader.do_kill_pydev_thread()
            self.sock.close()
        except:
            pass

    def registerMainUIReady(self):
        """ 告知dispatcher, 主界面已经准备好了, 可以处理消息了
        """
        self._mainUIReady = True
        for cmd_id, seq, text in self._msg_buffer:
            self.notify(cmd_id, seq, text)

    def notify(self, cmd_id, seq, text):
        if not self._mainUIReady:
            # 缓存起来
            self._msg_buffer.append((cmd_id, seq, text))
        self.sigMsg.emit(self.id, {"cmd_id": cmd_id, "seq": seq, "text": text})

    def sendEnableInspect(self, extra: dict):
        self.writer.add_command(self.net_command_factory.make_enable_inspect_message(extra))

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

        self._isServing = False
        self._socket = None

    def run(self):
        self._isServing = True
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.settimeout(None)

        # try:
        #     from socket import SO_REUSEPORT
        #     s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        # except ImportError:
        #     s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            self._socket.bind(('', self.port))
            self._socket.listen(1)

            dispatcherId = 0

            while self._isServing:
                newSock, _addr = self._socket.accept()
                # 新建个线程来处理
                dispatcher = Dispatcher(None, newSock, dispatcherId)
                dispatcher.sigDelete.connect(self._onDispatcherDelete)
                self.dispatchers.append(dispatcher)
                self.idToDispatcher[dispatcherId] = dispatcher

                self.sigNewDispatcher.emit(dispatcher)
                dispatcher.start()
                dispatcherId += 1

        except Exception as e:
            if getattr(e, 'errno') == 10038:
                return  # Socket closed.

            sys.stderr.write("Could not bind to port: %s\n" % (self.port,))
            sys.stderr.flush()
            traceback.print_exc()
            self.socketError.emit(str(e))

    def stop(self):
        self._isServing = False
        for dispatcher in self.dispatchers:
            dispatcher.close()

        if self._socket:
            self._socket.close()

    def onMsg(self, info: dict):
        self.widgetInfoRecv.emit(info)

    def sendEnableInspect(self, extra: dict):
        for dispatcher in self.dispatchers:
            dispatcher.sendEnableInspect(extra)

    def sendEnableInspectToDispatcher(self, dispatcherId: int, extra: dict):
        dispatcher = self.idToDispatcher.get(dispatcherId)
        if dispatcher:
            dispatcher.sendEnableInspect(extra)

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

    def clearInfo(self):
        self._classNameLine.setValue("")
        self._objectNameLine.setValue("")
        self._sizeLine.setValue("")
        self._posLine.setValue("")
        self._styleSheetLine.setValue("")


class PQIWindow(QtWidgets.QMainWindow):
    sigDisableInspectKeyPressed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQtInspect")
        self.setWindowIcon(get_icon())
        self.resize(700, 1000)

        self._menuBar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menuBar)

        self._moreMenu = QtWidgets.QMenu(self._menuBar)
        self._moreMenu.setTitle("More")
        self._menuBar.addMenu(self._moreMenu)

        # ==================== #
        #     Menu Actions     #
        # ==================== #
        # Press F8 to Disable Inspect Action
        self._pressF8ToDisableInspectAction = QtWidgets.QAction(self)
        self._pressF8ToDisableInspectAction.setText("Press F8 to Finish Inspect")
        self._pressF8ToDisableInspectAction.setCheckable(True)
        self._pressF8ToDisableInspectAction.setChecked(True)  # default
        self._moreMenu.addAction(self._pressF8ToDisableInspectAction)

        # Mock Left Button Down Action
        self._isMockLeftButtonDownAction = QtWidgets.QAction(self)
        self._isMockLeftButtonDownAction.setText("Mock Right Button Down as Left")
        self._isMockLeftButtonDownAction.setCheckable(True)
        self._isMockLeftButtonDownAction.setChecked(True)  # default
        self._moreMenu.addAction(self._isMockLeftButtonDownAction)

        # Attach Action
        self._attachAction = QtWidgets.QAction(self)
        self._attachAction.setText("Attach To Process")
        self._moreMenu.addAction(self._attachAction)
        self._attachAction.triggered.connect(self._onAttachActionTriggered)
        self._attachAction.setEnabled(False)

        self._moreMenu.addSeparator()

        # Setting Action
        self._settingAction = QtWidgets.QAction(self)
        self._settingAction.setText("Settings")
        self._moreMenu.addAction(self._settingAction)
        self._settingAction.triggered.connect(self._openSettingWindow)

        # Child Windows
        self._settingWindow = None
        self._codeWindow = None
        self._attachWindow = None

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
        self._serveButton.setCheckable(True)
        self._serveButton.clicked.connect(self._onServeButtonToggled)

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

        # ==================== #
        #     Create Stack     #
        # ==================== #
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

        # ==================== #
        #     Hierarchy Bar    #
        # ==================== #
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
        self._currDispatcherIdForHoveredWidget = None  # todo 可能会有多选情况
        self._keyboardHookThread = self._generateKeyboardHookThread()

        self._curWidgetId = -1
        self._curHighlightedWidgetId = -1

        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._initConnections()

    def _initConnections(self):
        self.sigDisableInspectKeyPressed.connect(self._onInspectKeyPressed)

    # region For Serve Button
    def _onServeButtonToggled(self, checked: bool):
        if checked:
            try:
                port = int(self._portLineEdit.text())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "PyQtInspect", "Port must be a number")
                self._serveButton.setChecked(False)
                return

            DataCenter.instance.setServerConfig({"port": port})

            self._runWorker()
        else:
            self._askStopWorkerConfirmation()

    def _runWorker(self):
        if self._worker is not None:
            return

        port = DataCenter.instance.port

        self._portLineEdit.setEnabled(False)
        # self._serveButton.setEnabled(False)
        self._inspectButton.setEnabled(True)
        self._attachAction.setEnabled(True)

        self._worker = PQYWorker(None, port)  # The parent of worker must be None!
        self._worker.widgetInfoRecv.connect(self.on_widget_info_recv)
        self._worker.sigNewDispatcher.connect(self.onNewDispatcher)
        self._worker.socketError.connect(self._onWorkerSocketError)
        self._workerThread = QtCore.QThread()

        self._worker.moveToThread(self._workerThread)
        self._workerThread.started.connect(self._worker.run)

        self._workerThread.start()

    def _cleanUpWhenWorkerStopped(self):
        if self._worker is None:
            return

        # clear worker and its thread

        if self._worker is not None:
            self._worker.stop()
            self._worker.deleteLater()
            self._worker = None

        if self._workerThread is not None:
            self._workerThread.quit()
            self._workerThread.wait()
            self._workerThread = None

        # set buttons status to default
        self._portLineEdit.setEnabled(True)
        self._inspectButton.setEnabled(False)

        # set action status to default
        self._attachAction.setEnabled(False)

        # clear ui
        self._widgetBriefWidget.clearInfo()
        self._createStacksListWidget.clearStacks()
        self._hierarchyBar.clearData()

    def _askStopWorkerConfirmation(self):
        """ Ask the user for confirmation to stop the server. """
        self._serveButton.setChecked(True)  # hold the button checked before user's choice

        reply = QtWidgets.QMessageBox.question(self, "PyQtInspect", "Are you sure to stop serving?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self._cleanUpWhenWorkerStopped()
            self._serveButton.setChecked(False)

    def _onWorkerSocketError(self, msg):
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._cleanUpWhenWorkerStopped()
        self._serveButton.setChecked(False)

    # endregion

    def on_widget_info_recv(self, dispatcherId: int, info: dict):
        cmdId = info.get("cmd_id")
        text = info.get("text", "")
        if cmdId == CMD_QT_PATCH_SUCCESS:
            pid = int(text)
            print(f"PyQtInspect: Qt patched successfully, pid: {pid}")

            # If inspection is enabled, enable it for the new process.
            if self._inspectButton.isChecked():
                self._worker.sendEnableInspectToDispatcher(
                    dispatcherId,
                    {'mock_left_button_down': self._isMockLeftButtonDownAction.isChecked()}
                )
        elif cmdId == CMD_WIDGET_INFO:
            self._currDispatcherIdForHoveredWidget = dispatcherId
            self.handleWidgetInfoMsg(json.loads(text))
        elif cmdId == CMD_INSPECT_FINISHED:
            self._currDispatcherIdForSelectedWidget = dispatcherId
            self.handle_inspect_finished_msg()
            self.windowHandle().requestActivate()
        elif cmdId == CMD_EXEC_CODE_ERROR:
            errMsg = text
            self._notifyResultToCodeWindow(True, errMsg)
        elif cmdId == CMD_EXEC_CODE_RESULT:
            result = text
            self._notifyResultToCodeWindow(False, result)
        elif cmdId == CMD_CHILDREN_INFO:
            childrenInfoDict = json.loads(text)
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
        dispatcher.registerMainUIReady()

    def _enableInspect(self):
        self._worker.sendEnableInspect({'mock_left_button_down': self._isMockLeftButtonDownAction.isChecked()})

        if self._pressF8ToDisableInspectAction.isChecked():
            # start keyboard hook thread if user wants to disable inspect by pressing F8
            # TODO: 1) 自定义热键; 2) 当用户打开开关时, 且处于inspect, 立即运行线程
            self._keyboardHookThread.start()

    def _disableInspect(self):
        self._worker.sendDisableInspect()
        self._currDispatcherIdForSelectedWidget = None

        if self._keyboardHookThread.isRunning():
            self._keyboardHookThread.quit()

    def _onInspectButtonClicked(self, checked: bool):
        if self._worker is None:
            return
        if checked:
            self._enableInspect()
        else:
            self._disableInspect()

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

    def _onAttachActionTriggered(self):
        if self._attachWindow is None:
            self._attachWindow = AttachWindow(self)
        self._attachWindow.show()

    # region For Keyboard Hook to disable inspect
    def _generateKeyboardHookThread(self):
        def _inSubThread():
            import PyQtInspect._pqi_bundle.pqi_keyboard_hook_win as kb_hook
            kb_hook.grab(0x77, lambda: self.sigDisableInspectKeyPressed.emit())

        thread = QtCore.QThread(self)
        thread.started.connect(_inSubThread)
        return thread

    def _onInspectKeyPressed(self):
        """ 当停止inspect热键按下后, 停止inspect """
        self._inspectButton.setChecked(False)
        self._finishInspectWhenKeyPress()

    def _finishInspectWhenKeyPress(self):
        """ todo """
        self._disableInspect()
        self._currDispatcherIdForSelectedWidget = self._currDispatcherIdForHoveredWidget
    # endregion


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = PQIWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
