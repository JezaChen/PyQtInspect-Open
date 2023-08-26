# PQI Tools for Qt

# todo Only Supports PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui
import inspect


def get_qt_version():
    return QtCore.PYQT_VERSION_STR


def get_widget_class_name(widget):
    return widget.__class__.__name__


def get_widget_object_name(widget):
    return widget.objectName()


def get_widget_size(widget: QtWidgets.QWidget):
    return widget.size().width(), widget.size().height()


def get_widget_pos(widget: QtWidgets.QWidget):
    return widget.pos().x(), widget.pos().y()


def get_parent_classes(widget: QtWidgets.QWidget):
    while True:
        parent = widget.parent()
        if parent is None:
            break
        widget = parent
        yield widget.__class__.__name__


def get_stylesheet(widget: QtWidgets.QWidget):
    return widget.styleSheet()


