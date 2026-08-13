from typing import NamedTuple, Tuple

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.monkey_qt.metadata import SuppressPatchMark
from PyQtInspect._pqi_bundle.monkey_qt.widget_utils import (
    get_widget_class_name,
    get_widget_object_name,
    get_widget_size,
    get_widget_pos,
    get_widget_size_hint,
    get_widget_window_pos,
    get_widget_visual_rect,
)

__all__ = [
    "DetailedInspectTooltipManager",
]

_CARD_OBJECT_NAME = "_pqiPopupCard"
_TITLE_LABEL_OBJECT_NAME = "_pqiPopupTitle"
_NAME_LABEL_OBJECT_NAME = "_pqiPopupPropertyName"
_VALUE_LABEL_OBJECT_NAME = "_pqiPopupPropertyValue"

_STYLE_SHEET = f"""
QFrame#{_CARD_OBJECT_NAME} {{
    background: white;
    border: 1px solid #d8d8d8;
    border-radius: 6px;
}}

QLabel {{
    color: #5f6368;
    font-size: 14px;
    background: transparent;
}}

QLabel#{_NAME_LABEL_OBJECT_NAME} {{
    color: #6b6b6b;
}}

QLabel#{_VALUE_LABEL_OBJECT_NAME} {{
    color: #4a4a4a;
}}

QLabel#{_TITLE_LABEL_OBJECT_NAME} {{
    color: #512da8;
    font-size: 15px;
    font-weight: 600;
}}
"""


def _make_breakable(text: str) -> str:
    # Insert zero-width spaces between characters so QLabel can wrap the text.
    # https://stackoverflow.com/questions/12262123/how-to-customize-qlabel-word-wrap-mode
    return "\u200b".join(text)


class _WidgetInfo(NamedTuple):
    class_name: str
    object_name: str

    size: Tuple[int, int]
    size_hint: Tuple[int, int]
    rel_pos: Tuple[int, int]
    window_pos: Tuple[int, int]


class DetailedInspectTooltipManager:
    def __init__(_self, qt_module):
        QtWidgets = qt_module.QtWidgets
        QtGui = qt_module.QtGui
        QtCore = qt_module.QtCore

        Qt = QtCore.Qt
        QPoint = QtCore.QPoint

        QColor = QtGui.QColor

        QApplication = QtWidgets.QApplication
        QWidget = QtWidgets.QWidget
        QFrame = QtWidgets.QFrame
        QLabel = QtWidgets.QLabel
        QVBoxLayout = QtWidgets.QVBoxLayout
        QGridLayout = QtWidgets.QGridLayout
        QGraphicsDropShadowEffect = QtWidgets.QGraphicsDropShadowEffect
        QSizePolicy = QtWidgets.QSizePolicy

        _self._QWidget_cls = QWidget

        class DetailedInspectTooltip(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)

                self.setWindowFlags(
                    Qt.WindowType.Tool
                    | Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.WindowStaysOnTopHint
                )
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

                self._initUI()

            def _initUI(self):
                # Leave some space around the outer layout for the drop shadow.
                self.outerLayout = QVBoxLayout(self)
                self.outerLayout.setContentsMargins(10, 10, 10, 10)

                self.card = QFrame()
                self.card.setObjectName(_CARD_OBJECT_NAME)
                self.card.setStyleSheet(_STYLE_SHEET)

                shadow = QGraphicsDropShadowEffect(self.card)
                shadow.setBlurRadius(18)
                shadow.setOffset(0, 3)
                shadow.setColor(QColor(0, 0, 0, 90))
                self.card.setGraphicsEffect(shadow)

                self.outerLayout.addWidget(self.card)

                self.mainLayout = QVBoxLayout(self.card)
                self.mainLayout.setContentsMargins(12, 10, 12, 12)
                self.mainLayout.setSpacing(7)

                # ----------------------------
                # Title Area: Object Name + Size
                # ----------------------------
                self.titleLabel = QLabel()
                self.titleLabel.setObjectName(_TITLE_LABEL_OBJECT_NAME)
                self.titleLabel.setWordWrap(True)
                self.titleLabel.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )

                self.mainLayout.addWidget(self.titleLabel)

                # ----------------------------
                # Properties Area
                # ----------------------------
                self.propertyGrid = QGridLayout()
                self.propertyGrid.setHorizontalSpacing(16)
                self.propertyGrid.setVerticalSpacing(5)
                self.propertyGrid.setColumnStretch(1, 1)

                self.mainLayout.addLayout(self.propertyGrid)
                self.setFixedWidth(300)

            def addProperty(self, name, value):
                name_label = QLabel(self.card)
                name_label.setText(name)
                name_label.setObjectName(_NAME_LABEL_OBJECT_NAME)
                name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                value_label = QLabel(self.card)
                value_label.setText(value)
                value_label.setObjectName(_VALUE_LABEL_OBJECT_NAME)
                value_label.setWordWrap(True)
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

                cnt = self.propertyGrid.count() // 2

                self.propertyGrid.addWidget(name_label, cnt, 0)
                self.propertyGrid.addWidget(value_label, cnt, 1)

                # Important:
                # Newly added widgets may not become visible immediately when the
                # popup is already shown, which can result in an incorrect height.
                # Show them explicitly so the layout includes them in its height calculation.
                name_label.show()
                value_label.show()

            def fitHeightToWidth(self):
                """"""
                # The layout contents may have just changed and need to be invalidated.
                self.propertyGrid.invalidate()
                self.mainLayout.invalidate()
                self.outerLayout.invalidate()

                self.propertyGrid.activate()
                self.mainLayout.activate()
                self.outerLayout.activate()

                # Important:
                # Calculate the height using the popup's actual fixed width so that
                # word-wrapped labels are measured at their final display width.
                # Relying on unconstrained size hints can overestimate the required
                # height.
                height = self.outerLayout.heightForWidth(self.width())

                if height >= 0:
                    self.setFixedHeight(height)
                else:
                    self.adjustSize()

                self.card.repaint()

            def clearProperties(self):
                while True:
                    item = self.propertyGrid.takeAt(0)
                    if item is None:
                        break
                    widget = item.widget()
                    if widget is not None:
                        # Do not call setParent(None) here; the queued show event
                        # would then display the widget as a top-level window.
                        # https://chatgpt.com/s/t_6a7817ffaa488191b24a00b376d8483f
                        # widget.setParent(None)
                        widget.deleteLater()

            def setInfo(self, info: _WidgetInfo):
                with SuppressPatchMark.marked(
                    _self._QWidget_cls
                ):
                    self.titleLabel.setText(_make_breakable(
                        info.class_name
                        + ("#" + info.object_name if info.object_name != "" else "")
                    ))
                    self.clearProperties()

                    self.addProperty("Size", f"{info.size[0]} × {info.size[1]}")
                    self.addProperty("SizeHint", f"{info.size_hint[0]} × {info.size_hint[1]}")
                    self.addProperty("Position (relative)", f"{info.rel_pos[0]}, {info.rel_pos[1]}")
                    self.addProperty("Position (in window)", f"{info.window_pos[0]}, {info.window_pos[1]}")

            def showNear(self, widget):
                widget_info = _WidgetInfo(
                    class_name=get_widget_class_name(widget),
                    object_name=get_widget_object_name(widget),
                    size=get_widget_size(widget),
                    rel_pos=get_widget_pos(widget),
                    window_pos=get_widget_window_pos(widget),
                    size_hint=get_widget_size_hint(widget),
                )
                self.setInfo(widget_info)
                self.fitHeightToWidth()

                def findScreen(_pos):
                    _screen = QApplication.screenAt(_pos)
                    if _screen:
                        return _screen
                    # Try again using the tooltip's expected bottom-right corner.
                    _screen = QApplication.screenAt(
                        QPoint(_pos.x() + self.width(), _pos.y() + self.height())
                    )
                    return _screen

                # Keep the tooltip within the current screen.
                visual_rect = get_widget_visual_rect(widget)
                if visual_rect is None:
                    pqi_log.warning("Failed to get visual rect for widget: %s. Tooltip will not be shown.", widget)
                    self.hide()
                    return

                pqi_log.debug("Showing tooltip for widget: %s at visual rect: %s", widget, visual_rect)
                screen = findScreen(QPoint(visual_rect.x, visual_rect.y))
                x = visual_rect.x
                # Place the tooltip below the target widget by default.
                y = visual_rect.y + visual_rect.height + 4

                if screen:
                    # Clamp the tooltip to the screen's available geometry.
                    rect = screen.availableGeometry()
                    available_right = rect.x() + rect.width()
                    available_bottom = rect.y() + rect.height()

                    if x + self.width() > available_right:
                        x = available_right - self.width()

                    if y + self.height() > available_bottom:
                        # Place the tooltip above the target widget if there is not enough space below.
                        y = visual_rect.y - self.height() - 4

                    x = max(rect.left(), x)
                    y = max(rect.top(), y)

                self.move(x, y)
                self.show()
                self.raise_()

        _self._tooltipCls = DetailedInspectTooltip

    def show_tooltip(_self, target_widget):
        # Create the popup lazily on first use.
        # Creating it in DetailedInspectTooltipManager.__init__ may occur before Qt's event loop starts.
        if not hasattr(_self, "_tooltip"):
            with SuppressPatchMark.marked(
                _self._QWidget_cls  # patch QWidget is enough, because all the other widgets are subclasses of QWidget
            ):
                _self._tooltip = _self._tooltipCls()
        _self._tooltip.showNear(target_widget)

    def hide_tooltip(_self):
        if hasattr(_self, "_tooltip"):
            _self._tooltip.hide()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout


    class Demo(QWidget):
        def runPopup(self):
            self.popup_manager.show_tooltip(self.button)

        def __init__(self):
            super().__init__()

            self.resize(800, 500)

            layout = QVBoxLayout(self)

            self.button = QPushButton("Show Inspector Popup")
            self.button.setFixedSize(200, 40)

            layout.addWidget(self.button)
            layout.addStretch()

            self.popup_manager = DetailedInspectTooltipManager(qt_module=__import__("PyQt5"))

            self.button.clicked.connect(self.runPopup)


    app = QApplication(sys.argv)

    window = Demo()
    window.show()

    sys.exit(app.exec_())
