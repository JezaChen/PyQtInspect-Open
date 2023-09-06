from __future__ import nested_scopes

# from _pydev_imps._pydev_saved_modules import threading
# from _pydevd_bundle.pydevd_constants import IS_PY38
import os
import threading  # todo used by only python3
import sys

from PyQtInspect._pqi_bundle.pqi_qt_tools import get_widget_size, get_widget_pos, get_parent_classes, get_stylesheet
from PyQtInspect.pqi_contants import get_global_debugger
from PyQtInspect.pqi_structures import QWidgetInfo


def set_trace_in_qt():
    # from _pydevd_bundle.pydevd_comm import get_global_debugger
    # debugger = get_global_debugger()
    # if debugger is not None:
    #     threading.current_thread()  # Create the dummy thread for qt.
    #     debugger.enable_tracing()
    pass


IS_PY38 = sys.version_info[0] == 3 and sys.version_info[1] == 8

_patched_qt = False


def patch_qt(qt_support_mode):
    '''
    This method patches qt (PySide, PyQt4, PyQt5) so that we have hooks to set the tracing for QThread.
    '''
    if not qt_support_mode:
        return

    if qt_support_mode is True or qt_support_mode == 'True':
        # do not break backward compatibility
        qt_support_mode = 'auto'

    if qt_support_mode == 'auto':
        qt_support_mode = os.getenv('PYDEVD_PYQT_MODE', 'auto')

    # Avoid patching more than once
    global _patched_qt
    if _patched_qt:
        return

    _patched_qt = True

    if qt_support_mode == 'auto':

        patch_qt_on_import = None
        try:
            if IS_PY38:
                raise ImportError
            import PySide6
            qt_support_mode = 'pyside6'
        except:
            try:
                # PY-50959
                # Problem:
                # 1. We have Python 3.8;
                # 2. PyQt compatible = Auto or PySide2;
                # 3. We try to import numpy, we get "AttributeError: module 'numpy.core' has no attribute 'numerictypes'"
                #
                # Solution:
                # We decided to turn off patching for PySide2 if we have Python 3.8
                # Here we skip 'import PySide2' and keep trying to import another qt libraries
                if IS_PY38:
                    raise ImportError
                import PySide2  # @UnresolvedImport @UnusedImport
                qt_support_mode = 'pyside2'
            except:
                try:
                    import Pyside  # @UnresolvedImport @UnusedImport
                    qt_support_mode = 'pyside'
                except:
                    try:
                        import PyQt6  # @UnresolvedImport @UnusedImport
                        qt_support_mode = 'pyqt6'
                    except:
                        try:
                            import PyQt5  # @UnresolvedImport @UnusedImport
                            qt_support_mode = 'pyqt5'
                        except:
                            try:
                                import PyQt4  # @UnresolvedImport @UnusedImport
                                qt_support_mode = 'pyqt4'
                            except:
                                return

    if qt_support_mode == 'pyside6':
        if IS_PY38:
            return
        try:
            import PySide6.QtCore  # @UnresolvedImport
            _internal_patch_qt(PySide6.QtCore, qt_support_mode)
        except:
            return
    elif qt_support_mode == 'pyside2':
        # PY-50959
        # We can get here only if PyQt compatible = PySide2, in this case we should return
        # See comment above about PY-50959
        if IS_PY38:
            return
        try:
            import PySide2.QtCore  # @UnresolvedImport
            _internal_patch_qt(PySide2.QtCore, qt_support_mode)
        except:
            return

    elif qt_support_mode == 'pyside':
        try:
            import PySide.QtCore  # @UnresolvedImport
            _internal_patch_qt(PySide.QtCore, qt_support_mode)
        except:
            return

    elif qt_support_mode == 'pyqt6':
        try:
            import PyQt6.QtCore  # @UnresolvedImport
            _internal_patch_qt(PyQt6.QtCore)
        except:
            return

    elif qt_support_mode == 'pyqt5':
        try:
            import PyQt5.QtCore  # @UnresolvedImport
            import PyQt5.QtWidgets  # @UnresolvedImport

            _internal_patch_qt(PyQt5.QtCore)
            _internal_patch_qt_widgets(PyQt5.QtWidgets, PyQt5.QtCore)
        except Exception as e:
            print(e)
            return

    # elif qt_support_mode == 'pyqt4':
    #     # Ok, we have an issue here:
    #     # PyDev-452: Selecting PyQT API version using sip.setapi fails in debug mode
    #     # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    #     # Mostly, if the user uses a different API version (i.e.: v2 instead of v1),
    #     # that has to be done before importing PyQt4 modules (PySide/PyQt5 don't have this issue
    #     # as they only implements v2).
    #     patch_qt_on_import = 'PyQt4'
    #     def get_qt_core_module():
    #         import PyQt4.QtCore  # @UnresolvedImport
    #         return PyQt4.QtCore
    #     _patch_import_to_patch_pyqt_on_import(patch_qt_on_import, get_qt_core_module)

    else:
        raise ValueError('Unexpected qt support mode: %s' % (qt_support_mode,))


# def _patch_import_to_patch_pyqt_on_import(patch_qt_on_import, get_qt_core_module):
#     # I don't like this approach very much as we have to patch __import__, but I like even less
#     # asking the user to configure something in the client side...
#     # So, our approach is to patch PyQt4 right before the user tries to import it (at which
#     # point he should've set the sip api version properly already anyways).
#
#     dotted = patch_qt_on_import + '.'
#     original_import = __import__
#
#     from _pydev_imps._pydev_sys_patch import patch_sys_module, patch_reload, cancel_patches_in_sys_module
#
#     patch_sys_module()
#     patch_reload()
#
#     def patched_import(name, *args, **kwargs):
#         if patch_qt_on_import == name or name.startswith(dotted):
#             builtins.__import__ = original_import
#             cancel_patches_in_sys_module()
#             _internal_patch_qt(get_qt_core_module()) # Patch it only when the user would import the qt module
#         return original_import(name, *args, **kwargs)
#
#     import sys
#     if sys.version_info[0] >= 3:
#         import builtins # Py3
#     else:
#         import __builtin__ as builtins
#
#     builtins.__import__ = patched_import


def _internal_patch_qt(QtCore, qt_support_mode='auto'):
    _original_thread_init = QtCore.QThread.__init__
    _original_runnable_init = QtCore.QRunnable.__init__
    _original_QThread = QtCore.QThread

    class FuncWrapper:
        def __init__(self, original):
            self._original = original

        def __call__(self, *args, **kwargs):
            set_trace_in_qt()
            return self._original(*args, **kwargs)

    class StartedSignalWrapper(QtCore.QObject):  # Wrapper for the QThread.started signal

        try:
            _signal = QtCore.Signal()  # @UndefinedVariable
        except:
            _signal = QtCore.pyqtSignal()  # @UndefinedVariable

        def __init__(self, thread, original_started):
            QtCore.QObject.__init__(self)
            self.thread = thread
            self.original_started = original_started
            if qt_support_mode in ('pyside', 'pyside2', 'pyside6'):
                self._signal = original_started
            else:
                self._signal.connect(self._on_call)
                self.original_started.connect(self._signal)

        def connect(self, func, *args, **kwargs):
            if qt_support_mode in ('pyside', 'pyside2', 'pyside6'):
                return self._signal.connect(FuncWrapper(func), *args, **kwargs)
            else:
                return self._signal.connect(func, *args, **kwargs)

        def disconnect(self, *args, **kwargs):
            return self._signal.disconnect(*args, **kwargs)

        def emit(self, *args, **kwargs):
            return self._signal.emit(*args, **kwargs)

        def _on_call(self, *args, **kwargs):
            set_trace_in_qt()

    class ThreadWrapper(QtCore.QThread):  # Wrapper for QThread

        def __init__(self, *args, **kwargs):
            _original_thread_init(self, *args, **kwargs)

            # In PyQt5 the program hangs when we try to call original run method of QThread class.
            # So we need to distinguish instances of QThread class and instances of QThread inheritors.
            if self.__class__.run == _original_QThread.run:
                self.run = self._exec_run
            else:
                self._original_run = self.run
                self.run = self._new_run
            self._original_started = self.started
            self.started = StartedSignalWrapper(self, self.started)

        def _exec_run(self):
            set_trace_in_qt()
            self.exec_()
            return None

        def _new_run(self):
            set_trace_in_qt()
            return self._original_run()

    class RunnableWrapper(QtCore.QRunnable):  # Wrapper for QRunnable

        def __init__(self, *args):
            _original_runnable_init(self, *args)

            self._original_run = self.run
            self.run = self._new_run

        def _new_run(self):
            set_trace_in_qt()
            return self._original_run()

    QtCore.QThread = ThreadWrapper
    QtCore.QRunnable = RunnableWrapper


def _internal_patch_qt_widgets(QtWidgets, QtCore, qt_support_mode='auto'):
    import inspect, sip, copy
    _original_QWidget_init = QtWidgets.QWidget.__init__
    oldEnterEvent = QtWidgets.QWidget.enterEvent
    oldLeaveEvent = QtWidgets.QWidget.leaveEvent
    oldMouseReleaseEvent = QtWidgets.QWidget.mouseReleaseEvent
    oldEvent = QtWidgets.QWidget.event

    lastHighlightWidget = None

    def _hideLastHighlightWidget():
        nonlocal lastHighlightWidget
        if isinstance(lastHighlightWidget, QtWidgets.QWidget) and not sip.isdeleted(lastHighlightWidget):
            lastHighlightWidget.hide()
            lastHighlightWidget = None

    def _createHighlightWidget(parent: QtWidgets.QWidget):
        widget = QtWidgets.QWidget.__new__(QtWidgets.QWidget)
        _original_QWidget_init(widget, parent)
        widget.setFixedSize(parent.size())
        widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        widget.setObjectName("_pqi_highlight_bg")
        widget.setStyleSheet("background-color: rgba(255, 0, 0, 0.2);")
        return widget

    def _filter_trace_stack(traceStacks):
        filteredStacks = []
        from PyQtInspect.pqi import SetupHolder
        stackMaxDepth = SetupHolder.setup["stack-max-depth"]
        stacks = traceStacks[1:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[1:]
        for frame in stacks:
            filteredStacks.append(
                {
                    'filename': frame.filename,
                    'lineno': frame.lineno,
                    'function': frame.function,
                    'code_context': frame.code_context,
                }
            )
        return filteredStacks

    def _new_QWidget_init(self, *args, **kwargs):
        _original_QWidget_init(self, *args, **kwargs)
        if sip.ispycreated(self):
            frames = inspect.stack()
            frame = inspect.currentframe()
            previousFrame = frame.f_back
            previousFrameInfo = inspect.getframeinfo(previousFrame)
            # 不要直接保存frame引用, 因为调用后frame会走到最后一行, 失去了回溯意义
            setattr(self, '_pqi_stacks_when_create', _filter_trace_stack(frames))

    # hook QWidget enterEvent
    def _enterEvent(self: QtWidgets.QWidget, event):
        nonlocal lastHighlightWidget

        def _mouseReleaseEvent(event):
            if event.button() != QtCore.Qt.LeftButton:
                return self._oldMouseReleaseEvent(event)
            debugger = get_global_debugger()
            if debugger is None or not debugger.inspect_enabled:
                return self._oldMouseReleaseEvent(event)
            debugger.notify_inspect_finished(self)
            if hasattr(self, '_pqi_highlight_bg'):
                self._pqi_highlight_bg.hide()
            self.mouseReleaseEvent = self._oldMouseReleaseEvent

        # setattr(_mouseReleaseEvent, '_pqi_hooked', True)

        if self.objectName() == "_pqi_highlight_bg":
            return oldEnterEvent(self, event)

        debugger = get_global_debugger()
        if debugger is None or not debugger.inspect_enabled:
            return oldEnterEvent(self, event)

        widget_info = QWidgetInfo(
            class_name=self.__class__.__name__,
            object_name=self.objectName(),
            stacks_when_create=self._pqi_stacks_when_create,
            size=get_widget_size(self),
            pos=get_widget_pos(self),
            parent_classes=list(get_parent_classes(self)),
            stylesheet=get_stylesheet(self)
        )
        debugger.send_widget_message(widget_info)
        if not hasattr(self, '_pqi_highlight_bg'):
            self._pqi_highlight_bg = _createHighlightWidget(self)

        self._pqi_highlight_bg.setFixedSize(self.size())
        _hideLastHighlightWidget()
        self._pqi_highlight_bg.show()
        lastHighlightWidget = self._pqi_highlight_bg

        self._oldMouseReleaseEvent = self.mouseReleaseEvent
        self.mouseReleaseEvent = _mouseReleaseEvent

        return oldEnterEvent(self, event)

    # hook QWidget leaveEvent
    def _leaveEvent(self: QtWidgets.QWidget, event):
        if self.objectName() == "_pqi_highlight_bg":
            return oldLeaveEvent(self, event)

        if hasattr(self, '_pqi_highlight_bg'):
            self._pqi_highlight_bg.hide()

        if hasattr(self, '_oldMouseReleaseEvent'):
            self.mouseReleaseEvent = self._oldMouseReleaseEvent

        return oldLeaveEvent(self, event)

    # hook QWidget mouseReleaseEvent
    def _mouseReleaseEvent(self: QtWidgets.QWidget, event):
        if event.button() != QtCore.Qt.LeftButton:
            return oldMouseReleaseEvent(self, event)
        debugger = get_global_debugger()
        if debugger is None or not debugger.inspect_enabled:
            return oldMouseReleaseEvent(self, event)
        debugger.notify_inspect_finished()
        if hasattr(self, '_pqi_highlight_bg'):
            self._pqi_highlight_bg.hide()

    def _event(self: QtWidgets.QWidget, event):
        if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
            debugger = get_global_debugger()
            if debugger is not None and debugger.inspect_enabled:
                debugger.notify_inspect_finished()
                _hideLastHighlightWidget()
                return True
        return oldEvent(self, event)

    QtWidgets.QWidget.__init__ = _new_QWidget_init
    QtWidgets.QWidget.enterEvent = _enterEvent
    QtWidgets.QWidget.leaveEvent = _leaveEvent
    print("patched")
