# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/24 17:36
# Description: 
# ==============================================
import pathlib
import sys
import typing

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect.pqi_gui.workers.pqy_worker import PQYWorker, DUMMY_WORKER, DummyWorker

pyqt_inspect_module_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if pyqt_inspect_module_dir not in sys.path:
    sys.path.insert(0, pyqt_inspect_module_dir)

import json

from PyQt5 import QtWidgets, QtCore
from PyQtInspect.pqi_gui.attach_window import AttachWindow
from PyQtInspect.pqi_gui.create_stacks_list_widget import CreateStacksListWidget
from PyQtInspect._pqi_bundle.pqi_comm_constants import CMD_WIDGET_INFO, CMD_INSPECT_FINISHED, CMD_EXEC_CODE_ERROR, \
    CMD_EXEC_CODE_RESULT, CMD_CHILDREN_INFO, CMD_QT_PATCH_SUCCESS

import ctypes

from PyQtInspect.pqi_gui.code_window import CodeWindow
from PyQtInspect.pqi_gui.hierarchy_bar import HierarchyBar
from PyQtInspect.pqi_gui.settings_window import SettingWindow
from PyQtInspect.pqi_gui.styles import GLOBAL_STYLESHEET
import PyQtInspect.pqi_gui.data_center as DataCenter
from PyQtInspect.pqi_gui._pqi_res import get_icon
from PyQtInspect.pqi_gui.keyboard_hook_handler import KeyboardHookHandler


# ==== SetupHolder ====
from PyQtInspect._pqi_common.pqi_setup_holder import SetupHolder

SetupHolder.setup = {
    'server': True
}

if sys.platform == "win32":
    myappid = 'jeza.tools.pyqt_inspect.0.0.1alpha2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


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
    _sigInspectFinished = QtCore.pyqtSignal()
    _sigInspectBegin = QtCore.pyqtSignal()
    _sigInspectDisabled = QtCore.pyqtSignal()

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
        #    Top Container   #
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
        self._currDispatcherIdForHoveredWidget = None  # todo 可能会有多个进程都有选中的情况?

        self._curWidgetId = -1
        self._curHighlightedWidgetId = -1

        self.setStyleSheet(GLOBAL_STYLESHEET)

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

    # endregion

    def on_widget_info_recv(self, dispatcherId: int, info: dict):
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
        self._getWorker().sendDisableInspect()  # disable inspect for all dispatchers
        self._sigInspectFinished.emit()

    def onNewDispatcher(self, dispatcher):
        dispatcher.sigMsg.connect(self.on_widget_info_recv)
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

    def _notifyExecCodeInSelectedWidget(self, code: str):
        worker = self._getWorker()
        if not worker or self._currDispatcherIdForSelectedWidget is None:
            return

        worker.sendExecCodeEvent(self._currDispatcherIdForSelectedWidget, code)

    def _onAncestorWidgetItemHighlight(self, widgetId: str):
        worker = self._getWorker()
        if worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        widgetId = int(widgetId)
        # unhighlight prev widget, and highlight current widget
        self._unhighlightPrevWidget()
        worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId, True)
        self._curHighlightedWidgetId = widgetId

    def _onAncestorWidgetItemClicked(self, widgetId: str):
        worker = self._getWorker()
        if not worker or self._currDispatcherIdForSelectedWidget is None:
            return

        widgetId = int(widgetId)

        self._worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        self._worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId, {
            "from": "ancestor"
        })  # 通过bar来点击回溯获取祖先控件的信息, 带上from字段, 避免覆盖祖先控件信息(即点击导航条前面的类后, 该类后面的类全都无了, 因为此时显示的是该类的祖先控件信息)
        self._worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)  # todo 会不会有时序问题

    def _onChildWidgetItemHighlight(self, widgetId: str):
        worker = self._getWorker()
        if worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        widgetId = int(widgetId)
        # unhighlight prev widget, and highlight current widget
        self._unhighlightPrevWidget()
        worker.sendHighlightWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId, True)
        self._curHighlightedWidgetId = widgetId

    def _onChildWidgetItemClicked(self, widgetId: str):
        worker = self._getWorker()
        if worker is None or self._currDispatcherIdForSelectedWidget is None:
            return

        widgetId = int(widgetId)
        worker.sendSelectWidgetEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        self._unhighlightPrevWidget()
        worker.sendRequestWidgetInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)
        worker.sendRequestChildrenInfoEvent(self._currDispatcherIdForSelectedWidget, widgetId)

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
        worker = self._getWorker()
        if worker is not None and self._currDispatcherIdForSelectedWidget is not None:
            widgetId = int(widgetIdStr)
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

    def _onAttachActionTriggered(self):
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

    # endregion

    def closeEvent(self, a0):
        self.cleanUp()

    def cleanUp(self):
        self._disableInspect()


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


def main():
    import sys

    # Check if the debug option is set.
    debug_option = '--debug'
    if debug_option in sys.argv:
        sys.argv.remove(debug_option)
        _set_debug()

    # open high-resolution support
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    app = QtWidgets.QApplication(sys.argv)
    window = PQIWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
