from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger
from PyQtInspect._pqi_bundle.monkey_qt.metadata import _PQI_INSPECTED_PROP_NAME, _PQI_WIDGET_INSPECTED_MARK

__all__ = [
    "is_inspect_enabled",
    "is_widget_patched",
    "mark_widget_patched",
    "is_widget_inspected",
    "mark_widget_inspected",
    "clear_widget_inspected_mark",
]


def is_inspect_enabled():
    debugger = get_global_debugger()
    return debugger.inspect_enabled


# =========================
# PATCHED WIDGET MARKING
# =========================
def is_widget_patched(obj) -> bool:
    return bool(obj.property(_PQI_INSPECTED_PROP_NAME))


def mark_widget_patched(widget):
    widget.setProperty(_PQI_INSPECTED_PROP_NAME, True)


# =========================
# WIDGET INSPECTED MARKING
# =========================

def is_widget_inspected(widget) -> bool:
    return hasattr(widget, _PQI_WIDGET_INSPECTED_MARK)


def mark_widget_inspected(widget):
    setattr(widget, _PQI_WIDGET_INSPECTED_MARK, True)


def clear_widget_inspected_mark(widget):
    if hasattr(widget, _PQI_WIDGET_INSPECTED_MARK):
        delattr(widget, _PQI_WIDGET_INSPECTED_MARK)
