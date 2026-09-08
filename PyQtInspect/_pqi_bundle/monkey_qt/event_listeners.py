# Just make the event listener class by injecting the qt_module, so that it can be used in both PyQt and PySide.

from PyQtInspect._pqi_bundle.monkey_qt.shared.shared_tools import is_inspect_enabled, is_widget_inspected, \
    is_widget_patched, clear_widget_inspected_mark, mark_widget_inspected
from PyQtInspect._pqi_bundle.monkey_qt.widget_patching.enter_widget_stack import EnteredWidgetStack
from PyQtInspect._pqi_bundle.pqi_contants import get_global_debugger, IS_WINDOWS, IS_MACOS
from PyQtInspect._pqi_bundle.pqi_log.log_utils import log_exception
from PyQtInspect._pqi_bundle.monkey_qt.metadata import (
    _PQI_MOCKED_EVENT_ATTR,
    _PQI_INSPECTED_PROP_NAME_BYTES,
    _PQI_CUSTOM_EVENT_IS_ENTER_ATTR,
    _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR,
    _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR,
    _PQI_CUSTOM_EVENT_DISABLE_INSPECT_ATTR,
)


def make_qt_event_listener_cls(
    qt_module,
    enter_widget_stack,
    detailed_inspect_tooltip_mgr,
    highlighter,
):
    QtWidgets = qt_module.QtWidgets
    QtGui = qt_module.QtGui
    QtCore = qt_module.QtCore

    EventEnum = QtCore.QEvent.Type
    MouseButtonEnum = QtCore.Qt.MouseButton
    KeyboardModifierEnum = QtCore.Qt.KeyboardModifier
    QContextMenuEventReasonEnum = QtGui.QContextMenuEvent.Reason

    def _create_mouse_event(event_type, pos, button):
        """ Create a mouse event with the specified parameters.
        It is safe, because the event object created by Python is allocated on the heap.
        """
        return QtGui.QMouseEvent(event_type, QtCore.QPointF(pos), button, button, KeyboardModifierEnum.NoModifier)

    def _inspect_top(stack: EnteredWidgetStack):
        # todo move to EnteredWidgetStack class
        stack.filter()
        if not stack:
            return

        if not is_inspect_enabled():
            return

        obj = stack[-1]
        _inspect_widget(obj)

    def _inspect_widget(widget: QtWidgets.QWidget):
        # todo move
        debugger = get_global_debugger()

        # print('inspect:', widget.__class__.__name__, widget.objectName(), widget)
        # === save widget ===
        debugger.set_hovered_widget(widget)

        # === send widget info === #
        debugger.send_widget_info_to_server(widget)

        # === highlight widget === #
        highlighter.highlight(widget)

        # === populate detailed inspect tooltip === #
        detailed_inspect_tooltip_mgr.show_tooltip(widget)

        # === hook mouseReleaseEvent === #
        mark_widget_inspected(widget)

    class EventListener(QtCore.QObject):

        def _handleEnterEvent(self, obj, event):
            if not is_inspect_enabled():
                return

            if enter_widget_stack:
                # If the stack has elements, clear the selected state of the widget on top.
                # Otherwise QTabWidget behaves abnormally.
                # TODO: Investigate whether this logic can be integrated into the stack, as they are tightly coupled.
                clear_widget_inspected_mark(enter_widget_stack[-1])
            enter_widget_stack.push(obj)
            _inspect_top(enter_widget_stack)

        def _handleLeaveEvent(self, obj, event):
            # Note the asymmetry:
            # leaveEvent is triggered when the cursor leaves, but at that moment it may already have entered the next widget,
            # so we cannot simply pop.
            if not is_inspect_enabled():
                return

            if enter_widget_stack and enter_widget_stack[-1] == obj:
                enter_widget_stack.pop()
            else:
                enter_widget_stack.clear()

            if len(enter_widget_stack) == 0:
                # no inspected widgets, hide the tooltip
                detailed_inspect_tooltip_mgr.hide_tooltip()

            highlighter.unhighlight(obj)
            clear_widget_inspected_mark(obj)

            _inspect_top(enter_widget_stack)

        def _handleMouseReleaseEvent(self, obj, event) -> bool:
            """Handle mouse click events and return whether to intercept them."""
            if not is_inspect_enabled():
                return False

            # print(f'click: {obj}, button: {event.button()}')
            if not is_widget_inspected(obj):
                return False

            # Ignore events posted by ourselves.
            # Do not rely on event.spontaneous(), because for QTextBrowser click events it returns False.
            if getattr(event, _PQI_MOCKED_EVENT_ATTR, False):
                return False

            debugger = get_global_debugger()

            if event.button() != MouseButtonEnum.LeftButton:
                if debugger.mock_left_button_down and event.button() == MouseButtonEnum.RightButton:
                    # mock left button press and release event
                    # First, send a mouse press event
                    pressEvent = _create_mouse_event(EventEnum.MouseButtonPress, event.pos(),
                                                     MouseButtonEnum.LeftButton)
                    # Propagate the event with postEvent instead of calling obj.mousePressEvent directly,
                    # so that other event filters can receive it.
                    QtCore.QCoreApplication.postEvent(obj, pressEvent)

                    # Then, change the original event and send it again
                    event = _create_mouse_event(EventEnum.MouseButtonRelease, event.pos(), MouseButtonEnum.LeftButton)
                    setattr(event, _PQI_MOCKED_EVENT_ATTR, True)
                    # Similarly, propagate the event again via postEvent so that subsequent event filters can process it.
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
            debugger.finish_select(obj)
            debugger.stop_select()
            highlighter.unhighlight(obj)
            enter_widget_stack.clear()
            clear_widget_inspected_mark(obj)
            detailed_inspect_tooltip_mgr.hide_tooltip()

            # stop event propagation
            return True

        def _handleMousePressEvent(self, obj, event):
            if not is_inspect_enabled():
                return False
            # print(f'press: {obj}')
            if not event.spontaneous():
                return False
            if not is_widget_inspected(obj):
                return False
            # obj.mousePressEvent(event)
            # For the widget currently under inspection, block MousePress propagation.
            # This prevents other event filters from changing the inspected widget during MousePress handling,
            # which would disrupt the subsequent MouseRelease processing.
            return True

        def _handleCustomEvent(self, obj, event):
            # handle enter & leave
            if hasattr(event, _PQI_CUSTOM_EVENT_IS_ENTER_ATTR):
                is_enter = getattr(event, _PQI_CUSTOM_EVENT_IS_ENTER_ATTR)
                if is_enter:
                    self._handleEnterEvent(obj, event)
                else:
                    self._handleLeaveEvent(obj, event)
            # handle highlight
            if hasattr(event, _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR):
                is_highlight = getattr(event, _PQI_CUSTOM_EVENT_IS_HIGHLIGHT_ATTR)

                if is_highlight:
                    highlighter.highlight(obj)
                else:
                    highlighter.unhighlight(obj)
            # handle code exec
            if hasattr(event, _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR):
                code = getattr(event, _PQI_CUSTOM_EVENT_EXEC_CODE_ATTR)
                obj._pqi_exec(code)
            # handle inspect disabled
            if hasattr(event, _PQI_CUSTOM_EVENT_DISABLE_INSPECT_ATTR):
                # no need call debugger.stop_select() here,
                # because this event is sent by the debugger
                enter_widget_stack.clear()
                detailed_inspect_tooltip_mgr.hide_tooltip()

        def _handleContextMenuEvent(self, obj, event):
            """ #1 https://github.com/JezaChen/PyQtInspect-Open/issues/1
            When mocking right-click is enabled,
            we need to prevent the context menu from popping up when user right-clicks on the widget.
            """
            if not is_inspect_enabled():
                return False
            if not is_widget_inspected(obj):
                return False
            if hasattr(event, 'reason') and event.reason() != QContextMenuEventReasonEnum.Mouse:
                # If the context menu is not triggered by the mouse, do not intercept
                return False
            debugger = get_global_debugger()
            # Prevent the context menu from popping up
            return debugger.mock_left_button_down

        def eventFilter(self, obj, event):
            # Intercept `QDynamicPropertyChange` events for properties dynamically
            # added by PyQtInspect itself (like `_pqi_inspected`).

            with log_exception(suppress=True):
                if (event.type() == EventEnum.DynamicPropertyChange
                    and bytes(event.propertyName()) == _PQI_INSPECTED_PROP_NAME_BYTES):
                    return True

                if not is_widget_patched(obj):
                    return False

                if event.type() == EventEnum.Enter:
                    self._handleEnterEvent(obj, event)
                elif event.type() == EventEnum.Leave:
                    self._handleLeaveEvent(obj, event)
                elif event.type() == EventEnum.MouseButtonPress:
                    return self._handleMousePressEvent(obj, event)
                elif event.type() == EventEnum.MouseButtonRelease:
                    return self._handleMouseReleaseEvent(obj, event)
                elif event.type() == EventEnum.ContextMenu:
                    return self._handleContextMenuEvent(obj, event)
                elif event.type() == EventEnum.User:
                    self._handleCustomEvent(obj, event)
            return False

    return EventListener


def make_native_event_listener_cls(qt_module):
    QtWidgets = qt_module.QtWidgets
    QtGui = qt_module.QtGui
    QtCore = qt_module.QtCore

    EventEnum = QtCore.QEvent.Type

    if IS_WINDOWS:
        class NativeEventListener(QtCore.QAbstractNativeEventFilter):
            """
            For some widgets that have overloaded the nativeEvent, mouse events may be intercepted earlier.
            Therefore, a NativeEventFilter needs to be implemented to prevent mouse events from being intercepted.
            """
            HTCLIENT = 1
            WM_NCHITTEST = 0x0084

            def nativeEventFilter(self, eventType, message):
                if not is_inspect_enabled():
                    # If inspect is disabled, do not filter native events
                    return False, 0

                from ctypes import wintypes
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
                if not is_inspect_enabled():
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

    return NativeEventListener
