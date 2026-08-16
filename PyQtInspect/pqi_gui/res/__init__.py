# -*- encoding:utf-8 -*-
# resources for pqi_gui

_PQI_GUI_ICON = None


def get_icon():
    global _PQI_GUI_ICON
    if _PQI_GUI_ICON is None:
        from PyQt5 import QtGui
        from . import resources

        _PQI_GUI_ICON = QtGui.QIcon(":/icons/icon.png")
    return _PQI_GUI_ICON
