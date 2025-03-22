# -*- coding: utf-8 -*-
import typing

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQtInspect._pqi_bundle.pqi_comm_constants import TreeViewKeys


class _DefaultOptions:
    HighlightWhenHover = True


class _CustomDataRole:
    WidgetId = QtCore.Qt.UserRole + 1


class ControlTreeView(QtWidgets.QTreeView):
    sigMouseLeave = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Disable editing

    def leaveEvent(self, ev):
        self.sigMouseLeave.emit()
        return super().leaveEvent(ev)


class ControlTreeWindow(QtWidgets.QWidget):
    sigReqControlTree = QtCore.pyqtSignal(bool)  # param1: need to locate current widget
    sigReqCurrentSelectedWidgetId = QtCore.pyqtSignal()
    sigReqInspectWidget = QtCore.pyqtSignal(object)
    sigReqHighlightWidget = QtCore.pyqtSignal(object)
    sigReqUnhighlightWidget = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint)
        self.resize(800, 500)

        self.setWindowTitle('Control Tree View')

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(8, 8, 8, 8)

        self._buttonLayout = QtWidgets.QHBoxLayout()
        self._mainLayout.addLayout(self._buttonLayout)

        self._updateButton = QtWidgets.QPushButton(self)
        self._updateButton.setText("Refresh")
        self._updateButton.clicked.connect(self._onRefreshButtonClicked)
        self._buttonLayout.addWidget(self._updateButton)

        self._locateButton = QtWidgets.QPushButton(self)
        self._locateButton.setText("Locate")
        self._locateButton.clicked.connect(self._onLocateButtonClicked)
        self._buttonLayout.addWidget(self._locateButton)

        self._inspectButton = QtWidgets.QPushButton(self)
        self._inspectButton.setText("Inspect")
        self._inspectButton.clicked.connect(self._inspectCurrentRow)
        self._buttonLayout.addWidget(self._inspectButton)

        self._treeWidget = ControlTreeView(self)

        self._mainLayout.addWidget(self._treeWidget)

        self._model = QtGui.QStandardItemModel(self._treeWidget)
        self._treeWidget.setModel(self._model)
        self._treeWidget.setMouseTracking(_DefaultOptions.HighlightWhenHover)
        self._treeWidget.entered.connect(self._onTreeViewEntered)
        self._treeWidget.sigMouseLeave.connect(self._onMouseLeave)
        self._treeWidget.selectionModel().currentRowChanged.connect(self._onCurrentRowChanged)

        self._highlightWhenHoverOption = QtWidgets.QCheckBox(self)
        self._highlightWhenHoverOption.setText("When hovering a row, highlight the corresponding widget")
        self._highlightWhenHoverOption.setChecked(_DefaultOptions.HighlightWhenHover)
        self._highlightWhenHoverOption.stateChanged.connect(self._onHighlightWhenHoverOptionChanged)

        self._mainLayout.addWidget(self._highlightWhenHoverOption)

    def notifyControlTreeInfo(self, controlTreeInfo: typing.List[typing.Dict]):
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Object", "Type", "Child Count"])
        self._treeWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._treeWidget.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self._addSubItems(self._model, controlTreeInfo)

    def notifyLocateWidget(self, widgetId: int):
        """ Locate the widget in the tree view. """

        def _find_helper(cur_item: QtGui.QStandardItem) -> bool:
            for i in range(cur_item.rowCount()):
                res = _find_helper(cur_item.child(i))
                if res:
                    # expand
                    self._treeWidget.setExpanded(cur_item.index(), True)
                    return True

            if cur_item.data(_CustomDataRole.WidgetId) == widgetId:
                # select the row
                self._treeWidget.setCurrentIndex(cur_item.index())
                return True
            return False
        # Firstly, clear the index
        self._treeWidget.selectionModel().clearCurrentIndex()
        _find_helper(self._model.invisibleRootItem())

    def refresh(self):
        self._model.clear()
        self.sigReqControlTree.emit(True)

    def _addSubItems(self, parentItem, childrenInfoList):
        """ Recursively add sub items to the tree view. """
        for childInfo in childrenInfoList:
            widgetObjNameItem = QtGui.QStandardItem(childInfo[TreeViewKeys.OBJ_NAME_KEY])
            widgetObjNameItem.setData(childInfo[TreeViewKeys.OBJ_ID_KEY], _CustomDataRole.WidgetId)
            widgetTypeItem = QtGui.QStandardItem(childInfo[TreeViewKeys.OBJ_CLS_NAME_KEY])
            widgetChildCountItem = QtGui.QStandardItem(str(childInfo[TreeViewKeys.CHILD_CNT_KEY]))

            parentItem.appendRow([widgetObjNameItem, widgetTypeItem, widgetChildCountItem])

            self._addSubItems(widgetObjNameItem, childInfo[TreeViewKeys.CHILDREN_KEY])

    # region Event handlers
    def _onRefreshButtonClicked(self):
        self.refresh()

    def _onLocateButtonClicked(self):
        self.sigReqCurrentSelectedWidgetId.emit()

    def _inspectCurrentRow(self):
        index = self._treeWidget.currentIndex()
        if index.isValid():
            first_col_sibling = index.siblingAtColumn(0)
            wgtId = first_col_sibling.data(_CustomDataRole.WidgetId)
            self.sigReqInspectWidget.emit(wgtId)

    def _reqHighlightWidgetByIndex(self, index: QtCore.QModelIndex):
        first_col_sibling = index.siblingAtColumn(0)
        wgtId = first_col_sibling.data(_CustomDataRole.WidgetId)
        self.sigReqHighlightWidget.emit(wgtId)

    def _onCurrentRowChanged(self, index: QtCore.QModelIndex, prevIndex: QtCore.QModelIndex):
        self._reqHighlightWidgetByIndex(index)

    def _onTreeViewEntered(self, index: QtCore.QModelIndex):
        self._reqHighlightWidgetByIndex(index)

    def _onMouseLeave(self):
        curIndex = self._currentSelectedIndex()
        if curIndex.isValid():
            self._reqHighlightWidgetByIndex(curIndex)

    def _onHighlightWhenHoverOptionChanged(self, state):
        self._treeWidget.setMouseTracking(state == QtCore.Qt.Checked)

    def closeEvent(self, ev):
        self.sigReqUnhighlightWidget.emit()
        return super().closeEvent(ev)

    # endregion

    # region helpers
    def _currentSelectedIndex(self) -> QtCore.QModelIndex:
        return self._treeWidget.currentIndex()
    # endregion
