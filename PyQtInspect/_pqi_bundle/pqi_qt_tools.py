# PQI Tools for Qt

# # todo Only Supports PyQt5
# from PyQt5 import QtWidgets, QtCore, QtGui
# import inspect
#
#
# def get_qt_version():
#     return QtCore.PYQT_VERSION_STR


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


def exec_code_in_widget(widget, code: str):
    # if not isinstance(widget, QtWidgets.QWidget):
    #     return

    if hasattr(widget, '_pqi_exec'):
        widget._pqi_exec(code)


def import_Qt(qt_version: str):
    if qt_version == 'pyqt5':
        import PyQt5 as QtLib
    elif qt_version == 'pyside2':
        import PySide2 as QtLib
    else:
        raise ValueError(f'Unsupported Qt version: {qt_version}')

    return QtLib
