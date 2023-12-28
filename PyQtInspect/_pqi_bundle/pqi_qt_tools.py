# PQI Tools for Qt

# ==== TODO ====
# 这个最好写个单元测试代码
def find_name_in_mro(cls, name, default):
    """ Emulate _PyType_Lookup() in Objects/typeobject.c """
    for base in cls.__mro__:
        if hasattr(base, name):
            yield base, getattr(base, name)
    yield default, default


def find_callable_var(obj, name):
    null = object()
    for cls, cls_var in find_name_in_mro(type(obj), name, null):
        if callable(cls_var):
            return cls_var
    raise AttributeError(name)


def find_method_by_name_and_call(obj, name, *args, **kwargs):
    if callable(getattr(obj, name)):
        return getattr(obj, name)(*args, **kwargs)
    else:
        return find_callable_var(obj, name)(obj, *args, **kwargs)


def get_widget_class_name(widget):
    return widget.__class__.__name__


def get_widget_object_name(widget):
    return find_method_by_name_and_call(widget, 'objectName')


def get_widget_size(widget):
    size = find_method_by_name_and_call(widget, 'size')
    return size.width(), size.height()


def get_widget_pos(widget):
    pos = find_method_by_name_and_call(widget, 'pos')
    return pos.x(), pos.y()


def get_widget_parent(widget):
    return find_method_by_name_and_call(widget, 'parent')


def get_parent_info(widget):
    while True:
        try:
            parent = get_widget_parent(widget)
        except:
            break

        if parent is None:
            break
        widget = parent
        yield get_widget_class_name(widget), id(widget), get_widget_object_name(widget)


def get_stylesheet(widget):
    return find_method_by_name_and_call(widget, 'styleSheet')


def get_children_info(widget):
    children = find_method_by_name_and_call(widget, 'children')
    for child in children:
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
