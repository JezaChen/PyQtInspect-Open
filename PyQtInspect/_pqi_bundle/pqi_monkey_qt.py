from __future__ import nested_scopes

import collections
import os
import queue
import sys
from contextlib import redirect_stdout
from io import StringIO

from PyQtInspect._pqi_bundle.pqi_qt_tools import get_widget_size, get_widget_pos, get_parent_info, get_stylesheet, \
    get_children_info
from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger, QtWidgetClasses
from PyQtInspect._pqi_bundle.pqi_stack_tools import getStackFrame
from PyQtInspect._pqi_bundle.pqi_structures import QWidgetInfo


def set_trace_in_qt():
    # from _pydevd_bundle.pydevd_comm import get_global_debugger
    # debugger = get_global_debugger()
    # if debugger is not None:
    #     threading.current_thread()  # Create the dummy thread for qt.
    #     debugger.enable_tracing()
    pass


IS_PY38 = sys.version_info[0] == 3 and sys.version_info[1] == 8

_patched_qt = False


def patch_qt(qt_support_mode, is_attach=False):
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
            import PySide2.QtWidgets
            _internal_patch_qt(PySide2.QtCore, qt_support_mode)
            _internal_patch_qt_widgets(PySide2.QtWidgets, PySide2.QtCore, qt_support_mode)
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
            _internal_patch_qt_widgets(PyQt5.QtWidgets, PyQt5.QtCore, qt_support_mode, is_attach)
        except Exception as e:
            print(e)
            return

    # todo PyQt4
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
                self.run = self._pqi_exec_run
            else:
                # MUST ADD PREFIX '_pqi_' to the method name, otherwise it will cause infinite recursion
                # 如果使用和pydevd相同的变量名
                # 则根据继承关系 QThead的子类 -> QThreadWrapper in pqi -> QThreadWrapper in pydevd -> QThread
                # pqi中的self._pqi_original_run会指向pydevd中的self.run,
                # 而此时self.run已经被pqi中的self._pqi_new_run(in pqi!!! pqi层的QThreadWrapper同名方法覆盖了pydevd层的方法)替换
                # 因此会无限递归pqi层面的QThreadWrapper的self._pqi_new_run方法
                self._pqi_original_run = self.run
                self.run = self._pqi_new_run
            self._original_started = self.started
            self.started = StartedSignalWrapper(self, self.started)

        # MUST ADD PREFIX '_pqi_' to the method name, otherwise it will cause infinite recursion
        def _pqi_exec_run(self):
            set_trace_in_qt()
            self.exec_()
            return None

        def _pqi_new_run(self):
            set_trace_in_qt()
            return self._pqi_original_run()

    class RunnableWrapper(QtCore.QRunnable):  # Wrapper for QRunnable

        def __init__(self, *args):
            _original_runnable_init(self, *args)

            self._pqi_original_run = self.run
            self.run = self._pqi_new_run

        def _pqi_new_run(self):
            set_trace_in_qt()
            return self._pqi_original_run()

    QtCore.QThread = ThreadWrapper
    QtCore.QRunnable = RunnableWrapper


def _internal_patch_qt_widgets(QtWidgets, QtCore, qt_support_mode='auto', is_attach=False):
    import inspect
    # _original_QWidget_init = QtWidgets.QWidget.__init__

    lastHighlightWidget = None
    enteredWidgetStack = []

    if qt_support_mode.startswith("pyqt"):
        import sip
        isdeleted = sip.isdeleted
        ispycreated = sip.ispycreated
    elif qt_support_mode.startswith("pyside"):  # todo pyside6 also use this?
        import shiboken2  # todo: or shiboken?
        isdeleted = lambda obj: not shiboken2.isValid(obj)
        ispycreated = shiboken2.createdByPython

    def _filterEnteredWidgetStack():
        nonlocal enteredWidgetStack
        while enteredWidgetStack:
            wgt = enteredWidgetStack[-1]
            if isdeleted(wgt):
                enteredWidgetStack.pop()
            else:
                break

    def _clearEnteredWidgetStack():
        nonlocal enteredWidgetStack
        enteredWidgetStack.clear()

    def _showLastHighlightWidget():
        nonlocal lastHighlightWidget
        _filterEnteredWidgetStack()
        if not enteredWidgetStack:
            return

        obj = enteredWidgetStack[-1]
        # todo no need for attached
        # if not hasattr(obj, '_pqi_stacks_when_create'):
        #     return

        def _mouseReleaseEvent(event):
            if event.button() != QtCore.Qt.LeftButton:
                return obj._oldMouseReleaseEvent(event)
            debugger = get_global_debugger()
            if debugger is None or not debugger.inspect_enabled:
                return obj._oldMouseReleaseEvent(event)
            debugger.notify_inspect_finished(obj)
            if hasattr(obj, '_pqi_highlight_bg'):
                obj._pqi_highlight_bg.hide()
                _clearEnteredWidgetStack()
            obj.mouseReleaseEvent = obj._oldMouseReleaseEvent

        setattr(_mouseReleaseEvent, '_pqi_hooked', True)

        if obj.objectName() == "_pqi_highlight_bg":
            return

        debugger = get_global_debugger()
        if debugger is None or not debugger.inspect_enabled:
            return

        # === send widget info === #
        # todo parent信息貌似可以缓存? changeParent可能会导致parent信息变化
        parent_info = list(get_parent_info(obj))
        parent_classes, parent_ids, parent_obj_names = [], [], []
        if parent_info:
            parent_classes, parent_ids, parent_obj_names = zip(*parent_info)
        widget_info = QWidgetInfo(
            class_name=obj.__class__.__name__,
            object_name=obj.objectName(),
            id=id(obj),
            stacks_when_create=[],
            size=get_widget_size(obj),
            pos=get_widget_pos(obj),
            parent_classes=parent_classes,
            parent_ids=parent_ids,
            parent_object_names=parent_obj_names,
            stylesheet=get_stylesheet(obj),
        )
        debugger.send_widget_message(widget_info)

        # === highlight widget === #
        if not hasattr(obj, '_pqi_highlight_bg'):
            obj._pqi_highlight_bg = _createHighlightWidget(obj)

        obj._pqi_highlight_bg.setFixedSize(obj.size())
        _hideLastHighlightWidget()
        obj._pqi_highlight_bg.show()
        lastHighlightWidget = obj._pqi_highlight_bg

        if not hasattr(obj.mouseReleaseEvent, '_pqi_hooked'):
            obj._oldMouseReleaseEvent = obj.mouseReleaseEvent
        obj.mouseReleaseEvent = _mouseReleaseEvent

    class EventListener(QtCore.QObject):
        def _handleEnterEvent(self, obj, event):
            nonlocal lastHighlightWidget
            enteredWidgetStack.append(obj)
            _showLastHighlightWidget()

        def _handleLeaveEvent(self, obj, event):
            if enteredWidgetStack and enteredWidgetStack[-1] == obj:
                enteredWidgetStack.pop()
            else:
                enteredWidgetStack.clear()

            if obj.objectName() == "_pqi_highlight_bg":
                return

            if hasattr(obj, '_pqi_highlight_bg'):
                obj._pqi_highlight_bg.hide()

            if hasattr(obj, '_oldMouseReleaseEvent'):
                obj.mouseReleaseEvent = obj._oldMouseReleaseEvent

            _showLastHighlightWidget()

        def eventFilter(self, obj, event):
            if event.type() == QtCore.QEvent.Enter:
                self._handleEnterEvent(obj, event)
            elif event.type() == QtCore.QEvent.Leave:
                self._handleLeaveEvent(obj, event)
            elif event.type() == QtCore.QEvent.User:
                # handle highlight
                if hasattr(event, '_pqi_is_highlight'):
                    is_highlight = event._pqi_is_highlight
                    if is_highlight:
                        obj._pqi_highlight_self()
                    else:
                        obj._pqi_unhighlight_self()
                # handle code exec
                if hasattr(event, '_pqi_exec_code'):
                    code = event._pqi_exec_code
                    obj._pqi_exec(code)
            return False

    def _hideLastHighlightWidget():
        nonlocal lastHighlightWidget
        if isinstance(lastHighlightWidget, QtWidgets.QWidget) and not isdeleted(lastHighlightWidget):
            lastHighlightWidget.hide()
        lastHighlightWidget = None

    def _createHighlightWidget(parent: QtWidgets.QWidget):
        # 先new再调用之前的__init__
        widget = QtWidgets.QWidget.__new__(QtWidgets.QWidget)
        QtWidgets.QWidget._original_QWidget_init(widget, parent)
        widget.setFixedSize(parent.size())
        widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        widget.setObjectName("_pqi_highlight_bg")
        widget.setStyleSheet("background-color: rgba(255, 0, 0, 0.2);")
        return widget

    def _filter_trace_stack(traceStacks):
        filteredStacks = []
        from PyQtInspect.pqi import SetupHolder
        stackMaxDepth = SetupHolder.setup["stack-max-depth"]
        stacks = traceStacks[2:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[2:]
        for frame, lineno in stacks:
            filteredStacks.append(
                {
                    'filename': inspect.getsourcefile(frame),
                    'lineno': lineno,
                    'function': frame.f_code.co_name,
                }
            )
        return filteredStacks

    def _new_QWidget_init(self, *args, **kwargs):
        self._original_QWidget_init(*args, **kwargs)
        if ispycreated(self):
            frames = getStackFrame()
            setattr(self, '_pqi_stacks_when_create', frames)
        self._pqi_event_listener = EventListener()
        self.installEventFilter(self._pqi_event_listener)

        # === register widget === #
        debugger = get_global_debugger()
        if debugger is not None:
            debugger.register_widget(self)

    def _pqi_exec(self: QtWidgets.QWidget, code):
        debugger = get_global_debugger()
        try:
            f = StringIO()
            with redirect_stdout(f):
                exec(code, globals(), locals())
            if debugger is not None:
                debugger.notify_exec_code_result(f.getvalue())
        except Exception as e:
            if debugger is not None:
                debugger.notify_exec_code_error_message(str(e))

    def _pqi_highlight_self(self: QtWidgets.QWidget):
        nonlocal lastHighlightWidget
        if not hasattr(self, '_pqi_highlight_bg'):
            self._pqi_highlight_bg = _createHighlightWidget(self)

        self._pqi_highlight_bg.setFixedSize(self.size())
        _hideLastHighlightWidget()
        self._pqi_highlight_bg.show()
        lastHighlightWidget = self._pqi_highlight_bg

    def _pqi_unhighlight_self(self: QtWidgets.QWidget):
        nonlocal lastHighlightWidget
        if hasattr(self, '_pqi_highlight_bg'):
            self._pqi_highlight_bg.hide()
            lastHighlightWidget = None

    # ================================
    # ATTACH
    # ================================
    def _patch_old_widgets_when_attached():
        topLevelWidgets = QtWidgets.QApplication.topLevelWidgets()
        widgetsToPatch = collections.deque(topLevelWidgets)
        while widgetsToPatch:  # BFS traverse
            widget = widgetsToPatch.popleft()

            if isdeleted(widget) or not ispycreated(widget):
                continue

            event_listener = EventListener()
            event_listener.moveToThread(widget.thread())
            widget._pqi_event_listener = event_listener
            widget.installEventFilter(widget._pqi_event_listener)

            # === register widget === #
            debugger = get_global_debugger()
            if debugger is not None:
                debugger.register_widget(widget)

            widgetsToPatch.extend(widget.findChildren(QtWidgets.QWidget))

    # 对于PyQt, 仅需patch基类QWidget即可
    # 但对于PySide, 则需要给所有的QWidget子类都打上补丁
    classesToPatch = QtWidgetClasses if qt_support_mode.startswith('pyside') else ['QWidget']

    for widgetClsName in classesToPatch:
        widgetCls = getattr(QtWidgets, widgetClsName)
        widgetCls._original_QWidget_init = widgetCls.__init__
        widgetCls.__init__ = _new_QWidget_init
        widgetCls._pqi_exec = _pqi_exec
        widgetCls._pqi_highlight_self = _pqi_highlight_self
        widgetCls._pqi_unhighlight_self = _pqi_unhighlight_self

    if is_attach:
        _patch_old_widgets_when_attached()

    print("<patched>")
