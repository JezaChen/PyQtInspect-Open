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

_PYCHARM_EXECUTABLE_NAMES = ["pycharm64.exe", "pycharm.exe", "pycharm"]


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

    def findForUnix():
        """ for Unix-like systems, we can use which command to find the path """
        output = subprocess.run(
            'which pycharm',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        if output.stdout:
            return output.stdout.strip()

    # First, try to use terminal command to find the path
    if sys.platform == "win32":
        defaultPath = findForWindows()
        if defaultPath:
            return defaultPath
    else:
        defaultPath = findForUnix()
        if defaultPath:
            return defaultPath

    # If the above method fails, we can try to find the path from the environment variables
    for path in os.environ["PATH"].split(";" if sys.platform == "win32" else ":"):
        for pycharm_exe_name in _PYCHARM_EXECUTABLE_NAMES:
            pycharm_path = os.path.join(path, pycharm_exe_name)
            if os.path.isfile(pycharm_path):
                return pycharm_path
    return ""
