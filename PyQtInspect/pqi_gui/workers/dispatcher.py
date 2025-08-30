# -*- encoding:utf-8 -*-
# A dispatcher is a class that can be used to send and receive messages between pqi-server and single pqi-client.

from PyQt5 import QtCore
import threading

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread, WriterThread, NetCommandFactory
from PyQtInspect._pqi_bundle.pqi_override import overrides
from PyQtInspect._pqi_bundle.pqi_typing import OptionalDict


class DispatchReader(ReaderThread):
    def __init__(self, dispatcher):
        ReaderThread.__init__(self, dispatcher.sock)
        self.dispatcher = dispatcher

    @overrides(ReaderThread._on_run)
    def _on_run(self):
        dummy_thread = threading.current_thread()
        dummy_thread.is_pydev_daemon_thread = False
        return ReaderThread._on_run(self)

    def handle_except(self):
        self.dispatcher.notifyDelete()

    def process_command(self, cmd_id, seq, text):
        # unquote text
        from urllib.parse import unquote
        text = unquote(text)
        self.dispatcher.notify(cmd_id, seq, text)


class Dispatcher(QtCore.QThread):
    sigMsg = QtCore.pyqtSignal(int, dict)  # dispatcher_id, info
    sigClosed = QtCore.pyqtSignal(int)

    def __init__(self, parent, sock, id):
        super().__init__(parent)
        self.sock = sock
        self.id = id
        self.net_command_factory = NetCommandFactory()
        self.reader = None
        self.writer = None

        # Since when the dispatcher is just created, the main UI is not ready to handle immediately incoming messages (PQYWorker has not emitted the new dispatcher creation signal)
        # So it needs to be processed after the main UI is ready
        # Messages before this are cached
        self._mainUIReady = False
        self._msg_buffer = []

    def run(self):
        self.writer = WriterThread(self.sock)
        self.writer.pydev_do_not_trace = False  # We run writer in the same thread so we don't want to loose tracing.
        self.writer.start()

        self.reader = DispatchReader(self)
        self.reader.pydev_do_not_trace = False  # We run reader in the same thread so we don't want to loose tracing.
        self.reader.run()

    def close(self):
        try:
            self.writer.do_kill_pydev_thread()
            self.reader.do_kill_pydev_thread()
            self.sock.close()
        except:
            pass
        self.sigClosed.emit(self.id)

    def registerMainUIReady(self):
        """ The Main UI is ready and we can start processing messages.
        """
        self._mainUIReady = True
        for cmd_id, seq, text in self._msg_buffer:
            self.notify(cmd_id, seq, text)
        self._msg_buffer.clear()

    def notify(self, cmd_id, seq, text):
        if not self._mainUIReady:
            # Not ready yet, buffer the message.
            self._msg_buffer.append((cmd_id, seq, text))
        self.sigMsg.emit(self.id, {"cmd_id": cmd_id, "seq": seq, "text": text})

    def sendEnableInspect(self, extra: dict):
        self.writer.add_command(self.net_command_factory.make_enable_inspect_message(extra))

    def sendDisableInspect(self):
        self.writer.add_command(self.net_command_factory.make_disable_inspect_message())

    def sendExecCodeEvent(self, code: str):
        self.writer.add_command(self.net_command_factory.make_exec_code_message(code))

    def sendHighlightWidgetEvent(self, widgetId: int, isHighlight: bool):
        self.writer.add_command(self.net_command_factory.make_set_widget_highlight_message(widgetId, isHighlight))

    def sendSelectWidgetEvent(self, widgetId: int):
        self.writer.add_command(self.net_command_factory.make_select_widget_message(widgetId))

    def sendRequestWidgetInfoEvent(self, widgetId: int, extra: OptionalDict = None):
        self.writer.add_command(self.net_command_factory.make_req_widget_info_message(widgetId, extra))

    def sendRequestChildrenInfoEvent(self, widgetId: int):
        self.writer.add_command(self.net_command_factory.make_req_children_info_message(widgetId))

    def sendRequestControlTreeInfoEvent(self, extra: OptionalDict = None):
        self.writer.add_command(self.net_command_factory.make_req_control_tree_message(extra))

    def sendRequestWidgetPropsEvent(self, widgetId: int):
        self.writer.add_command(self.net_command_factory.make_req_widget_props_message(widgetId))

    def notifyDelete(self):
        self.close()
