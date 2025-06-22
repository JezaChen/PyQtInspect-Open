# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/24 17:36
# Description: 
# ==============================================
import pathlib
import sys
import typing
import argparse
import json
import ctypes

# Ensure the ``PyQtInspect`` module is in the sys.path
pyqt_inspect_module_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if pyqt_inspect_module_dir not in sys.path:
    sys.path.insert(0, pyqt_inspect_module_dir)

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect.pqi_gui.workers.pqy_worker import PQYWorker, DUMMY_WORKER, DummyWorker

pyqt_inspect_module_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if pyqt_inspect_module_dir not in sys.path:
    sys.path.insert(0, pyqt_inspect_module_dir)

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQtInspect.pqi_gui.windows.attach_window import AttachWindow
from PyQtInspect.pqi_gui.create_stacks_list_widget import CreateStacksListWidget
from PyQtInspect._pqi_bundle.pqi_comm_constants import (
    CMD_WIDGET_INFO, CMD_INSPECT_FINISHED, CMD_EXEC_CODE_ERROR,
    CMD_EXEC_CODE_RESULT, CMD_CHILDREN_INFO, CMD_QT_PATCH_SUCCESS, CMD_CONTROL_TREE,
    CMD_EXIT, TreeViewResultKeys, TreeViewExtraKeys
)
from PyQtInspect.pqi_gui.windows.code_window import CodeWindow
from PyQtInspect.pqi_gui.hierarchy_bar import HierarchyBar
from PyQtInspect.pqi_gui.windows.settings_window import SettingWindow
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET
import PyQtInspect.pqi_gui.data_center as DataCenter
from PyQtInspect.pqi_gui._pqi_res import get_icon
from PyQtInspect.pqi_gui.keyboard_hook_handler import KeyboardHookHandler
from PyQtInspect._pqi_common.pqi_setup_holder import SetupHolder
from PyQtInspect import version


def _setup():
    # ==== SetupHolder ====
    setup_dict = {'server': True}

    if SetupHolder.setup is not None:
        SetupHolder.setup.update(setup_dict)
    else:
        SetupHolder.setup = setup_dict

    # ==== Set App ID For Windows ====
    if sys.platform == "win32":
        myappid = 'jeza.tools.pyqt_inspect.0.0.1alpha2'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


_setup()

# ==== Default Values ====
_DEFAULT_PORT = 19394


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
        self._keyLabel.setMinimumWidth(90)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QLineEdit(self)
        self._valueLineEdit.setObjectName("codeStyleLineEdit")
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._valueLineEdit.setReadOnly(True)
        self._valueLineEdit.textChanged.connect(self._updateToolTipForValueLineEdit)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)

    def _updateToolTipForValueLineEdit(self, text: str):
        # If the text is too long, set the tooltip to the full text.
        metrics = self._valueLineEdit.fontMetrics()
        if metrics.width(text) > self._valueLineEdit.width():
            self._valueLineEdit.setToolTip(text)
        else:
            self._valueLineEdit.setToolTip("")


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
    _sigInspectFinished = QtCore.pyqtSignal()
    _sigInspectBegin = QtCore.pyqtSignal()
    _sigInspectDisabled = QtCore.pyqtSignal()

    def __init__(self, parent=None, defaultPort: int = _DEFAULT_PORT):
        super().__init__(parent)

        self.setWindowTitle(self._getWindowTitle())
        self.setWindowIcon(get_icon())
        self.resize(700, 1000)

        # region -- Menu bar --
        self._menuBar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menuBar)

        # region -- View Menu --
        self._viewMenu = QtWidgets.QMenu(self._menuBar)
        self._viewMenu.setTitle("Tool")
        self._menuBar.addMenu(self._viewMenu)

        self._controlTreeAction = QtWidgets.QAction(self)
        self._controlTreeAction.setText("Control Tree")
        self._viewMenu.addAction(self._controlTreeAction)
        self._viewMenu.triggered.connect(self._openControlTreeWindow)
        # endregion

        # region -- More Menu --
        self._moreMenu = QtWidgets.QMenu(self._menuBar)
        self._moreMenu.setTitle("More")
        self._menuBar.addMenu(self._moreMenu)

        # ==================== #
        #     Menu Actions     #
        # ==================== #
        # Always on Top Action
        self._alwaysOnTopAction = QtWidgets.QAction(self)
        self._alwaysOnTopAction.setText("Always on Top")
        self._alwaysOnTopAction.setCheckable(True)
        self._alwaysOnTopAction.setChecked(False)  # default
        # Use trigger instead of toggled
        # because the toggled signal will be emitted when the `setChecked` method in the code is called
        self._alwaysOnTopAction.triggered.connect(self._onAlwaysOnTopActionToggled)
        self._moreMenu.addAction(self._alwaysOnTopAction)

        # Press F8 to Disable Inspect Action
        self._keyboardHookHandler = KeyboardHookHandler(self)

        self._pressF8ToDisableInspectAction = QtWidgets.QAction(self)
        self._pressF8ToDisableInspectAction.setText("Press F8 to Finish Inspect")
        self._pressF8ToDisableInspectAction.setCheckable(True)
        self._pressF8ToDisableInspectAction.setEnabled(self._keyboardHookHandler.isValid())
        self._pressF8ToDisableInspectAction.setChecked(self._keyboardHookHandler.isValid())  # default
        # --- Connect Signals ---
        # main gui -> keyboard hook handler
        self._sigInspectBegin.connect(self._keyboardHookHandler.onInspectBegin)
        self._sigInspectFinished.connect(self._keyboardHookHandler.onInspectFinished)
        self._sigInspectDisabled.connect(self._keyboardHookHandler.onInspectDisabled)
        self._pressF8ToDisableInspectAction.toggled.connect(self._keyboardHookHandler.setEnable)
        # keyboard hook handler -> main gui
        self._keyboardHookHandler.sigDisableInspectKeyPressed.connect(self._onInspectKeyPressed)

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
        self._attachAction.triggered.connect(self._openAttachWindow)
        self._attachAction.setEnabled(False)

        self._moreMenu.addSeparator()

        # Open Log Folder Action
        self._openLogDirAction = QtWidgets.QAction(self)
        self._openLogDirAction.setText("Open Log Folder")
        self._moreMenu.addAction(self._openLogDirAction)
        self._openLogDirAction.triggered.connect(self._openLogDir)

        # Clear Logs Action
        self._clearLogsAction = QtWidgets.QAction(self)
        self._clearLogsAction.setText("Clear Logs")
        self._moreMenu.addAction(self._clearLogsAction)
        self._clearLogsAction.triggered.connect(self._clearLogs)

        self._moreMenu.addSeparator()

        # Setting Action
        self._settingAction = QtWidgets.QAction(self)
        self._settingAction.setText("Settings")
        self._moreMenu.addAction(self._settingAction)
        self._settingAction.triggered.connect(self._openSettingWindow)

        self._moreMenu.addSeparator()

        # About Action
        self._aboutAction = QtWidgets.QAction(self)
        self._aboutAction.setText("About")
        self._moreMenu.addAction(self._aboutAction)
        self._aboutAction.triggered.connect(self._openAboutWindow)

        # endregion

        # endregion

        # region -- Child Windows Definition --
        self._settingWindow = None
        self._codeWindow = None
        self._attachWindow = None
        self._controlTreeViewWindow = None  # None | ControlTreeViewWindow
        # endregion

        # region -- Main Container --
        self._mainContainer = QtWidgets.QWidget(self)
        self.setCentralWidget(self._mainContainer)
        self._mainLayout = QtWidgets.QVBoxLayout(self._mainContainer)
        self._mainLayout.setContentsMargins(4, 4, 4, 4)
        self._mainLayout.setSpacing(0)


        # region -- Top Container --
        self._topContainer = QtWidgets.QWidget(self)
        self._topContainer.setFixedHeight(30)
        self._topContainer.move(0, 0)

        self._topLayout = QtWidgets.QHBoxLayout(self._topContainer)
        self._topLayout.setContentsMargins(0, 0, 0, 0)
        self._topLayout.setSpacing(0)

        self._portLabel = QtWidgets.QLabel(self._topContainer)
        self._portLabel.setText("Port: ")
        self._portLabel.setFixedHeight(30)
        self._portLabel.setFixedWidth(50)
        self._portLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._portLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._topLayout.addWidget(self._portLabel)

        self._portLineEdit = QtWidgets.QLineEdit(self._topContainer)
        self._portLineEdit.setFixedHeight(30)
        self._portLineEdit.setText(str(defaultPort))
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
        # endregion

        # region -- Create Stack --
        self._createStackGroupBox = QtWidgets.QGroupBox(self)
        self._createStackGroupBox.setTitle("Create Stack")

        self._createStackGroupBoxLayout = QtWidgets.QVBoxLayout(self._createStackGroupBox)
        self._createStackGroupBoxLayout.setContentsMargins(4, 4, 4, 6)
        self._createStackGroupBoxLayout.setSpacing(0)

        self._createStacksListWidget = CreateStacksListWidget(self)
        self._createStacksListWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._createStackGroupBoxLayout.addWidget(self._createStacksListWidget)

        self._mainLayout.addSpacing(3)
        self._mainLayout.addWidget(self._createStackGroupBox)
        # endregion

        # region -- Hierarchy Bar --
        self._hierarchyBar = HierarchyBar(self)
        self._hierarchyBar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._hierarchyBar.sigAncestorItemHovered.connect(self._highlightWidget)
        self._hierarchyBar.sigAncestorItemChanged.connect(self._onAncestorWidgetItemClicked)
        self._hierarchyBar.sigChildMenuItemHovered.connect(self._highlightWidget)
        self._hierarchyBar.sigChildMenuItemClicked.connect(self._inspectWidget)
        self._hierarchyBar.sigReqChildWidgetsInfo.connect(self._reqChildWidgetsInfo)
        self._hierarchyBar.sigMouseLeaveBarAndMenu.connect(self._unhighlightPrevWidget)

        self._mainLayout.addSpacing(3)
        self._mainLayout.addWidget(self._hierarchyBar)
        # endregion

        # endregion

        # region -- Data --
        self._worker = None
        self._currDispatcherIdForSelectedWidget = None
        self._currDispatcherIdForHoveredWidget = None  # todo 可能会有多个进程都有选中的情况?

        self._curWidgetId = -1
        self._curHighlightedWidgetId = -1
        # endregion

        self.setStyleSheet(GLOBAL_STYLESHEET)

    # region -- For always on top action --
    def _onAlwaysOnTopActionToggled(self, checked: bool):
        window = self.windowHandle()
        if window is None:
            # Fallback logic
            # it will cause a short blink when the window is shown again
            if checked:
                self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            # After changing the window flags, the window will be hidden, we need to show it again.
            self.show()
        else:  # window is not None
            if checked:
                window.setFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            else:
                window.setFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
    # endregion

    # region -- For Serve Button --
    def _onServeButtonToggled(self, checked: bool):
        if checked:
            self._startServer()
        else:
            self._stopServer()

    def _startServer(self):
        try:
            port = int(self._portLineEdit.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "PyQtInspect", "Port must be a number")
            self._serveButton.setChecked(False)
            return

        DataCenter.instance.setServerConfig({"port": port})

        self._runWorker()

    def _stopServer(self):
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
        self._worker.sigWidgetInfoRecv.connect(self.onWidgetInfoRecv)
        self._worker.sigNewDispatcher.connect(self.onNewDispatcher)
        self._worker.sigSocketError.connect(self._onWorkerSocketError)
        self._worker.sigDispatcherExited.connect(self._onDispatcherExited)
        # Fix issue #16: use queued connection to avoid recursive call of `PQYWorker.stop`
        self._worker.sigAllDispatchersExited.connect(self._onAllDispatchersExited, QtCore.Qt.QueuedConnection)
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

    def _getWorker(self) -> typing.Union[PQYWorker, DummyWorker]:
        if self._worker is None:
            return DUMMY_WORKER
        return self._worker

    def _askStopWorkerConfirmation(self):
        """ Ask the user for confirmation to stop the server. """
        self._serveButton.setChecked(True)  # hold the button checked before user's choice

        reply = QtWidgets.QMessageBox.question(self, "PyQtInspect", "Are you sure to stop serving?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self._disableInspect()  # disable inspect for all dispatchers before stopping the server
            self._cleanUpWhenWorkerStopped()
            self._serveButton.setChecked(False)

    def _onWorkerSocketError(self, msg):
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._cleanUpWhenWorkerStopped()
        self._serveButton.setChecked(False)

    def _onDispatcherExited(self, dispatcherId: int):
        """ Only log the info when a dispatcher exited. """
        pqi_log.info(f"PyQtInspect: Dispatcher {dispatcherId} exited.")

    def _onAllDispatchersExited(self):
        """ Only log the info when all dispatchers exited. """
        pqi_log.info("PyQtInspect: All dispatchers exited.")

    # endregion

    def onWidgetInfoRecv(self, dispatcherId: int, info: dict):
        cmdId = info.get("cmd_id")
        text = info.get("text", "")
        if cmdId == CMD_QT_PATCH_SUCCESS:
            pid = int(text)
            pqi_log.info(f"PyQtInspect: Qt patched successfully, pid: {pid}")

            # If inspection is enabled, enable it for the new process.
            if self._inspectButton.isChecked():
                self._getWorker().sendEnableInspectToDispatcher(
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
        elif cmdId == CMD_CONTROL_TREE:
            result = json.loads(text)
            controlTreeInfo = result[TreeViewResultKeys.TREE_INFO_KEY]
            extra = result[TreeViewResultKeys.EXTRA_KEY]
            self._notifyResultToControlTreeViewWindow(controlTreeInfo, extra)
        elif cmdId == CMD_EXIT:  # the client has exited elegantly
            pqi_log.info(f"PyQtInspect: Dispatcher {dispatcherId} exited elegantly.")

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
        self._getWorker().sendDisableInspect()  # disable inspect for all dispatchers
        self._sigInspectFinished.emit()

    def onNewDispatcher(self, dispatcher):
        dispatcher.sigMsg.connect(self.onWidgetInfoRecv)
        dispatcher.registerMainUIReady()

    def _enableInspect(self):
        worker = self._getWorker()
        if not worker:
            return
        worker.sendEnableInspect({'mock_left_button_down': self._isMockLeftButtonDownAction.isChecked()})
        self._sigInspectBegin.emit()

    def _disableInspect(self):
        self._getWorker().sendDisableInspect()
        self._currDispatcherIdForSelectedWidget = None
        self._sigInspectDisabled.emit()

    def _onInspectButtonClicked(self, checked: bool):
        if not self._getWorker():
            return
        if checked:
            self._enableInspect()
        else:
            self._disableInspect()

    def _onAncestorWidgetItemClicked(self, widgetId: int):
        worker = self._getWorker()
        if not worker or self._currDispatcherIdForSelectedWidget is None:
            return

        self._worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        self._worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId, {
            "from": "ancestor"
        })  # 通过bar来点击回溯获取祖先控件的信息, 带上from字段, 避免覆盖祖先控件信息(即点击导航条前面的类后, 该类后面的类全都无了, 因为此时显示的是该类的祖先控件信息)
        self._worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)  # todo 会不会有时序问题

    def _highlightWidget(self, widgetId: int):
        """ Highlight the widget with the given widgetId, but not inspect it.
        """
        worker = self._getWorker()
        if worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        # unhighlight prev widget, and highlight current widget
        self._unhighlightPrevWidget()
        worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId, True)
        self._curHighlightedWidgetId = widgetId

    def _inspectWidget(self, widgetId: int):
        worker = self._getWorker()
        if worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)

    # region -- Setting window --
    def _openSettingWindow(self):
        if self._settingWindow is None:
            self._settingWindow = SettingWindow(self)
        self._settingWindow.show()

    # endregion

    # region -- code exec --
    def _openCodeWindow(self):
        if self._codeWindow is None:
            self._codeWindow = CodeWindow(self)
            self._codeWindow.sigExecCode.connect(self._notifyExecCodeInSelectedWidget)
        self._codeWindow.show()

    def _notifyExecCodeInSelectedWidget(self, code: str):
        worker = self._getWorker()
        if not worker or self._currDispatcherIdForSelectedWidget is None:
            return

        worker.sendExecCodeEvent(self._currDispatcherIdForSelectedWidget, code)

    def _notifyResultToCodeWindow(self, isErr: bool, result: str):
        if self._codeWindow is None:
            return
        self._codeWindow.notifyResult(isErr, result)
    # endregion

    def _reqChildWidgetsInfo(self, widgetId: int):
        worker = self._getWorker()
        if worker is not None and self._currDispatcherIdForSelectedWidget is not None:
            worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)

    def _unhighlightPrevWidget(self):
        # todo 貌似不用这样了现在, pqi可以保证只有一个widget能高亮
        worker = self._getWorker()
        conditions_met = (
            bool(worker),
            self._currDispatcherIdForSelectedWidget is not None,
            self._curHighlightedWidgetId != -1
        )

        if all(conditions_met):
            worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget,
                                            self._curHighlightedWidgetId,
                                            False)
            self._curHighlightedWidgetId = -1

    def _openAttachWindow(self):
        if self._attachWindow is None:
            self._attachWindow = AttachWindow(self)
        self._attachWindow.show()

    def _onInspectKeyPressed(self):
        """ 当停止inspect热键按下后, 停止inspect """
        self._inspectButton.setChecked(False)
        self._finishInspectWhenKeyPress()

    def _finishInspectWhenKeyPress(self):
        self._disableInspect()
        # override self._currDispatcherIdForSelectedWidget
        # todo 看看有没有更好的办法
        self._currDispatcherIdForSelectedWidget = self._currDispatcherIdForHoveredWidget

        _worker = self._getWorker()
        # notify the client to select the widget (the widget is marked as inspected only before)
        _worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, self._curWidgetId)
        # we must set the highlight status of this widget to false, because it is hovered before
        _worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, self._curWidgetId, False)

    def closeEvent(self, a0):
        self.cleanUp()

    def cleanUp(self):
        self._disableInspect()
        self._cleanUpWhenWorkerStopped()

    # region APIs
    def setPort(self, port: int):
        """ Set the port to listen. """
        if self._portLineEdit.isEnabled():
            self._portLineEdit.setText(str(port))

    def listen(self, newPort: typing.Optional[int] = None):
        """ Start the server to listen to the port. """
        if newPort is not None:
            self.setPort(newPort)
        self._startServer()

    def stop(self):
        """ Stop the server. """
        self._stopServer()

    @classmethod
    def createWindow(cls, args: argparse.Namespace):
        """ A factory method to create a window. """
        window = cls(defaultPort=args.port)
        return window

    # endregion

    # region About & Title
    def _openAboutWindow(self):
        QtWidgets.QMessageBox.about(self, "About PyQtInspect",
                                    f"PyQtInspect {version.PQI_VERSION}\n"
                                    "© 2025 Jeza Chen (陈建彰)\n\n"
                                    "PyQtInspect is a tool for developers to inspect the native elements in the running PyQt/PySide applications.")

    def _getWindowTitle(self) -> str:
        return f"PyQtInspect {version.PQI_VERSION}"
    # endregion

    # region Control tree
    def _openControlTreeWindow(self):
        if self._controlTreeViewWindow is None:
            from PyQtInspect.pqi_gui.windows.control_tree_view_window import ControlTreeWindow
            self._controlTreeViewWindow = ControlTreeWindow(self)
            w = self._controlTreeViewWindow
            # signals
            w.sigReqControlTree.connect(self._reqControlTreeInCurrentProcess)
            w.sigReqCurrentSelectedWidgetId.connect(
                self._notifyCurrentSelectedWidgetIdToControlTreeView
            )
            w.sigReqHighlightWidget.connect(self._highlightWidget)
            w.sigReqUnhighlightWidget.connect(self._unhighlightPrevWidget)
            w.sigReqInspectWidget.connect(self._inspectWidget)
        self._controlTreeViewWindow.show()
        self._controlTreeViewWindow.refresh()

    def _reqControlTreeInCurrentProcess(self, needToLocateCurWidget: bool):
        worker = self._getWorker()
        if not worker or self._currDispatcherIdForSelectedWidget is None:
            return
        extra = {}
        if needToLocateCurWidget:
            extra = {TreeViewExtraKeys.CURRENT_WIDGET_ID: self._curWidgetId}
        worker.sendRequestControlTreeInfoEvent(self._currDispatcherIdForSelectedWidget, extra)

    def _notifyResultToControlTreeViewWindow(self, controlTreeInfo: typing.List[typing.Dict], extra: typing.Dict):
        if self._controlTreeViewWindow is None:
            return
        self._controlTreeViewWindow.notifyControlTreeInfo(controlTreeInfo)
        if TreeViewExtraKeys.CURRENT_WIDGET_ID in extra:
            self._controlTreeViewWindow.notifyLocateWidget(extra[TreeViewExtraKeys.CURRENT_WIDGET_ID])

    def _notifyCurrentSelectedWidgetIdToControlTreeView(self):
        if self._controlTreeViewWindow is None:
            return
        self._controlTreeViewWindow.notifyLocateWidget(self._curWidgetId)
    # endregion


    # region Logging
    def _openLogDir(self):
        """ Open the log directory in the file explorer."""
        log_dir = pqi_log.getLogDirPath()
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(log_dir.resolve())))

    def _clearLogs(self):
        """ Clear the logs in the console and file. """
        reply = QtWidgets.QMessageBox.question(
            self,
            self._getWindowTitle(),
            "Are you sure you want to delete all logs? (The current log will be kept)",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            pqi_log.clear_logs()
            QtWidgets.QMessageBox.information(self, self._getWindowTitle(),
                                              "All logs except the current one have been deleted.")
    # endregion

class DirectModePQIWindow(PQIWindow):
    def __init__(self, parent=None, defaultPort: int = _DEFAULT_PORT):
        super().__init__(parent, defaultPort)
        # Hide the top container and the attach action because in the direct mode
        # the server connects to the only one process.
        self._serveButton.setVisible(False)
        self._attachAction.setVisible(False)

    def _onAllDispatchersExited(self):
        """ Override the method to close the window when all dispatchers exited. """
        super()._onAllDispatchersExited()
        self._cleanUpWhenWorkerStopped()
        self.close()

    @classmethod
    def createWindow(cls, args: argparse.Namespace):
        """ Create a window in direct mode. """
        window = cls(defaultPort=args.port)
        window.listen()  # start the server directly after the window is created.

        return window

    def _getWindowTitle(self) -> str:
        return super()._getWindowTitle() + " (Direct Mode)"


def _set_debug():
    import logging
    from PyQtInspect._pqi_bundle.pqi_contants import DebugInfoHolder

    # SetupHolder.setup
    SetupHolder.setup.update({
        'DEBUG_RECORD_SOCKET_READS': True,
        'LOG_TO_FILE_LEVEL': logging.DEBUG,
        'LOG_TO_CONSOLE_LEVEL': logging.DEBUG
    })
    # DebugInfoHolder (for logging)
    DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = SetupHolder.setup.get(
        'DEBUG_RECORD_SOCKET_READS',
        DebugInfoHolder.DEBUG_RECORD_SOCKET_READS)
    DebugInfoHolder.LOG_TO_FILE_LEVEL = SetupHolder.setup.get('LOG_TO_FILE_LEVEL', DebugInfoHolder.LOG_TO_FILE_LEVEL)
    DebugInfoHolder.LOG_TO_CONSOLE_LEVEL = SetupHolder.setup.get('LOG_TO_CONSOLE_LEVEL',
                                                                 DebugInfoHolder.LOG_TO_CONSOLE_LEVEL)


def _createWindow(args: argparse.Namespace):
    if args.direct:  # direct mode
        return DirectModePQIWindow.createWindow(args)

    # default
    return PQIWindow.createWindow(args)


def main():
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug', action='store_true', help='Set debug mode'
    )
    parser.add_argument(
        '--direct',
        action='store_true',
        help='Set direct mode, it will hide the top container and listen to the port directly'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Set the port to listen',
        default=_DEFAULT_PORT
    )

    args = parser.parse_args()  # type: argparse.Namespace

    # Check if the debug option is set.
    if args.debug:
        _set_debug()

    # open high-resolution support
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    app = QtWidgets.QApplication(sys.argv)

    # Use the fusion palette for macOS
    if sys.platform == "darwin":
        style = QtWidgets.QStyleFactory.create("Fusion")
        if style:
            fusion_palette = style.standardPalette()
            fusion_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 255, 255))
            app.setPalette(fusion_palette)

    window = _createWindow(args)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
