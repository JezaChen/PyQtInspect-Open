# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/18 14:24
# Description: 
# ==============================================
'''
This module holds the constants used for specifying the states of the debugger.
'''
from __future__ import nested_scopes

import logging
import sys  # Note: the sys import must be here anyways (others depend on it)


class DebugInfoHolder:
    # we have to put it here because it can be set through the command line (so, the
    # already imported references would not have it).
    DEBUG_RECORD_SOCKET_READS = False
    LOG_TO_FILE_LEVEL = logging.INFO
    LOG_TO_CONSOLE_LEVEL = logging.WARNING

import os

# Constant detects when running on Jython/windows properly later on.
IS_WINDOWS = sys.platform == 'win32'

IS_64BIT_PROCESS = sys.maxsize > (2 ** 32)

IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform == 'darwin'

IS_PYTHON_STACKLESS = "stackless" in sys.version.lower()

IS_PYCHARM_ATTACH = os.getenv('PYCHARM_ATTACH') == 'True'

#=======================================================================================================================
# Python 3?
#=======================================================================================================================
IS_PY3K = False
IS_PY34_OR_GREATER = False
IS_PY36_OR_GREATER = False
IS_PY37_OR_GREATER = False
IS_PY36_OR_LESSER = False
IS_PY38_OR_GREATER = False
IS_PY38 = False
IS_PY39_OR_GREATER = False
IS_PY311 = False
IS_PY311_OR_GREATER = False
IS_PY2 = True
IS_PY27 = False
IS_PY24 = False
try:
    if sys.version_info[0] >= 3:
        IS_PY3K = True
        IS_PY2 = False
        IS_PY34_OR_GREATER = sys.version_info >= (3, 4)
        IS_PY36_OR_GREATER = sys.version_info >= (3, 6)
        IS_PY37_OR_GREATER = sys.version_info >= (3, 7)
        IS_PY36_OR_LESSER = sys.version_info[:2] <= (3, 6)
        IS_PY38 = sys.version_info[0] == 3 and sys.version_info[1] == 8
        IS_PY38_OR_GREATER = sys.version_info >= (3, 8)
        IS_PY39_OR_GREATER = sys.version_info >= (3, 9)
        IS_PY311 = sys.version_info[0] == 3 and sys.version_info[1] == 11
        IS_PY311_OR_GREATER = sys.version_info >= (3, 11)
    elif sys.version_info[0] == 2 and sys.version_info[1] == 7:
        IS_PY27 = True
    elif sys.version_info[0] == 2 and sys.version_info[1] == 4:
        IS_PY24 = True
except AttributeError:
    pass  # Not all versions have sys.version_info


SHOW_DEBUG_INFO_ENV = os.getenv('PYCHARM_DEBUG') == 'True' or os.getenv('PQI_DEBUG') == 'True'

if SHOW_DEBUG_INFO_ENV:
    # show debug info before the debugger start
    DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = True
    DebugInfoHolder.LOG_TO_FILE_LEVEL = logging.DEBUG
    DebugInfoHolder.LOG_TO_CONSOLE_LEVEL = logging.DEBUG



#=======================================================================================================================
# Null
#=======================================================================================================================
class Null:
    """
    Gotten from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/68205
    """

    def __init__(self, *args, **kwargs):
        return None

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return self

    def __getattr__(self, mname):
        if len(mname) > 4 and mname[:2] == '__' and mname[-2:] == '__':
            # Don't pretend to implement special method names.
            raise AttributeError(mname)
        return self

    def __setattr__(self, name, value):
        return self

    def __delattr__(self, name):
        return self

    def __repr__(self):
        return "<Null>"

    def __str__(self):
        return "Null"

    def __len__(self):
        return 0

    def __getitem__(self):
        return self

    def __setitem__(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def __nonzero__(self):
        return 0

    def __iter__(self):
        return iter(())


# Default instance
NULL = Null()


#=======================================================================================================================
# GlobalDebuggerHolder
#=======================================================================================================================
class GlobalDebuggerHolder:
    '''
        Holder for the global debugger.
    '''
    global_dbg = None  # Note: don't rename (the name is used in our attach to process)


#=======================================================================================================================
# get_global_debugger
#=======================================================================================================================
def get_global_debugger():
    return GlobalDebuggerHolder.global_dbg


GetGlobalDebugger = get_global_debugger  # Backward-compatibility


#=======================================================================================================================
# set_global_debugger
#=======================================================================================================================
def set_global_debugger(dbg):
    GlobalDebuggerHolder.global_dbg = dbg


# =======================================================================================================================
# Qt Patch
# =======================================================================================================================

QtWidgetClasses = [
    'QWidget',
    'QAbstractButton',
    'QFrame',
    'QAbstractSlider',
    'QAbstractSpinBox',
    'QCalendarWidget',
    'QDialog',
    'QComboBox',
    'QDesktopWidget',
    'QDialogButtonBox',
    'QDockWidget',
    'QFocusFrame',
    'QGroupBox',
    'QKeySequenceEdit',
    'QLineEdit',
    'QMainWindow',
    'QMdiSubWindow',
    'QMenu',
    'QMenuBar',
    'QOpenGLWidget',
    'QProgressBar',
    'QRubberBand',
    'QSizeGrip',
    'QSplashScreen',
    'QSplitterHandle',
    'QStatusBar',
    'QTabBar',
    'QTabWidget',
    'QToolBar',
    'QWizardPage',
    'QCheckBox',
    'QPushButton',
    'QRadioButton',
    'QToolButton',
    'QCommandLinkButton',
    'QAbstractScrollArea',
    'QLCDNumber',
    'QLabel',
    # 'QSplitter',  # ignored
    'QStackedWidget',
    'QToolBox',
    'QAbstractItemView',
    'QGraphicsView',
    'QMdiArea',
    'QPlainTextEdit',
    'QScrollArea',
    'QTextEdit',
    'QColumnView',
    'QHeaderView',
    'QListView',
    'QTableView',
    'QTreeView',
    'QListWidget',
    'QUndoView',
    'QTableWidget',
    'QTreeWidget',
    'QTextBrowser',
    'QDial',
    'QScrollBar',
    'QSlider',
    'QDateTimeEdit',
    'QDoubleSpinBox',
    'QSpinBox',
    'QDateEdit',
    'QTimeEdit',
    'QColorDialog',
    'QErrorMessage',
    'QFileDialog',
    'QFontDialog',
    'QInputDialog',
    'QMessageBox',
    'QProgressDialog',
    'QWizard',
    'QFontComboBox',
]

if __name__ == '__main__':
    if Null():
        sys.stdout.write('here\n')
