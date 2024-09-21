# -*- encoding:utf-8 -*-
"""
python pack_exe.py py2exe
"""

import os
from pathlib import Path
from distutils.sysconfig import get_python_lib
from distutils.core import setup
import py2exe
import sys


def find_Qt_bin_path():
    pyqt_path = Path(get_python_lib()) / 'PyQt5'

    for file in pyqt_path.rglob('Qt5Core.dll'):
        return file.parent


def find_Qt_qwindows_dll():
    pyqt_path = Path(get_python_lib()) / 'PyQt5'

    for file in pyqt_path.rglob('qwindows.dll'):
        return file


def find_Qt_qwindowsvistastyle_dll():
    pyqt_path = Path(get_python_lib()) / 'PyQt5'

    for file in pyqt_path.rglob('qwindowsvistastyle.dll'):
        return file


INCLUDES = ["PyQt5.sip"]

options = {
    "py2exe":
        {
            # "compressed": 1,  # compress
            "optimize": 2,
            # "bundle_files": 1,  # all in one file
            "includes": INCLUDES,
            "dll_excludes": ["MSVCR100.dll"],
        }
}

Qt_path = find_Qt_bin_path()

setup(
    options=options,
    description="this is a py2exe test",
    zipfile=None,
    console=[{"script": 'PyQtInspect/pqi_server_gui.py'}],
    data_files=[  # the files need to be copied
        ('platforms', [find_Qt_qwindows_dll()]),
        ('styles', [find_Qt_qwindowsvistastyle_dll()]),
        ('', [
            f'{Qt_path}\\Qt5Core.dll',
            f'{Qt_path}\\Qt5Gui.dll',
            f'{Qt_path}\\Qt5Widgets.dll',
        ])
    ],
    packages=['PyQtInspect']
)
