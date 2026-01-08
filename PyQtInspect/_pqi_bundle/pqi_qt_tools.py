# PQI Tools for Qt
import typing

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_comm_constants import TreeViewKeys
from PyQtInspect._pqi_bundle.pqi_monkey_qt_props import (
    _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR, _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR, _PQI_STACK_WHEN_CREATED_ATTR,
    _PQI_HIGHLIGHT_FG_NAME,
)
from PyQtInspect._pqi_bundle.pqi_path_helper import find_pqi_module_path, is_relative_to


def _filter_trace_stack(traceStacks):
    filteredStacks = []
    from PyQtInspect.pqi import SetupHolder
    stackMaxDepth = SetupHolder.setup[SetupHolder.KEY_STACK_MAX_DEPTH]
    showPqiStack = SetupHolder.setup[SetupHolder.KEY_SHOW_PQI_STACK]
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
# Ideally, add a unit test for this helper.
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
    if __debug__ and obj is None:
        raise ValueError('The object is None, cannot find method by name')
    assert obj is not None, f'obj is None, cannot find method {name}'

    if callable(getattr(obj, name)):
        return getattr(obj, name)(*args, **kwargs)
    else:
        # Sometimes, ``obj`` has a variable with the same name as the method
        return find_callable_var(obj, name)(obj, *args, **kwargs)


def find_method_by_name_and_safe_call(obj, name, default_val, *args, **kwargs):
    try:
        return find_method_by_name_and_call(obj, name, *args, **kwargs)
    except Exception as e:
        pqi_log.warning(f'Error calling method {name} on {obj}: {e}')
        return default_val


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
    from PyQtInspect.pqi import SetupHolder
    need_to_include_fg = SetupHolder.setup[SetupHolder.KEY_IS_DEBUG_MODE]

    children = find_method_by_name_and_call(widget, 'children')
    for child in children:
        obj_name = get_widget_object_name(child)
        if obj_name == _PQI_HIGHLIGHT_FG_NAME and not need_to_include_fg:
            continue
        yield get_widget_class_name(child), id(child), get_widget_object_name(child)


def get_create_stack(widget):
    return _filter_trace_stack(getattr(widget, _PQI_STACK_WHEN_CREATED_ATTR, []))


def _get_full_class_name(o):
    klass = o.__class__
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + '.' + klass.__qualname__


def get_control_tree() -> typing.List[typing.Dict]:
    # === Helper functions ===
    def _get_object_identifier(obj):
        """ Get the object identifier of the obj.
        If the widget has an objectName, return it;
        Otherwise, return the hex id of the widget.
        """
        if isinstance(obj, QtWidgets.QSpacerItem):
            return 'Spacer'

        objectName = get_widget_object_name(obj)
        if objectName:
            return objectName
        return hex(id(obj))

    class _InfoBuilder:
        @staticmethod
        def _init_info(obj):
            return {
                TreeViewKeys.OBJ_ID_KEY: id(obj),
                TreeViewKeys.OBJ_NAME_KEY: _get_object_identifier(obj),
                TreeViewKeys.OBJ_CLS_NAME_KEY: _get_full_class_name(obj),
                TreeViewKeys.CHILDREN_KEY: [],
                TreeViewKeys.CHILD_CNT_KEY: 0,
            }

        @staticmethod
        def build_widget_info(widget):
            info = _InfoBuilder._init_info(widget)
            info[TreeViewKeys.CHILD_CNT_KEY] = traverse_widget(widget, info[TreeViewKeys.CHILDREN_KEY])
            return info

        @staticmethod
        def build_layout_info(layout, visitedWidgets):
            info = _InfoBuilder._init_info(layout)
            info[TreeViewKeys.CHILD_CNT_KEY] = traverse_layout(layout, visitedWidgets, info[TreeViewKeys.CHILDREN_KEY])
            return info

        @staticmethod
        def build_spacer_info(spacer):
            return _InfoBuilder._init_info(spacer)

    def traverse_widget(parent, child_info_list) -> int:
        """ Traverse the children of the parent widget and add the children info to the childrenInfoList.
        :param parent: the parent widget
        :param child_info_list: the list to store the children info
        :return: the number of widgets in the parent widget's hierarchy
        """
        widget_cnt = 0

        # Avoid visiting the same widget multiple times
        # When a widget is in a layout, don't visit it again when calling parent.children()
        visited = set()

        # ------ ATTENTION ------
        # We use explicit function call instead of binding to the parent.layout()
        # because sometimes it is shadowed by the same name variable in `__dict__`
        # -----------------------
        layout = QtWidgets.QWidget.layout(parent)
        if layout is not None:
            # Traverse the layout first
            layout_info = _InfoBuilder.build_layout_info(layout, visited)
            widget_cnt += layout_info[TreeViewKeys.CHILD_CNT_KEY]
            child_info_list.append(layout_info)

        for widget in QtWidgets.QWidget.children(parent):
            if not widget.isWidgetType() or id(widget) in visited or widget.objectName() == _PQI_HIGHLIGHT_FG_NAME:
                continue
            widget_cnt += 1

            widget_info = _InfoBuilder.build_widget_info(widget)
            widget_cnt += widget_info[TreeViewKeys.CHILD_CNT_KEY]
            child_info_list.append(widget_info)

        return widget_cnt

    def traverse_layout(parent_layout, visited_widgets, child_info_list) -> int:
        """ Traverse the parent layout and add the child widgets info to the child_info_list.
        :param parent_layout: the parentLayout to traverse
        :param visited_widgets: the set of visited widgets
        :param child_info_list: the list to store the children info
        :return: the number of widgets in the parentLayout
        """
        widget_cnt = 0
        for i in range(parent_layout.count()):
            item = parent_layout.itemAt(i)
            if isinstance(item, QtWidgets.QWidgetItem):
                widget = item.widget()
                if widget is None or id(widget) in visited_widgets:
                    continue

                visited_widgets.add(id(widget))
                widget_cnt += 1

                widget_info = _InfoBuilder.build_widget_info(widget)
                widget_cnt += widget_info[TreeViewKeys.CHILD_CNT_KEY]
                child_info_list.append(widget_info)
            elif isinstance(item, QtWidgets.QSpacerItem):
                child_info_list.append(_InfoBuilder.build_spacer_info(item))
            elif isinstance(item, QtWidgets.QLayoutItem):
                layout = item.layout()
                layout_info = _InfoBuilder.build_layout_info(layout, visited_widgets)
                widget_cnt += layout_info[TreeViewKeys.CHILD_CNT_KEY]
                child_info_list.append(layout_info)

        return widget_cnt

    from PyQtInspect.pqi import SetupHolder

    QtLib = import_Qt(SetupHolder.setup[SetupHolder.KEY_QT_SUPPORT])
    QtWidgets, QtGui = QtLib.QtWidgets, QtLib.QtGui  # noqa

    top_level_widgets = QtWidgets.QApplication.topLevelWidgets()
    res = []

    for topLevelWidget in top_level_widgets:
        widget_info = _InfoBuilder.build_widget_info(topLevelWidget)
        res.append(widget_info)
    return res


def import_Qt(qt_type: str):
    """
    Import Qt libraries by type.

    :param qt_type: The Qt type to import, either 'pyqt5' or 'pyside2'.
    """
    if qt_type == 'pyqt5':
        import PyQt5 as QtLib
        import PyQt5.QtCore, PyQt5.QtWidgets, PyQt5.QtGui
    elif qt_type == 'pyqt6':
        import PyQt6 as QtLib
        import PyQt6.QtCore, PyQt6.QtWidgets, PyQt6.QtGui
    elif qt_type == 'pyside2':
        import PySide2 as QtLib
        import PySide2.QtCore, PySide2.QtWidgets, PySide2.QtGui
    elif qt_type == 'pyside6':
        import PySide6 as QtLib
        import PySide6.QtCore, PySide6.QtWidgets, PySide6.QtGui
    else:
        pqi_log.warning(f'Unsupported Qt type: {qt_type}, maybe the function is called before the setup')
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

    QtCore = import_Qt(SetupHolder.setup[SetupHolder.KEY_QT_SUPPORT]).QtCore
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
    return import_wrap_module(SetupHolder.setup[SetupHolder.KEY_QT_SUPPORT])._pqi_is_valid(ptr)
