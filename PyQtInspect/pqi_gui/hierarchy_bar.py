# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/10/9 19:20
# Description: 
# ==============================================
import typing

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QPushButton, QMenu, QWidgetAction, QApplication, QAction
from PyQt5.QtGui import QPixmap, QPainter, QFontMetrics, QColor, QBrush, QFont, QIcon
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint

ARROW_WIDTH = 17
SPACE_WIDTH = 8
ITEM_HEIGHT = 20


def clearLayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


class HierarchyItem(QPushButton):
    arrowClicked = pyqtSignal()

    def __init__(self, parent, clsName: str, objName: str, widgetId: int, barWidget: 'HierarchyBar'):
        super().__init__(parent)
        self._barWidget = barWidget
        # === for paint === #
        self._pressed = False
        self._pressedText = False
        self._lastPressedText = False
        self._moveFlag = False
        self._menuShowed = False

        # === data === #
        self._clsName = clsName
        self._objName = objName
        self._widgetId = widgetId

        self._text = f"{clsName}#{objName}"

        self.m_font = parent.font()
        if self._text == "":
            self._textWidth = 0
            self.setFixedSize(ARROW_WIDTH, 21)
        else:
            fm = QFontMetrics(self.m_font)
            self._textWidth = fm.width(self._text) + SPACE_WIDTH
            self.setFixedSize(self._textWidth + ARROW_WIDTH, 21)

        self.m_normalIcon = QPixmap(":/icons/arrow_right.png")
        self.m_checkedIcon = QPixmap(":/icons/arrow_down.png")

        self.setMouseTracking(True)
        self.setCheckable(True)
        self.setToolTip(f"{clsName}#{objName} (id {widgetId})")

        self.arrowClicked.connect(self._onArrowClicked)

    def getWidgetId(self) -> int:
        return self._widgetId

    def paintEvent(self, event):
        painter = QPainter(self)

        if self._moveFlag:
            painter.setPen(QColor(205, 232, 254))
            painter.fillRect(QRect(0, 0, self._textWidth + ARROW_WIDTH, ITEM_HEIGHT), QBrush(QColor(229, 243, 254)))
            painter.drawRect(QRect(0, 0, self._textWidth, ITEM_HEIGHT))
            painter.drawRect(QRect(self._textWidth, 0, ARROW_WIDTH, ITEM_HEIGHT))

        if self._pressed or self.isChecked():
            painter.setPen(QColor(153, 209, 255))
            painter.fillRect(QRect(0, 0, self._textWidth + ARROW_WIDTH, ITEM_HEIGHT), QBrush(QColor(204, 232, 255)))
            painter.drawRect(QRect(0, 0, self._textWidth, ITEM_HEIGHT))
            painter.drawRect(QRect(self._textWidth, 0, ARROW_WIDTH, ITEM_HEIGHT))

            painter.setPen(QColor(0, 0, 0))
            painter.setFont(self.m_font)
            painter.drawText(QRect(1, 1, self._textWidth, ITEM_HEIGHT), Qt.AlignCenter, self._text)

        else:
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(self.m_font)
            painter.drawText(QRect(0, 0, self._textWidth, ITEM_HEIGHT), Qt.AlignCenter, self._text)

        # 绘制箭头
        if self._menuShowed:
            painter.drawPixmap(QRect(self._textWidth, 0, ARROW_WIDTH, ITEM_HEIGHT), self.m_checkedIcon,
                               self.m_checkedIcon.rect())
        else:
            painter.drawPixmap(QRect(self._textWidth, 0, ARROW_WIDTH, ITEM_HEIGHT), self.m_normalIcon,
                               self.m_normalIcon.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.hitButton(event.pos()):
            self._pressed = True
            if QRect(0, 0, self._textWidth, ITEM_HEIGHT).contains(event.pos()):
                self._pressedText = True
                self._lastPressedText = True
            elif QRect(self._textWidth, 0, ARROW_WIDTH, ITEM_HEIGHT).contains(event.pos()):
                self._lastPressedText = False
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._pressed:
                if self._pressedText:
                    self.setChecked(True)
                else:
                    self.arrowClicked.emit()

            self._pressedText = False
            self._pressed = False
            self.update()

    def enterEvent(self, event):
        self._moveFlag = True
        self.update()
        self._barWidget.notifyItemHovered(self)  # 向上层通知鼠标进入

    def leaveEvent(self, event):
        self._moveFlag = False
        self.update()

    def menuAboutToHide(self):
        self._menuShowed = False
        self._moveFlag = False
        self._pressed = False
        self.update()

    def _onArrowClicked(self):
        self.update()
        globalPoint = self.mapToGlobal(QPoint(0, 0))
        globalPoint.setX(globalPoint.x() + ARROW_WIDTH + self._textWidth - 30)
        globalPoint.setY(globalPoint.y() + ITEM_HEIGHT)
        self._menuShowed = True
        self._barWidget.notifyShowMenu(self, globalPoint.x(), globalPoint.y())


HIERARCHY_BAR_STYLE_SHEET = """
QScrollArea { background: transparent; border:none;}
"""


class HierarchyBarScrollArea(QtWidgets.QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(21)
        self.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("hierarchyBarScrollArea")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        # 响应鼠标滚轮事件, 倒置事件的坐标系, 使得横向滚动条也能滚动
        newEvent = QtGui.QWheelEvent(event.pos(), event.globalPos(),
                                     QtCore.QPoint(event.pixelDelta().y(), event.pixelDelta().x()),
                                     QtCore.QPoint(event.angleDelta().y(), event.angleDelta().x()),
                                     event.buttons(), event.modifiers(), event.phase(), event.inverted())
        QtWidgets.QApplication.sendEvent(self.horizontalScrollBar(), newEvent)


class HierarchyBar(QtWidgets.QWidget):
    sigAncestorItemChanged = pyqtSignal(str)  # widgetId
    sigAncestorItemHovered = pyqtSignal(str)  # widgetId

    sigReqChildWidgetsInfo = pyqtSignal(str)  # widgetId
    sigChildMenuActionTriggered = pyqtSignal(str)  # widgetId
    sigChildMenuActionHovered = pyqtSignal(str)  # widgetId

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(21)

        self._buttonGroup = QtWidgets.QButtonGroup(self)
        self._buttonGroup.setExclusive(True)
        self._buttonGroup.buttonToggled.connect(self._onButtonToggled)  # 不能用clicked, 因为鼠标事件被拦截

        self._mainLayout = QtWidgets.QHBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(2)

        self._goLeftButton = QtWidgets.QPushButton(self)
        self._goLeftButton.setFixedSize(16, 21)
        self._goLeftButton.setIcon(QIcon(":/icons/go_left.png"))
        self._goLeftButton.setObjectName("goLeftButton")
        self._goLeftButton.clicked.connect(self._onGoLeftButtonClicked)

        self._mainLayout.addWidget(self._goLeftButton)

        self._container = QtWidgets.QWidget(self)
        self._container.setObjectName("hierarchyBarContainer")

        self._containerLayout = QtWidgets.QHBoxLayout(self._container)
        self._containerLayout.setContentsMargins(0, 0, 0, 0)
        self._containerLayout.setSpacing(0)

        self._scrollArea = HierarchyBarScrollArea(self)
        self._scrollArea.setWidget(self._container)
        self._scrollArea.horizontalScrollBar().rangeChanged.connect(self._handleScrollButtonVisible)
        self._scrollArea.horizontalScrollBar().rangeChanged.connect(self._scrollToEndWhenRangeChanged)

        self._mainLayout.addWidget(self._scrollArea)

        self._goRightButton = QtWidgets.QPushButton(self)
        self._goRightButton.setFixedSize(16, 21)
        self._goRightButton.setIcon(QIcon(":/icons/go_right.png"))
        self._goRightButton.setObjectName("goRightButton")
        self._goRightButton.clicked.connect(self._onGoRightButtonClicked)

        self._mainLayout.addWidget(self._goRightButton)

        self._menu = QMenu(self)
        self._menu.setWindowFlags(Qt.Popup)
        self._menu.addAction("aaa", lambda: print("aaa"))
        self._menu.aboutToHide.connect(self._menuAboutToHide)

        self._curItemWithMenuShowed: typing.Optional[HierarchyItem] = None
        self._curCheckedItem: typing.Optional[HierarchyItem] = None
        self._widgetIdOfCurrMenu = -1
        self._lastHoveredChildItemWidgetId = -1

        self.setStyleSheet(HIERARCHY_BAR_STYLE_SHEET)
        self._handleScrollButtonVisible()

    def _onGoLeftButtonClicked(self):
        self._scrollArea.horizontalScrollBar().setValue(
            self._scrollArea.horizontalScrollBar().value() - self._scrollArea.width() // 2
        )

    def _onGoRightButtonClicked(self):
        self._scrollArea.horizontalScrollBar().setValue(
            self._scrollArea.horizontalScrollBar().value() + self._scrollArea.width() // 2
        )

    def _handleScrollButtonVisible(self):
        if self._container.width() > self._scrollArea.width():
            self._goLeftButton.show()
            self._goRightButton.show()
        else:
            self._goLeftButton.hide()
            self._goRightButton.hide()

    def setData(self,
                ancestorClsNameList: typing.List[str],
                ancestorObjNameList: typing.List[str],
                ancestorWidgetIdList: typing.List[int]):
        # clear old data
        clearLayout(self._containerLayout)
        self._buttonGroup.buttons().clear()
        self._curItemWithMenuShowed = None
        self._curCheckedItem = None

        for clsName, objName, widgetId in zip(ancestorClsNameList, ancestorObjNameList, ancestorWidgetIdList):
            item = HierarchyItem(self, clsName, objName, widgetId, self)
            self._buttonGroup.addButton(item)
            self._containerLayout.addWidget(item)
        self._containerLayout.addStretch()

        if self._buttonGroup.buttons():  # not empty, set last item checked by default
            lastItem = self._buttonGroup.buttons()[-1]
            # 之所以在这里设置, 是因为避免数据变更后emit sigAncestorItemChanged信号
            # 导致重复获取数据
            self._curCheckedItem = lastItem
            lastItem.setChecked(True)

        self.update()

    def _scrollToEndWhenRangeChanged(self):
        self._scrollArea.horizontalScrollBar().setValue(self._scrollArea.horizontalScrollBar().maximum())

    def notifyShowMenu(self, itemWidget: HierarchyItem, posX: int, posY: int):
        self._curItemWithMenuShowed = itemWidget

        self._menu.move(posX, posY)
        if self._widgetIdOfCurrMenu != itemWidget.getWidgetId():
            # 脏数据
            self._menu.clear()
            self._menu.addAction("loading...")
            self._menu.adjustSize()
            self.sigReqChildWidgetsInfo.emit(str(itemWidget.getWidgetId()))
        self._menu.show()

    def notifyHideMenu(self, itemWidget: HierarchyItem):
        if self._curItemWithMenuShowed == itemWidget:
            self._menu.hide()
            self._curItemWithMenuShowed = None

    def _menuAboutToHide(self):
        if self._curItemWithMenuShowed:
            self._curItemWithMenuShowed.menuAboutToHide()

    def notifyItemHovered(self, itemWidget: HierarchyItem):
        self.sigAncestorItemHovered.emit(str(itemWidget.getWidgetId()))

    def _onButtonToggled(self, btn, checked):
        if checked and btn != self._curCheckedItem:
            self._curCheckedItem = btn
            self.sigAncestorItemChanged.emit(str(btn.getWidgetId()))

    def setMenuData(self,
                    widgetId: int,
                    childClsNameList: typing.List[str],
                    childObjNameList: typing.List[str],
                    childWidgetIdList: typing.List[int]):
        if self._curItemWithMenuShowed is None or widgetId != self._curItemWithMenuShowed.getWidgetId():
            # 脏数据
            return

        self._widgetIdOfCurrMenu = widgetId

        self._menu.clear()
        for clsName, objName, widgetId in zip(childClsNameList, childObjNameList, childWidgetIdList):
            action = QAction(self._menu)
            action.setText(f"{clsName}#{objName}")
            action.setToolTip(f"{clsName}#{objName} (id {widgetId})")

            # 注意这里的lambda函数的参数传递方式
            action.triggered.connect(lambda _, _wgtId=widgetId: self.sigChildMenuActionTriggered.emit(str(_wgtId)))
            action.hovered.connect(lambda _wgtId=widgetId: self._handleChildMenuActionHovered(_wgtId))

            self._menu.addAction(action)

    def _handleChildMenuActionHovered(self, widgetId: int):
        if self._lastHoveredChildItemWidgetId == widgetId:
            return

        self._lastHoveredChildItemWidgetId = widgetId
        self.sigChildMenuActionHovered.emit(str(widgetId))


class TestWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(500, 500)
        self._widget = HierarchyBar(self)
        # self._giftInfoWidget.setOrder(1)
        self.setCentralWidget(self._widget)
        self._widget.setData(
            ["QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget"],
            ["testWidget", "testWidget", "testWidget", "testWidget", "testWidget", "testWidget", "testWidget",
             "testWidget", "testWidget"],
            [1, 2, 3, 4, 5, 6, 7, 8, 9]
        )
        self._widget.sigAncestorItemHovered.connect(lambda widgetId: print(f"hovered {widgetId}"))
        self._widget.sigAncestorItemChanged.connect(lambda widgetId: print(f"changed {widgetId}"))
        self._widget.sigChildMenuActionTriggered.connect(lambda widgetId: print(f"triggered {widgetId}"))
        self._widget.sigChildMenuActionHovered.connect(lambda widgetId: print(f"hovered {widgetId}"))

        self._setMenuDataBtn = QtWidgets.QPushButton(self)
        self._setMenuDataBtn.setText("setMenuData")
        self._setMenuDataBtn.move(100, 100)
        self._setMenuDataBtn.clicked.connect(self._onSetMenuDataBtnClicked)

    def _onSetMenuDataBtnClicked(self):
        self._widget.setMenuData(9,
                                 ["QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget", "QWidget"],
                                 ["testWidget", "testWidget", "testWidget", "testWidget", "testWidget", "testWidget",
                                  "testWidget"],
                                 [1, 2, 3, 4, 5, 6, 7])


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    import PyQtInspect.pqi_gui._pqi_res.resources

    parentWin = TestWindow(None)
    parentWin.show()

    sys.exit(app.exec_())
