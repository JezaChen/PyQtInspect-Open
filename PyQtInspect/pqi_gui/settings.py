# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/7 16:11
# Description: 
# ==============================================
from PyQt5 import QtWidgets, QtGui, QtCore

settingsFile = "settings.ini"

setting = QtCore.QSettings(settingsFile, QtCore.QSettings.IniFormat)
setting.setIniCodec("UTF-8")


def getPyCharmPath():
    return setting.value("PyCharmPath", "")


def setPyCharmPath(path: str):
    setting.setValue("PyCharmPath", path)
    setting.sync()
    return


def findDefaultPycharmPath():
    import os
    for path in os.environ["PATH"].split(";"):
        if "pycharm" in path.lower():
            return path + "\\pycharm64.exe"
    return ""
