# PQI Tools for Qt


def get_widget_class_name(widget):
    return widget.__class__.__name__


def get_widget_object_name(widget):
    return widget.objectName()


def get_widget_size(widget):
    return widget.size().width(), widget.size().height()


def get_widget_pos(widget):
    return widget.pos().x(), widget.pos().y()


def get_parent_info(widget):
    while True:
        try:
            parent = widget.parent()
        except:
            break

        if parent is None:
            break
        widget = parent
        yield get_widget_class_name(widget), id(widget), get_widget_object_name(widget)


def get_stylesheet(widget):
    return widget.styleSheet()


def get_children_info(widget):
    for child in widget.children():
        yield get_widget_class_name(child), id(child), get_widget_object_name(child)


def import_Qt(qt_type: str):
    """
    Import Qt libraries by type.

    :param qt_type: The Qt type to import, either 'pyqt5' or 'pyside2'.
    """
    if qt_type == 'pyqt5':
        import PyQt5 as QtLib
    elif qt_type == 'pyside2':
        import PySide2 as QtLib
    else:
        raise ValueError(f'Unsupported Qt type: {qt_type}')

    return QtLib


def _send_custom_event(target_widget, key: str, val):
    from PyQtInspect.pqi import SetupHolder

    QtCore = import_Qt(SetupHolder.setup['qt-support']).QtCore
    event = QtCore.QEvent(QtCore.QEvent.User)
    setattr(event, key, val)
    QtCore.QCoreApplication.postEvent(target_widget, event)


def set_widget_highlight(widget, highlight: bool):
    """
    Set the highlight on a widget.

    :note: Use custom events to avoid program crashes due to cross-threaded calls

    :param widget: The widget to set the highlight on.

    :param highlight: A boolean indicating whether to highlight the widget or not.
    """
    _send_custom_event(widget, '_pqi_is_highlight', highlight)


def exec_code_in_widget(widget, code: str):
    _send_custom_event(widget, '_pqi_exec_code', code)
