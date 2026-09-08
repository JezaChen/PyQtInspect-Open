# -*- encoding:utf-8 -*-
import collections
import sys
from contextlib import redirect_stdout
from io import StringIO
import os

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.monkey_qt.detailed_inspect_tooltip import DetailedInspectTooltipManager
from PyQtInspect._pqi_bundle.monkey_qt.event_listeners import make_qt_event_listener_cls, make_native_event_listener_cls
from PyQtInspect._pqi_bundle.monkey_qt.shared.shared_api import QObjectInspectAPI, QObjectInspectAPIFunctions, QtModuleAPI
from PyQtInspect._pqi_bundle.monkey_qt.shared.shared_tools import is_widget_patched, mark_widget_patched
from PyQtInspect._pqi_bundle.monkey_qt.widget_creation_stack import capture_current_stack
from PyQtInspect._pqi_bundle.monkey_qt.widget_highlighter import QtWidgetHighlighter
from PyQtInspect._pqi_bundle.monkey_qt.widget_patching.enter_widget_stack import EnteredWidgetStack
from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger, QtWidgetClasses
from PyQtInspect._pqi_bundle.monkey_qt.metadata import (
    _PQI_STACK_WHEN_CREATED_ATTR,
    SuppressPatchMark,
)

def patch_qt_widgets(QtModule, qt_support_mode='auto', is_attach=False):
    QtWidgets = QtModule.QtWidgets
    QtCore = QtModule.QtCore

    isdeleted = lambda obj: False
    ispycreated = lambda obj: False

    if qt_support_mode.startswith("pyqt"):
        sip = QtModule.sip
        isdeleted = sip.isdeleted
        ispycreated = sip.ispycreated
    elif qt_support_mode.startswith("pyside"):  # todo pyside6 also use this?
        if qt_support_mode == 'pyside2':
            import shiboken2 as _shiboken
        elif qt_support_mode == 'pyside6':
            import shiboken6 as _shiboken
        isdeleted = lambda obj: not _shiboken.isValid(obj)
        ispycreated = _shiboken.createdByPython

    # init internal shared APIs
    QtModuleAPI.init_instance(QtModule)
    QObjectInspectAPI.init_instance(QObjectInspectAPIFunctions(isdeleted, ispycreated))

    highlighter = QtWidgetHighlighter()
    detailed_inspect_tooltip_mgr = DetailedInspectTooltipManager(QtModule)
    entered_widget_stack = EnteredWidgetStack()

    EventListener = make_qt_event_listener_cls(QtModule, entered_widget_stack, detailed_inspect_tooltip_mgr, highlighter)
    NativeEventListener = make_native_event_listener_cls(QtModule)

    def _initGlobalEventFilter():
        """ Initialize the global event filters when it does not exist """
        debugger = get_global_debugger()

        app = QtWidgets.QApplication.instance()
        if app is None:
            sys.stderr.write("QtWidgets.QApplication.instance() is None, stop attaching...")
            sys.stderr.flush()
            return

        # find one of the top-level widgets to move the event filter to the main thread
        topLevelWidgets = QtWidgets.QApplication.topLevelWidgets()
        if not topLevelWidgets:
            sys.stderr.write("Top-level widgets not found, stop attaching...")
            sys.stderr.flush()
            return

        topLevelWgt = topLevelWidgets[0]

        # Global event filter
        if debugger.global_event_filter is None:
            eventFilter = EventListener()
            # We need to move the event filter to the main thread
            eventFilter.moveToThread(topLevelWgt.thread())
            debugger.global_event_filter = eventFilter
            app.installEventFilter(eventFilter)

        # Global native event filter
        if debugger.global_native_event_filter is None and NativeEventListener is not None:
            nativeEventFilter = NativeEventListener()
            debugger.global_native_event_filter = nativeEventFilter
            app.installNativeEventFilter(nativeEventFilter)

    def _patchWidget(obj, *, attach=False):
        """ Install event listener and register widget to debugger """
        if not attach:
            # We use the Qt property system to mark the widget inspected
            #   because Python binding instance may change and lose the mark
            # To avoid the situation that attributes being dynamically added inside the `__init__` method
            #   and Qt inside directly executing the `event` method.
            # At this point, some custom classes may not have fully initialized
            #   and the event method can reference an uninitialized attribute.
            # So we use the QTimer and wait for `__init__` to finish.
            # ---
            # Bug Fixed 20240819: when the widget is deleted, the QTimer will not be executed.
            #   So we need to check if the widget is deleted before setting the property.
            # ---
            QtCore.QTimer.singleShot(0, lambda: mark_widget_patched(obj) if not isdeleted(obj) else None)
        else:
            # Attach thread may be different from the main thread,
            #   so the timer method will be invalid.
            # We just set the property directly because the widget has been initialized.
            mark_widget_patched(obj)
        # === register widget === #
        debugger = get_global_debugger()
        debugger.register_widget(obj)

    def _needExtraPatchAfterInit(obj):
        """ Check if the widget needs extra patch after __init__ """
        for specialMethod in ['viewport', 'tabBar', 'header', 'lineEdit']:
            try:
                p = object.__getattribute__(obj, specialMethod)
            except AttributeError:
                continue
            if callable(p) and isinstance(p(), QtWidgets.QWidget):
                return True

        # for some complex widgets like QCalendarWidget, there may be multiple child widgets that should be patched
        if isinstance(obj, (
                QtWidgets.QCalendarWidget,
                QtWidgets.QToolBox,
                QtWidgets.QToolBar,
                QtWidgets.QAbstractSpinBox,
                QtWidgets.QDialogButtonBox
        )):
            return True

        return False

    def _extraPatchAfterInit(obj):
        # === SPECIAL PATCH WIDGETS CREATED BY C++ === #
        if isdeleted(obj):
            return

        need_to_patch_children = False

        for specialMethod in ['viewport', 'tabBar', 'header', 'lineEdit']:
            # Bug fixed 20250302: Use a safer way to get the attribute
            # For some widget class which override the `__getattr__` method, where the object may access its own attribute
            #   but the attribute is not initialized yet (because the `__init__` method is not finished when patching),
            #   the `__getattr__` method will recursively call itself infinitely.
            # --> Spyder MainWindow
            try:
                p = object.__getattribute__(obj, specialMethod)
            except AttributeError:
                continue
            if callable(p) and isinstance(p(), QtWidgets.QWidget):
                need_to_patch_children = True
                break

        # for some complex widgets like QCalendarWidget, there may be multiple child widgets that should be patched
        if isinstance(obj, (QtWidgets.QCalendarWidget, QtWidgets.QToolBox, QtWidgets.QToolBar)):
            need_to_patch_children = True

        if need_to_patch_children:
            for child in obj.findChildren(QtWidgets.QWidget):
                if not is_widget_patched(child):
                    _patchWidget(child)

        # for QAbstractSpinBox we should install event listener on its line edit
        if isinstance(obj, (QtWidgets.QAbstractSpinBox,)):
            line_edit = obj.lineEdit()
            if line_edit and is_widget_patched(line_edit):  # lineEdit may be None
                _patchWidget(obj.lineEdit())

        # for QDialogButtonBox we should install event listener on its buttons (Issue #2)
        if isinstance(obj, QtWidgets.QDialogButtonBox):
            for button in obj.buttons():
                _patchWidget(button)

    def _new_QWidget_init(self, *args, **kwargs):
        self._original_QWidget_init(*args, **kwargs)
        if not ispycreated(self):
            # DO NOT install event listener for non-pycreated widget, because it may cause crash when exit
            return

        if SuppressPatchMark.is_marked(self):
            return

        # === save stack when create === #
        frames = capture_current_stack()
        setattr(self, _PQI_STACK_WHEN_CREATED_ATTR, frames)

        # Initialize the global filter when it does not exist
        _initGlobalEventFilter()

        # Patch widget
        _patchWidget(self)

        # Issue #20
        # Patch the child widgets created by C++ layer after the __init__ method is finished
        # Why? Some widgets create child widgets only after their C++ constructor is called.
        # These child widgets cannot be captured in the current _new_QWidget_init method.
        # We need to delay and capture these child widgets in the later loop.
        if _needExtraPatchAfterInit(self):
            QtCore.QTimer.singleShot(0, lambda: _extraPatchAfterInit(self))

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

    def _notify_patch_success():
        _debugger = get_global_debugger()
        _debugger.send_qt_patch_success_message()

    # ================================#
    #            ATTACH               #
    # ================================#
    def _patch_old_widgets_when_attached():
        # Initialize the global filter when beginning attach
        _initGlobalEventFilter()
        # Patch the existing widgets
        topLevelWidgets = QtWidgets.QApplication.topLevelWidgets()
        widgetsToPatch = collections.deque(topLevelWidgets)
        while widgetsToPatch:  # BFS traverse
            widget = widgetsToPatch.popleft()

            if isdeleted(widget) or not ispycreated(widget):
                continue

            # === patch widget ===
            _patchWidget(widget, attach=True)

            widgetsToPatch.extend(widget.findChildren(QtWidgets.QWidget))

    # For PyQt, patching the base QWidget class is sufficient.
    # For PySide, every QWidget subclass needs to be patched.
    classesToPatch = QtWidgetClasses if qt_support_mode.startswith('pyside') else ['QWidget']

    for widgetClsName in classesToPatch:
        widgetCls = getattr(QtWidgets, widgetClsName, None)
        if widgetCls is None:
            # For PySide6, some widget classes (e.g. QDesktopWidget) are deprecated and removed
            # If the class is not found, skip the patching to avoid exception
            # See: https://doc.qt.io/qt-6/widgets-changes-qt6.html
            pqi_log.info(f"Cannot find class {widgetClsName} in QtWidgets, skip patching.")
            continue
        widgetCls._original_QWidget_init = widgetCls.__init__
        widgetCls.__init__ = _new_QWidget_init
        widgetCls._pqi_exec = _pqi_exec

    if is_attach:
        _patch_old_widgets_when_attached()

    pqi_log.info(f"pid {os.getpid()} patched.")
    _notify_patch_success()
