# -*- encoding:utf-8 -*-
import collections
import sys
from contextlib import redirect_stdout
from ctypes import wintypes
from io import StringIO
import os

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger, QtWidgetClasses, IS_WINDOWS, IS_MACOS
from PyQtInspect._pqi_bundle.pqi_path_helper import find_pqi_module_path, is_relative_to
from PyQtInspect._pqi_bundle.pqi_qt_tools import get_widget_size
from PyQtInspect._pqi_bundle.pqi_stack_tools import getStackFrame
from PyQtInspect._pqi_bundle.pqi_log.log_utils import log_exception

_PQI_MOCKED_EVENT_ATTR = '_pqi_mocked'
_PQI_INSPECTED_PROP_NAME = '_pqi_inspected'
_PQI_INSPECTED_PROP_NAME_BYTES = b'_pqi_inspected'


def filter_trace_stack(traceStacks):
    filteredStacks = []
    from PyQtInspect.pqi import SetupHolder
    stackMaxDepth = SetupHolder.setup["stack-max-depth"]
    showPqiStack = SetupHolder.setup["show-pqi-stack"]
    pqi_module_path = find_pqi_module_path()
    stacks = traceStacks[2:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[2:]
    for filename, lineno, func_name in stacks:
        if not showPqiStack and is_relative_to(filename, pqi_module_path):
            break
        filteredStacks.append(
            {
                'filename': filename,
                'lineno': lineno,
                'function': func_name,
            }
        )
    return filteredStacks


def _is_inspect_enabled():
    debugger = get_global_debugger()
    return debugger is not None and debugger.inspect_enabled


def patch_QtWidgets(QtModule, qt_support_mode='auto', is_attach=False):
    QtWidgets = QtModule.QtWidgets
    QtGui = QtModule.QtGui
    QtCore = QtModule.QtCore

    EventEnum = QtCore.QEvent.Type if hasattr(QtCore.QEvent, 'Type') else QtCore.QEvent
    WidgetAttributeEnum = QtCore.Qt.WidgetAttribute if hasattr(QtCore.Qt, 'WidgetAttribute') else QtCore.Qt
    MouseButtonEnum = QtCore.Qt.MouseButton if hasattr(QtCore.Qt, 'MouseButton') else QtCore.Qt
    KeyboardModifierEnum = QtCore.Qt.KeyboardModifier if hasattr(QtCore.Qt, 'KeyboardModifier') else QtCore.Qt

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

    def _create_mouse_event(event_type, pos, button):
        """ Create a mouse event with the specified parameters.
        It is safe, because the event object created by Python is allocated on the heap.
        """
        return QtGui.QMouseEvent(event_type, QtCore.QPointF(pos), button, button, KeyboardModifierEnum.NoModifier)

    def _register_widget(widget):
        debugger = get_global_debugger()
        if debugger is not None:
            debugger.register_widget(widget)

    def _createHighlightFg(parent: QtWidgets.QWidget):
        # 先new再调用之前的__init__
        widget = QtWidgets.QWidget.__new__(QtWidgets.QWidget)
        QtWidgets.QWidget._original_QWidget_init(widget, parent)
        widget.setFixedSize(*get_widget_size(parent))
        # 不要响应鼠标事件
        widget.setAttribute(WidgetAttributeEnum.WA_TransparentForMouseEvents)
        widget.setObjectName("_pqi_highlight_fg")
        widget.setStyleSheet("background-color: rgba(255, 0, 0, 0.2);")
        return widget

    def _mark_obj_inspected(obj):
        setattr(obj, '_pqi_inspected_mark', True)

    def _clear_obj_inspected_mark(obj):
        if hasattr(obj, '_pqi_inspected_mark'):
            del obj._pqi_inspected_mark

    def _is_obj_inspected(obj):
        return hasattr(obj, '_pqi_inspected_mark')

    class HighlightController:
        last_highlighted_widget = None
        # for some widgets like QSplitter, we should not highlight them, or they will change their size
        widget_class_to_ignore = (
            QtWidgets.QSplitter,
        )

        @classmethod
        def _is_ignored(cls, widget):
            return any(isinstance(widget, class_) for class_ in cls.widget_class_to_ignore)

        @classmethod
        def unhighlight_last(cls):
            if cls.last_highlighted_widget is not None and not isdeleted(cls.last_highlighted_widget):
                cls.last_highlighted_widget.hide()
            cls.last_highlighted_widget = None

        @classmethod
        def highlight(cls, widget):
            if cls._is_ignored(widget):
                return

            if not hasattr(widget, '_pqi_highlight_fg'):
                widget._pqi_highlight_fg = _createHighlightFg(widget)

            widget._pqi_highlight_fg.setFixedSize(*get_widget_size(widget))
            cls.unhighlight_last()
            widget._pqi_highlight_fg.show()
            cls.last_highlighted_widget = widget._pqi_highlight_fg

        @classmethod
        def unhighlight(cls, widget):
            if hasattr(widget, '_pqi_highlight_fg'):
                widget._pqi_highlight_fg.hide()
                if cls.last_highlighted_widget is widget._pqi_highlight_fg:
                    cls.last_highlighted_widget = None

    class EnteredWidgetStack:
        def __init__(self):
            self._stack = []

        def push(self, widget):
            self._stack.append(widget)

        def pop(self):
            self._stack.pop()

        def filter(self):
            while self._stack:
                wgt = self._stack[-1]
                if isdeleted(wgt):
                    self._stack.pop()
                else:
                    break

        def clear(self):
            self._stack.clear()

        def __bool__(self):
            return bool(self._stack)

        def __getitem__(self, item):
            return self._stack[item]

        def __len__(self):
            return len(self._stack)

    _entered_widget_stack = EnteredWidgetStack()

    def _inspect_widget(debugger, widget: QtWidgets.QWidget):
        # print('inspect:', widget.__class__.__name__, widget.objectName(), widget)
        # === send widget info === #
        debugger.send_widget_info_to_server(widget)

        # === highlight widget === #
        HighlightController.highlight(widget)

        # === hook mouseReleaseEvent === #
        _mark_obj_inspected(widget)

    def _inspect_top(stack: EnteredWidgetStack):
        stack.filter()
        if not stack:
            return

        if not _is_inspect_enabled():
            return
        debugger = get_global_debugger()

        obj = stack[-1]

        _inspect_widget(debugger, obj)

    class EventListener(QtCore.QObject):

        def _handleEnterEvent(self, obj, event):
            if not _is_inspect_enabled():
                return

            if _entered_widget_stack:
                # 如果栈顶有元素, 则取消掉栈顶元素的选择状态
                # 否则QTabWidget会表现异常
                # todo 看看能不能集成在栈上, 毕竟两者强关联
                _clear_obj_inspected_mark(_entered_widget_stack[-1])
            _entered_widget_stack.push(obj)
            _inspect_top(_entered_widget_stack)

        def _handleLeaveEvent(self, obj, event):
            # 注意这个不对称
            # 因为leaveEvent是在鼠标离开时触发的, 但是鼠标离开时, 有可能鼠标已经进入了下一个widget
            # 所以不能直接pop
            if not _is_inspect_enabled():
                return

            if _entered_widget_stack and _entered_widget_stack[-1] == obj:
                _entered_widget_stack.pop()
            else:
                _entered_widget_stack.clear()

            HighlightController.unhighlight(obj)
            _clear_obj_inspected_mark(obj)

            _inspect_top(_entered_widget_stack)

        def _handleMouseReleaseEvent(self, obj, event) -> bool:
            """ 处理鼠标点击事件, 这里需要返回一个bool值, 表示是否拦截事件 """
            if not _is_inspect_enabled():
                return False

            # print(f'click: {obj}, button: {event.button()}')
            if not _is_obj_inspected(obj):
                return False

            # 自己通过postEvent发出的事件, 不处理
            # 不使用event.spontaneous()判断, 因为对于QTextBrowser的点击事件, spontaneous()返回False
            if getattr(event, _PQI_MOCKED_EVENT_ATTR, False):
                return False

            debugger = get_global_debugger()

            if event.button() != MouseButtonEnum.LeftButton:
                if debugger is not None and debugger.mock_left_button_down and event.button() == MouseButtonEnum.RightButton:
                    # mock left button press and release event
                    # First, send a mouse press event
                    pressEvent = _create_mouse_event(EventEnum.MouseButtonPress, event.pos(),
                                                     MouseButtonEnum.LeftButton)
                    # 使用postEvent传播事件, 而不是直接调用obj.mousePressEvent, 以便其他的eventFilter能够接收到这个事件
                    QtCore.QCoreApplication.postEvent(obj, pressEvent)

                    # Then, change the original event and send it again
                    event = _create_mouse_event(EventEnum.MouseButtonRelease, event.pos(), MouseButtonEnum.LeftButton)
                    setattr(event, _PQI_MOCKED_EVENT_ATTR, True)
                    # 同理, 为了能让后面的eventFilter能够接收到鼠标事件, 这里使用postEvent再次将事件传播出去
                    QtCore.QCoreApplication.postEvent(obj, event)
                    # stop event propagation
                    return True
                else:
                    # Bug Fixed 20240810: We CAN NOT re-post the original event,
                    # because it will be deleted after the event loop.
                    # see: https://doc.qt.io/qt-5/qcoreapplication.html#postEvent
                    # ---
                    # The event must be allocated on the heap
                    # since the post event queue will take ownership of the event
                    # and delete it once it has been posted.
                    # It is not safe to access the event after it has been posted.
                    # ---
                    # Note: all objects created in Python are allocated on the heap.
                    # see: https://docs.python.org/3/c-api/memory.html
                    # ---
                    return False

            # inspect finished
            debugger.notify_inspect_finished(obj)
            debugger.disable_inspect()
            HighlightController.unhighlight(obj)
            _entered_widget_stack.clear()
            _clear_obj_inspected_mark(obj)

            # stop event propagation
            return True

        def _handleMousePressEvent(self, obj, event):
            if not _is_inspect_enabled():
                return False
            # print(f'press: {obj}')
            if not event.spontaneous():
                return False
            if not _is_obj_inspected(obj):
                return False
            # obj.mousePressEvent(event)
            # 对于当前被检查的控件, 阻止MousePress事件传播
            # 防止点击后某些eventFilter在处理MousePress事件时使得inspect的控件改变, 导致后续的MouseRelease事件处理不正常
            return True

        def eventFilter(self, obj, event):
            # Intercept `QDynamicPropertyChange` events for properties dynamically
            # added by PyQtInspect itself (like `_pqi_inspected`).
            with log_exception(suppress=True):
                if (event.type() == EventEnum.DynamicPropertyChange
                        and bytes(event.propertyName()) == _PQI_INSPECTED_PROP_NAME_BYTES):
                    return True

                if not obj.property(_PQI_INSPECTED_PROP_NAME):
                    return False

                if event.type() == EventEnum.Enter:
                    self._handleEnterEvent(obj, event)
                elif event.type() == EventEnum.Leave:
                    self._handleLeaveEvent(obj, event)
                elif event.type() == EventEnum.MouseButtonPress:
                    return self._handleMousePressEvent(obj, event)
                elif event.type() == EventEnum.MouseButtonRelease:
                    return self._handleMouseReleaseEvent(obj, event)
                elif event.type() == EventEnum.User:
                    # handle enter & leave
                    if hasattr(event, '_pqi_is_enter'):
                        is_enter = event._pqi_is_enter
                        if is_enter:
                            self._handleEnterEvent(obj, event)
                        else:
                            self._handleLeaveEvent(obj, event)
                    # handle highlight
                    if hasattr(event, '_pqi_is_highlight'):
                        is_highlight = event._pqi_is_highlight
                        if is_highlight:
                            HighlightController.highlight(obj)
                        else:
                            HighlightController.unhighlight(obj)
                    # handle code exec
                    if hasattr(event, '_pqi_exec_code'):
                        code = event._pqi_exec_code
                        obj._pqi_exec(code)
            return False

    if IS_WINDOWS:
        class NativeEventListener(QtCore.QAbstractNativeEventFilter):
            """
            For some widgets that have overloaded the nativeEvent, mouse events may be intercepted earlier.
            Therefore, a NativeEventFilter needs to be implemented to prevent mouse events from being intercepted.
            """
            HTCLIENT = 1
            WM_NCHITTEST = 0x0084

            def nativeEventFilter(self, eventType, message):
                if not _is_inspect_enabled():
                    # If inspect is disabled, do not handle native events
                    return False, 0

                msg = wintypes.MSG.from_address(int(message))
                if msg.message == self.WM_NCHITTEST:
                    return True, self.HTCLIENT
                return False, 0
    elif IS_MACOS:
        class NativeEventListener(QtCore.QAbstractNativeEventFilter):
            """
            For macOS, when the window is not focused, the mouse event will not be triggered.
            Therefore, a NativeEventFilter needs to be implemented to obtain the mouse position
            and generate the corresponding enter and leave events.
            """
            __last_widget = None

            def nativeEventFilter(self, eventType, _):
                if not _is_inspect_enabled():
                    # If inspect is disabled, do not handle native events
                    return False, 0

                if eventType == 'mac_generic_NSEvent':
                    if QtGui.QGuiApplication.instance().focusWindow():
                        # If the window is focused, the event handle is not needed
                        self.__last_widget = None
                        return False, 0

                    locationInWindow = QtGui.QCursor.pos()
                    targetWidget = QtWidgets.QApplication.instance().widgetAt(locationInWindow)
                    if not targetWidget:
                        if self.__last_widget:
                            leaveEvent = QtCore.QEvent(EventEnum.User)
                            leaveEvent._pqi_is_enter = False
                            QtWidgets.QApplication.postEvent(self.__last_widget, leaveEvent)
                        self.__last_widget = None
                        return False, 0

                    if targetWidget != self.__last_widget:
                        # generate enter event
                        enterEvent = QtCore.QEvent(EventEnum.User)
                        enterEvent._pqi_is_enter = True
                        QtWidgets.QApplication.postEvent(targetWidget, enterEvent)
                        # generate leave event
                        if self.__last_widget:
                            leaveEvent = QtCore.QEvent(EventEnum.User)
                            leaveEvent._pqi_is_enter = False
                            QtWidgets.QApplication.postEvent(self.__last_widget, leaveEvent)
                        self.__last_widget = targetWidget
                return False, 0
    else:
        NativeEventListener = None

    def _initGlobalEventFilter():
        """ Initialize the global event filters when it does not exist """
        debugger = get_global_debugger()
        assert debugger is not None

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
        debugger = get_global_debugger()
        assert debugger is not None
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
            QtCore.QTimer.singleShot(0, lambda: obj.setProperty(_PQI_INSPECTED_PROP_NAME, True) if not isdeleted(
                obj) else None)
        else:
            # Attach thread may be different from the main thread,
            #   so the timer method will be invalid.
            # We just set the property directly because the widget has been initialized.
            obj.setProperty(_PQI_INSPECTED_PROP_NAME, True)
        # === register widget === #
        _register_widget(obj)

    def _new_QWidget_init(self, *args, **kwargs):
        self._original_QWidget_init(*args, **kwargs)
        if not ispycreated(self):
            # DO NOT install event listener for non-pycreated widget, because it may cause crash when exit
            return

        # === save stack when create === #
        frames = getStackFrame()
        setattr(self, '_pqi_stacks_when_create', frames)

        # Initialize the global filter when it does not exist
        _initGlobalEventFilter()

        # Patch widget
        _patchWidget(self)
        # Patch special widgets created by C++
        for specialMethod in ['viewport', 'tabBar', 'header']:
            if hasattr(self, specialMethod):
                p = getattr(self, specialMethod)
                if callable(p) and isinstance(p(), QtWidgets.QWidget):
                    for child in self.findChildren(QtWidgets.QWidget):
                        if not child.property(_PQI_INSPECTED_PROP_NAME):
                            _patchWidget(child)
                    break
        # for QAbstractSpinBox we should install event listener on its line edit
        if isinstance(self, QtWidgets.QAbstractSpinBox):
            _patchWidget(self.lineEdit())

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
        if _debugger is not None:
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

    # 对于PyQt, 仅需patch基类QWidget即可
    # 但对于PySide, 则需要给所有的QWidget子类都打上补丁
    classesToPatch = QtWidgetClasses if qt_support_mode.startswith('pyside') else ['QWidget']

    for widgetClsName in classesToPatch:
        widgetCls = getattr(QtWidgets, widgetClsName)
        widgetCls._original_QWidget_init = widgetCls.__init__
        widgetCls.__init__ = _new_QWidget_init
        widgetCls._pqi_exec = _pqi_exec

    if is_attach:
        _patch_old_widgets_when_attached()

    pqi_log.info(f"pid {os.getpid()} patched.")
    _notify_patch_success()
