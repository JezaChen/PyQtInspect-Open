# -*- encoding:utf-8 -*-
import collections
import inspect
from contextlib import redirect_stdout
from io import StringIO

from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger, QtWidgetClasses
from PyQtInspect._pqi_bundle.pqi_stack_tools import getStackFrame


def _try_get_file_name(frame):
    try:
        return inspect.getsourcefile(frame) or inspect.getfile(frame)
    except TypeError:
        return ''


def filter_trace_stack(traceStacks):
    filteredStacks = []
    from PyQtInspect.pqi import SetupHolder
    stackMaxDepth = SetupHolder.setup["stack-max-depth"]
    stacks = traceStacks[2:stackMaxDepth + 1] if stackMaxDepth != 0 else traceStacks[2:]
    for frame, lineno in stacks:
        filteredStacks.append(
            {
                'filename': _try_get_file_name(frame),
                'lineno': lineno,
                'function': frame.f_code.co_name,
            }
        )
    return filteredStacks


def patch_QtWidgets(QtWidgets, QtCore, QtGui, qt_support_mode='auto', is_attach=False):
    if qt_support_mode.startswith("pyqt"):
        import sip
        isdeleted = sip.isdeleted
        ispycreated = sip.ispycreated
    elif qt_support_mode.startswith("pyside"):  # todo pyside6 also use this?
        import shiboken2  # todo: or shiboken?
        isdeleted = lambda obj: not shiboken2.isValid(obj)
        ispycreated = shiboken2.createdByPython

    def _create_mouse_event(event_type, pos, button):
        return QtGui.QMouseEvent(event_type, pos, button, button, QtCore.Qt.NoModifier)

    def _register_widget(widget):
        debugger = get_global_debugger()
        if debugger is not None:
            debugger.register_widget(widget)

    def _createHighlightFg(parent: QtWidgets.QWidget):
        # 先new再调用之前的__init__
        widget = QtWidgets.QWidget.__new__(QtWidgets.QWidget)
        QtWidgets.QWidget._original_QWidget_init(widget, parent)
        widget.setFixedSize(parent.size())
        # 不要响应鼠标事件
        widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        widget.setObjectName("_pqi_highlight_fg")
        widget.setStyleSheet("background-color: rgba(255, 0, 0, 0.2);")
        return widget

    def _hook_mouseReleaseEvent(obj):
        if not hasattr(obj.mouseReleaseEvent, '_pqi_hooked'):
            obj._oldMouseReleaseEvent = obj.mouseReleaseEvent

        def _newMouseReleaseEvent(event):
            debugger = get_global_debugger()
            if debugger is None or not debugger.inspect_enabled:
                return obj._oldMouseReleaseEvent(event)

            if event.button() != QtCore.Qt.LeftButton:
                if debugger is not None and debugger.mock_left_button_down and event.button() == QtCore.Qt.RightButton:
                    # mock left button press and release event
                    obj.mousePressEvent(
                        _create_mouse_event(QtCore.QEvent.MouseButtonPress, event.pos(), QtCore.Qt.LeftButton)
                    )
                    event = _create_mouse_event(QtCore.QEvent.MouseButtonRelease, event.pos(), QtCore.Qt.LeftButton)
                return obj._oldMouseReleaseEvent(event)

            debugger.notify_inspect_finished(obj)
            HighlightController.unhighlight(obj)
            _entered_widget_stack.clear()
            obj.mouseReleaseEvent = obj._oldMouseReleaseEvent

        setattr(_newMouseReleaseEvent, '_pqi_hooked', True)

        obj.mouseReleaseEvent = _newMouseReleaseEvent

    def _unhook_mouseReleaseEvent(obj):
        if hasattr(obj, '_oldMouseReleaseEvent'):
            obj.mouseReleaseEvent = obj._oldMouseReleaseEvent
            del obj._oldMouseReleaseEvent

    class HighlightController:
        last_highlighted_widget = None

        @classmethod
        def unhighlight_last(cls):
            if cls.last_highlighted_widget is not None and not isdeleted(cls.last_highlighted_widget):
                cls.last_highlighted_widget.hide()
            cls.last_highlighted_widget = None

        @classmethod
        def highlight(cls, widget):
            if not hasattr(widget, '_pqi_highlight_fg'):
                widget._pqi_highlight_fg = _createHighlightFg(widget)

            widget._pqi_highlight_fg.setFixedSize(widget.size())
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

    _entered_widget_stack = EnteredWidgetStack()

    def _inspect_widget(debugger, widget: QtWidgets.QWidget):
        # === send widget info === #
        debugger.send_widget_info_to_server(widget)

        # === highlight widget === #
        HighlightController.highlight(widget)

        # === hook mouseReleaseEvent === #
        _hook_mouseReleaseEvent(widget)

    def _inspect_top(stack: EnteredWidgetStack):
        stack.filter()
        if not stack:
            return

        debugger = get_global_debugger()
        if debugger is None or not debugger.inspect_enabled:
            return

        obj = stack[-1]

        _inspect_widget(debugger, obj)

    class EventListener(QtCore.QObject):
        def _handleEnterEvent(self, obj, event):
            _entered_widget_stack.push(obj)
            _inspect_top(_entered_widget_stack)

        def _handleLeaveEvent(self, obj, event):
            # 注意这个不对称
            # 因为leaveEvent是在鼠标离开时触发的, 但是鼠标离开时, 有可能鼠标已经进入了下一个widget
            # 所以不能直接pop

            if _entered_widget_stack and _entered_widget_stack[-1] == obj:
                _entered_widget_stack.pop()

            HighlightController.unhighlight(obj)
            _unhook_mouseReleaseEvent(obj)

            _inspect_top(_entered_widget_stack)

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
                        HighlightController.highlight(obj)
                    else:
                        HighlightController.unhighlight(obj)
                # handle code exec
                if hasattr(event, '_pqi_exec_code'):
                    code = event._pqi_exec_code
                    obj._pqi_exec(code)
            return False

    def _new_QWidget_init(self, *args, **kwargs):
        self._original_QWidget_init(*args, **kwargs)
        if not ispycreated(self):
            # DO NOT install event listener for non-pycreated widget, because it may cause crash when exit
            return

        # === save stack when create === #
        frames = getStackFrame()
        setattr(self, '_pqi_stacks_when_create', frames)

        # === install event listener === #
        self._pqi_event_listener = EventListener()
        self.installEventFilter(self._pqi_event_listener)

        # === register widget === #
        _register_widget(self)

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
        topLevelWidgets = QtWidgets.QApplication.topLevelWidgets()
        widgetsToPatch = collections.deque(topLevelWidgets)
        while widgetsToPatch:  # BFS traverse
            widget = widgetsToPatch.popleft()

            if isdeleted(widget) or not ispycreated(widget):
                continue

            event_listener = EventListener()
            # We must move the event listener to the thread of the widget during attach
            event_listener.moveToThread(widget.thread())
            widget._pqi_event_listener = event_listener
            widget.installEventFilter(widget._pqi_event_listener)

            # === register widget === #
            _register_widget(widget)

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

    print("<patched>...")
    _notify_patch_success()

