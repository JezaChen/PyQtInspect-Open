# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/9/7 16:11
# Description: 
# ==============================================
import sys

from PyQt5 import QtWidgets, QtGui, QtCore

settingsFile = "settings.ini"

setting = QtCore.QSettings(settingsFile, QtCore.QSettings.IniFormat)
setting.setIniCodec("UTF-8")


def getPyCharmPath():
    return setting.value("PyCharmPath", "")


def setPyCharmPath(path: str):
    setting.setValue("PyCharmPath", path)
    setting.sync()


def findDefaultPycharmPath():
    import os, subprocess

    def findForWindows():
        """ for Windows, we can use powershell command to find the path """
        output = subprocess.run(
            'powershell -Command "$(Get-Command pycharm).path"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        if output.stdout:
            return output.stdout.strip()

    # First, try to use terminal command to find the path
    # TODO: add support for Linux and macOS
    if sys.platform == "win32":
        if defaultPath := findForWindows():
            return defaultPath

    # If the above method fails, we can try to find the path from the environment variables
    for path in os.environ["PATH"].split(";"):
        if "pycharm" in path.lower():
            return path + "\\pycharm64.exe"
    return ""
