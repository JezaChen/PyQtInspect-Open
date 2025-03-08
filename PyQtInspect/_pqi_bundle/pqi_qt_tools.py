# PQI Tools for Qt

from PyQtInspect._pqi_bundle.pqi_monkey_qt_props import (
    _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR, _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR, _PQI_STACK_WHEN_CREATED_ATTR
)
from PyQtInspect._pqi_bundle.pqi_path_helper import find_pqi_module_path, is_relative_to


def _filter_trace_stack(traceStacks):
    filteredStacks = []
    from PyQtInspect.pqi import SetupHolder
    stackMaxDepth = SetupHolder.setup["stack-max-depth"]
    showPqiStack = SetupHolder.setup["show-pqi-stack"]
    pqi_module_path = find_pqi_module_path()
    stacks = traceStacks[2:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[2:]
    for filename, lineno, func_name in stacks:
        if not showPqiStack and is_relative_to(filename, pqi_module_path):
            break
        filteredStacks.append(
            {
                'filename': filename,
                'lineno': lineno,
                'function': func_name,
            }
        )
    return filteredStacks


# ==== TODO ====
# 这个最好写个单元测试代码
def find_name_in_mro(cls, name, default):
    """ Emulate _PyType_Lookup() in Objects/typeobject.c """
    for base in cls.__mro__:
        if name in vars(base):
            yield base, vars(base)[name]
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
        # Sometimes, ``obj`` has a variable with the same name as the method
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


def get_create_stack(widget):
    return _filter_trace_stack(getattr(widget, _PQI_STACK_WHEN_CREATED_ATTR, []))


def import_Qt(qt_type: str):
    """
    Import Qt libraries by type.

    :param qt_type: The Qt type to import, either 'pyqt5' or 'pyside2'.
    """
    if qt_type == 'pyqt5':
        import PyQt5 as QtLib
    elif qt_type == 'pyqt6':
        import PyQt6 as QtLib
    elif qt_type == 'pyside2':
        import PySide2 as QtLib
    elif qt_type == 'pyside6':
        import PySide6 as QtLib
    else:
        raise ValueError(f'Unsupported Qt type: {qt_type}')

    return QtLib


def import_wrap_module(qt_type: str):
    """
    Import the wrap module by Qt type.

    :param qt_type: The Qt type to import, either 'pyqt5' or 'pyside2'.
    """
    if qt_type == 'pyqt5':
        from PyQt5 import sip as wrap_module
        wrap_module._pqi_is_valid = lambda x: wrap_module.isdeleted(x) == False
    elif qt_type == 'pyqt6':
        from PyQt6 import sip as wrap_module
        wrap_module._pqi_is_valid = lambda x: wrap_module.isdeleted(x) == False
    elif qt_type == 'pyside2':
        import shiboken2 as wrap_module
        wrap_module._pqi_is_valid = wrap_module.isValid
    elif qt_type == 'pyside6':
        import shiboken6 as wrap_module
        wrap_module._pqi_is_valid = wrap_module.isValid
    else:
        raise ValueError(f'Unsupported Qt type: {qt_type}')

    return wrap_module


def _send_custom_event(target_widget, key: str, val):
    from PyQtInspect.pqi import SetupHolder

    QtCore = import_Qt(SetupHolder.setup['qt-support']).QtCore
    EventEnum = QtCore.QEvent.Type if hasattr(QtCore.QEvent, 'Type') else QtCore.QEvent
    event = QtCore.QEvent(EventEnum.User)
    setattr(event, key, val)
    QtCore.QCoreApplication.postEvent(target_widget, event)


def set_widget_highlight(widget, highlight: bool):
    """
    Set the highlight on a widget.

    :note: Use custom events to avoid program crashes due to cross-threaded calls

    :param widget: The widget to set the highlight on.

    :param highlight: A boolean indicating whether to highlight the widget or not.
    """
    _send_custom_event(widget, _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR, highlight)


def exec_code_in_widget(widget, code: str):
    _send_custom_event(widget, _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR, code)


def is_wrapped_pointer_valid(ptr):
    """
    Check if a wrapped pointer is valid.

    :param ptr: The pointer to check.
    """
    from PyQtInspect.pqi import SetupHolder
    return import_wrap_module(SetupHolder.setup['qt-support'])._pqi_is_valid(ptr)
