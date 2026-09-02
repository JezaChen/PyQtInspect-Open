from PyQtInspect._pqi_bundle.monkey_qt.metadata import _PQI_HIGHLIGHT_FG_NAME
from PyQtInspect._pqi_bundle.monkey_qt.shared_api import QObjectInspectAPI, QtModuleAPI
from PyQtInspect._pqi_bundle.monkey_qt.widget_utils import get_widget_size
from PyQtInspect._pqi_bundle.pqi_contants import DEFAULT_HIGHLIGHT_COLOR, get_global_debugger

__all__ = [
    "QtWidgetHighlighter",
]


def _get_highlight_stylesheet() -> str:
    color_str = DEFAULT_HIGHLIGHT_COLOR
    debugger = get_global_debugger()
    if debugger is not None:
        color_str = debugger.highlight_color
    try:
        r, g, b, a = (int(x) for x in color_str.split(','))
        r, g, b, a = (max(0, min(255, v)) for v in (r, g, b, a))
        color_css = f"rgba({r},{g},{b},{a})"
    except (ValueError, AttributeError):
        color_css = "rgba(255,0,0,51)"
    return f"background: transparent; background-color: {color_css};"


def _createHighlightFg(parent):
    # Instantiate with __new__ first, then invoke the original __init__.
    QtWidgets = QtModuleAPI.instance().QtWidgets
    QtCore = QtModuleAPI.instance().QtCore

    assert hasattr(QtWidgets.QWidget, "_original_QWidget_init"), \
        "QtWidgets.QWidget._original_QWidget_init is not set. Please ensure that the monkey patching is applied before using QtWidgetHighlighter."

    widget = QtWidgets.QWidget.__new__(QtWidgets.QWidget)
    QtWidgets.QWidget._original_QWidget_init(widget, parent)
    widget.setFixedSize(*get_widget_size(parent))
    # Prevent it from responding to mouse events.
    widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setObjectName(_PQI_HIGHLIGHT_FG_NAME)
    # Fix for #63: Prevent repeated icon artifacts when highlighting widgets with background-image qss.
    # -------------------------------------------------------------------------------------------------
    # Use `background: transparent` shorthand to reset all inherited background properties
    #   (e.g. background-image, background-color) from parent stylesheets, then apply our highlight color.
    # -------------------------------------------------------------------------------------------------
    # Note: `background-image: none` is ineffective here, and reversing the declaration order
    #   will cause "background-color" to be overridden by the shorthand.
    # -------------------------------------------------------------------------------------------------
    widget.setStyleSheet(_get_highlight_stylesheet())
    return widget


class QtWidgetHighlighter:
    def __init__(self):
        QtWidgets = QtModuleAPI.instance().QtWidgets

        self.last_highlighted_widget = None
        # for some widgets like QSplitter, we should not highlight them, or they will change their size
        self.widget_class_to_ignore = (
            QtWidgets.QSplitter,
        )

    def _is_ignored(self, widget):
        return any(isinstance(widget, class_) for class_ in self.widget_class_to_ignore)

    def unhighlight_last(self):
        if self.last_highlighted_widget is not None and not QObjectInspectAPI.instance().isdeleted(
            self.last_highlighted_widget
        ):
            self.last_highlighted_widget.hide()
        self.last_highlighted_widget = None

    def highlight(self, widget):
        if self._is_ignored(widget):
            return

        if not hasattr(widget, _PQI_HIGHLIGHT_FG_NAME):
            setattr(widget, _PQI_HIGHLIGHT_FG_NAME, _createHighlightFg(widget))

        fg = getattr(widget, _PQI_HIGHLIGHT_FG_NAME)
        fg.setFixedSize(*get_widget_size(widget))
        fg.setStyleSheet(_get_highlight_stylesheet())
        self.unhighlight_last()
        fg.show()
        self.last_highlighted_widget = fg

    def unhighlight(self, widget):
        fg = getattr(widget, _PQI_HIGHLIGHT_FG_NAME, None)
        if fg is not None:
            fg.hide()
            if self.last_highlighted_widget is fg:
                self.last_highlighted_widget = None
