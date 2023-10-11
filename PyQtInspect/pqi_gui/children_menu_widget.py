# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/10/11 14:27
# Description: 
# ==============================================
import typing

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQt5.QtWidgets import QWidget, QListView
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QStandardItem, QStandardItemModel


class ChildrenMenuWidget(QWidget):
    sigClickChild = QtCore.pyqtSignal(str)
    sigHoverChild = QtCore.pyqtSignal(str)

    def __init__(self, parent, menu):
        super().__init__(parent)

        self.setObjectName("MenuWidget")
        self._menu = menu  # 需要保存menu, 用于设置数据时调整menu的大小
        # self.resize(217, 289)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listView = QtWidgets.QListView(self)
        self.listView.setStyleSheet("""
        QListView {
            border:none;
            background:transparent;
        }
        
        QToolTip {
            background-color: #ffffff;
            color: #000000;
            border: none;
            font-size: 12px;
        """)
        self.listView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listView.setObjectName("listView")
        self.verticalLayout.addWidget(self.listView)

        self._model = QStandardItemModel(self)
        self.listView.setModel(self._model)

        self.listView.setSpacing(0)
        self.listView.setViewMode(QListView.ListMode)
        self.listView.setResizeMode(QListView.Adjust)
        self.listView.setDragEnabled(False)
        self.listView.setMouseTracking(True)
        self.listView.setEditTriggers(QListView.NoEditTriggers)
        self.listView.clicked.connect(self.onListViewClicked)
        self.listView.entered.connect(self.onListViewEntered)

    def updateDirModel(self, path):
        info = QFileInfo(path)
        if info.isDir():
            self.m_pDirModel.refresh(self.m_pDirModel.index(path))
            self.listView.setRootIndex(self.m_pDirModel.index(path))

    def adjustMenuSize(self):
        pass

    def setLoading(self):
        self._model.clear()
        item = QStandardItem("Loading...")
        item.setData("Loading...", Qt.ToolTipRole)
        self._model.appendRow(item)

        self.setFixedSize(100, 25)
        self._menu.setFixedSize(100, 25)

    def setMenuData(self,
                    childClsNameList: typing.List[str],
                    childObjNameList: typing.List[str],
                    childWidgetIdList: typing.List[int]):
        self._model.clear()

        maxWidth = 0
        totalHeight = 0

        for clsName, objName, widgetId in zip(childClsNameList, childObjNameList, childWidgetIdList):
            item = QStandardItem(f"{clsName}{objName and f'#{objName}'}")
            item.setData(f"{clsName}{objName and f'#{objName}'} (id {widgetId})", Qt.ToolTipRole)
            item.setData(widgetId, Qt.UserRole + 1)
            self._model.appendRow(item)

            totalHeight += self.listView.sizeHintForRow(self._model.rowCount() - 1)
            maxWidth = max(maxWidth, QtGui.QFontMetrics(self.listView.font()).width(item.text()))

        targetWidth, targetHeight = maxWidth, min(totalHeight, 300)
        self.setFixedSize(targetWidth + 20, targetHeight + 5)
        self._menu.setFixedSize(targetWidth + 25, targetHeight + 10)

    def onListViewClicked(self, index):
        widgetId = index.data(Qt.UserRole + 1)
        if widgetId is None:
            widgetId = -1  # loading项的id为-1, 由外部处理点击事件(需要隐藏的)
        self.sigClickChild.emit(str(widgetId))

    def onListViewEntered(self, index):
        widgetId = index.data(Qt.UserRole + 1)
        if widgetId is None:
            widgetId = -1  # loading项的id为-1, 由外部处理点击事件(需要隐藏的)
        self.sigHoverChild.emit(str(widgetId))
