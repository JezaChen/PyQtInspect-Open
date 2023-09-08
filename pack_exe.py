# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/9/18 15:15
# Description: 
# ==============================================
import PyInstaller.__main__

PyInstaller.__main__.run([
    "PyQtInspect\\pqi_server_gui.py",
    "--onefile",
    "--windowed",
    "--clean",
])
