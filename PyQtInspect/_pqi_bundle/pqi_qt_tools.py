# PQI Tools for Qt

# todo Only Supports PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui
import inspect


def get_qt_version():
    return QtCore.PYQT_VERSION_STR


def get_qwidget_class_name(qwidget):
    return qwidget.__class__.__name__


def get_qwidget_object_name(qwidget):
    return qwidget.objectName()


def get_parent_classes(widget: QtWidgets.QWidget):
    while True:
        parent = widget.parent()
        if parent is None:
            break
        widget = parent
        yield widget.__class__.__name__
