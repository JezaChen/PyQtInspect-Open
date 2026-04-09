# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/18 14:24
# Description: 
# ==============================================
'''
This module holds the constants used for specifying the states of the debugger.
'''

import logging
import sys  # Note: the sys import must be here anyways (others depend on it)
import os


class DebugInfoHolder:
    # we have to put it here because it can be set through the command line (so, the
    # already imported references would not have it).
    DEBUG_RECORD_SOCKET_READS = False
    LOG_TO_FILE_LEVEL = logging.INFO
    LOG_TO_CONSOLE_LEVEL = logging.WARNING


# Platform detection
IS_WINDOWS = sys.platform == 'win32'

IS_64BIT_PROCESS = sys.maxsize > (2 ** 32)

IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform == 'darwin'

# Python version checks
IS_PY36_OR_GREATER = sys.version_info >= (3, 6)
IS_PY36_OR_LESSER = sys.version_info[:2] <= (3, 6)
IS_PY38_OR_GREATER = sys.version_info >= (3, 8)
IS_PY311_OR_GREATER = sys.version_info >= (3, 11)

SHOW_DEBUG_INFO_ENV = os.getenv('PYCHARM_DEBUG') == 'True' or os.getenv('PQI_DEBUG') == 'True'

if SHOW_DEBUG_INFO_ENV:
    # show debug info before the debugger start
    DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = True
    DebugInfoHolder.LOG_TO_FILE_LEVEL = logging.DEBUG
    DebugInfoHolder.LOG_TO_CONSOLE_LEVEL = logging.DEBUG


import _thread as thread
_thread_id_lock = thread.allocate_lock()
thread_get_ident = thread.get_ident


#=======================================================================================================================
# get_pid
#=======================================================================================================================
def get_pid():
    try:
        return os.getpid()
    except AttributeError:
        try:
            # Jython does not have it!
            import java.lang.management.ManagementFactory  # @UnresolvedImport -- just for jython
            pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName()
            return pid.replace('@', '_')
        except:
            # ok, no pid available (will be unable to debug multiple processes)
            return '000001'


def get_current_thread_id(thread):
    '''
    Note: the difference from get_current_thread_id to get_thread_id is that
    for the current thread we can get the thread id while the thread.ident
    is still not set in the Thread instance.
    '''
    try:
        # Fast path without getting lock.
        tid = thread.__pydevd_id__
        if tid is None:
            # Fix for https://www.brainwy.com/tracker/PyDev/645
            # if __pydevd_id__ is None, recalculate it... also, use an heuristic
            # that gives us always the same id for the thread (using thread.ident or id(thread)).
            raise AttributeError()
    except AttributeError:
        with _thread_id_lock:
            # We do a new check with the lock in place just to be sure that nothing changed
            tid = getattr(thread, '__pydevd_id__', None)
            if tid is None:
                # Note: don't use thread.ident because a new thread may have the
                # same id from an old thread.
                pid = get_pid()
                tid = 'pid_%s_id_%s' % (pid, id(thread))
                thread.__pydevd_id__ = tid

    return tid


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

# Default highlight overlay color: red with ~20% opacity (RGBA integers 0-255)
DEFAULT_HIGHLIGHT_COLOR = "255,0,0,51"

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

