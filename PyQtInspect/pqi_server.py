# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/24 16:13
# Description: 
# ==============================================
import sys
import threading
import traceback
from socket import socket, AF_INET, SOCK_STREAM
from ssl import SOL_SOCKET

from _socket import SO_REUSEADDR

from PyQtInspect._pqi_bundle.pqi_comm import ReaderThread
from PyQtInspect._pqi_bundle.pqi_override import overrides
from PyQtInspect.pqi import start_server


class Dispatcher(object):
    def __init__(self, sock):
        self.sock = sock

    def run(self):
        self.reader = DispatchReader(self)
        self.reader.pydev_do_not_trace = False  # We run reader in the same thread so we don't want to loose tracing.
        self.reader.run()

    def close(self):
        try:
            self.reader.do_kill_pydev_thread()
        except:
            pass


class DispatchReader(ReaderThread):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        ReaderThread.__init__(self, self.dispatcher.sock)

    @overrides(ReaderThread._on_run)
    def _on_run(self):
        dummy_thread = threading.current_thread()
        dummy_thread.is_pydev_daemon_thread = False
        return ReaderThread._on_run(self)

    def handle_except(self):
        ReaderThread.handle_except(self)

    def process_command(self, cmd_id, seq, text):
        # unquote text
        from urllib.parse import unquote
        text = unquote(text)
        print(cmd_id, seq, text)


def main(port: int):
    dispatchers = []
    threads = []

    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(None)

    try:
        from socket import SO_REUSEPORT
        s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
    except ImportError:
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    s.bind(('', port))
    s.listen(1)

    try:
        while True:
            newSock, _addr = s.accept()
            # 新建个线程来处理
            dispatcher = Dispatcher(newSock)
            t = threading.Thread(target=dispatcher.run)
            t.setDaemon(True)
            t.start()
            dispatchers.append(dispatcher)
            threads.append(t)

    except:
        sys.stderr.write("Could not bind to port: %s\n" % (port,))
        sys.stderr.flush()
        traceback.print_exc()


if __name__ == '__main__':
    main(19394)
