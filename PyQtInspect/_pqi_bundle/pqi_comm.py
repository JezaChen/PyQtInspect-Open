# -*- encoding:utf-8 -*-

import dataclasses

import queue
import threading
import time
import socket
import typing
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RD, SHUT_WR, SOL_SOCKET, SO_REUSEADDR

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_contants import DebugInfoHolder, IS_PY2, GlobalDebuggerHolder, get_global_debugger, \
    set_global_debugger
from PyQtInspect._pqi_bundle.pqi_override import overrides
import json

from PyQtInspect._pqi_bundle.pqi_structures import QWidgetInfo, QWidgetChildrenInfo
from PyQtInspect._pqi_bundle.pqi_typing import OptionalDict

try:
    from urllib import quote_plus, unquote, unquote_plus
except:
    from urllib.parse import quote_plus, unquote, unquote_plus  # @Reimport @UnresolvedImport

import sys
import traceback
from urllib.parse import quote

try:
    import cStringIO as StringIO  # may not always be available @UnusedImport
except:
    try:
        import StringIO  # @Reimport
    except:
        import io as StringIO

# CMD_XXX constants imported for backward compatibility
from PyQtInspect._pqi_bundle.pqi_comm_constants import (
    ID_TO_MEANING, CMD_EXIT, CMD_WIDGET_INFO, CMD_ENABLE_INSPECT,
    CMD_DISABLE_INSPECT, CMD_INSPECT_FINISHED, CMD_EXEC_CODE, CMD_EXEC_CODE_ERROR, CMD_EXEC_CODE_RESULT,
    CMD_SET_WIDGET_HIGHLIGHT, CMD_SELECT_WIDGET, CMD_REQ_WIDGET_INFO, CMD_REQ_CHILDREN_INFO, CMD_CHILDREN_INFO,
    CMD_REQ_CONTROL_TREE, CMD_CONTROL_TREE, CMD_REQ_WIDGET_PROPS, CMD_WIDGET_PROPS,
    # Keys
    TreeViewResultKeys
)

MAX_IO_MSG_SIZE = 1000  # if the io is too big, we'll not send all (could make the debugger too non-responsive)
# this number can be changed if there's need to do so

VERSION_STRING = "@@BUILD_NUMBER@@"


class CommunicationRole:
    """The class that contains the constants of roles that `PyDB` can play in
    the communication with the IDE.
    """
    CLIENT = 0
    SERVER = 1


# ------------------------------------------------------------------- ACTUAL COMM

# =======================================================================================================================
# PyDBDaemonThread
# =======================================================================================================================
class PyDBDaemonThread(threading.Thread):
    created_pydb_daemon_threads = {}

    def __init__(self, target_and_args=None):
        '''
        :param target_and_args:
            tuple(func, args, kwargs) if this should be a function and args to run.
            -- Note: use through run_as_pydevd_daemon_thread().
        '''
        threading.Thread.__init__(self)
        self.killReceived = False
        mark_as_pydevd_daemon_thread(self)
        self._target_and_args = target_and_args

    def run(self):
        created_pydb_daemon = self.created_pydb_daemon_threads
        created_pydb_daemon[self] = 1
        try:
            try:
                self._stop_trace()
                self._warn_pydevd_thread_is_traced()
                self._on_run()
            except:
                if sys is not None and traceback is not None:
                    traceback.print_exc()
        finally:
            del created_pydb_daemon[self]

    def _on_run(self):
        if self._target_and_args is not None:
            target, args, kwargs = self._target_and_args
            target(*args, **kwargs)
        else:
            raise NotImplementedError('Should be reimplemented by: %s' % self.__class__)

    def do_kill_pydev_thread(self):
        self.killReceived = True

    def _stop_trace(self):
        return
        # if self.pydev_do_not_trace:
        #     pydevd_tracing.SetTrace(None)  # no debugging on this thread

    def _warn_pydevd_thread_is_traced(self):
        if self.pydev_do_not_trace and sys.gettrace():
            pqi_log.info("The debugger thread '%s' is traced which may lead to debugging performance issues." % self.__class__.__name__)


def mark_as_pydevd_daemon_thread(thread):
    thread.pydev_do_not_trace = True
    thread.is_pydev_daemon_thread = True
    thread.daemon = True


def run_as_pydevd_daemon_thread(func, *args, **kwargs):
    '''
    Runs a function as a pydevd daemon thread (without any tracing in place).
    '''
    t = PyDBDaemonThread(target_and_args=(func, args, kwargs))
    t.name = '%s (pydevd daemon thread)' % (func.__name__,)
    t.start()
    return t


# =======================================================================================================================
# ReaderThread
# =======================================================================================================================
class ReaderThread(PyDBDaemonThread):
    """ reader thread reads and dispatches commands in an infinite loop """

    def __init__(self, sock):
        PyDBDaemonThread.__init__(self)
        self.sock = sock
        self.name = "pydevd.Reader"
        self.global_debugger_holder = GlobalDebuggerHolder

    def do_kill_pydev_thread(self):
        # We must close the socket so that it doesn't stay halted there.
        self.killReceived = True
        try:
            self.sock.shutdown(SHUT_RD)  # shutdown the socket for read
        except:
            # just ignore that
            pass

    @overrides(PyDBDaemonThread._on_run)
    def _on_run(self):
        read_buffer = ""
        try:

            while not self.killReceived:
                try:
                    r = self.sock.recv(1024)
                except:
                    if not self.killReceived:
                        traceback.print_exc()
                        self.handle_except()
                    return  # Finished communication.

                # Note: the java backend is always expected to pass utf-8 encoded strings. We now work with unicode
                # internally and thus, we may need to convert to the actual encoding where needed (i.e.: filenames
                # on python 2 may need to be converted to the filesystem encoding).
                if hasattr(r, 'decode'):
                    r = r.decode('utf-8')

                read_buffer += r
                if DebugInfoHolder.DEBUG_RECORD_SOCKET_READS:
                    pqi_log.debug('PyQtInspect: received >>%s<<' % (read_buffer,))

                if len(read_buffer) == 0:
                    self.handle_except()
                    break
                while read_buffer.find(u'\n') != -1:
                    command, read_buffer = read_buffer.split(u'\n', 1)

                    args = command.split(u'\t', 2)
                    try:
                        cmd_id = int(args[0])
                        pqi_log.debug('Received command: %s %s\n' % (ID_TO_MEANING.get(str(cmd_id), '???'), command,))
                        self.process_command(cmd_id, int(args[1]), args[2])
                    except:
                        traceback.print_exc()
                        pqi_log.error("Can't process net command: %s" % command)

        except:
            traceback.print_exc()
            self.handle_except()

    def handle_except(self):
        self.global_debugger_holder.global_dbg.finish_debugging_session()

    def process_command(self, cmd_id, seq, text):
        self.process_net_command(self.global_debugger_holder.global_dbg, cmd_id, seq, text)

    def process_net_command(self, global_dbg, cmd_id, seq, text):
        if global_dbg is None:
            return
        if cmd_id == CMD_ENABLE_INSPECT:
            extra = json.loads(unquote(text))
            global_dbg.enable_inspect(extra)
        elif cmd_id == CMD_DISABLE_INSPECT:
            global_dbg.disable_inspect()
        elif cmd_id == CMD_EXEC_CODE:
            code = unquote(text)
            global_dbg.exec_code_in_selected_widget(code)
        elif cmd_id == CMD_SET_WIDGET_HIGHLIGHT:
            jsonMsg = json.loads(unquote(text))
            widget_id, is_highlight = jsonMsg['widget_id'], jsonMsg['is_highlight']
            global_dbg.set_widget_highlight_by_id(widget_id, is_highlight)
        elif cmd_id == CMD_SELECT_WIDGET:
            widget_id = int(unquote(text))
            global_dbg.select_widget_by_id(widget_id)
        elif cmd_id == CMD_REQ_WIDGET_INFO:
            jsonMsg = json.loads(unquote(text))
            widget_id, extra = jsonMsg['widget_id'], jsonMsg['extra']
            global_dbg.notify_widget_info(widget_id, extra)
        elif cmd_id == CMD_REQ_CHILDREN_INFO:
            widget_id = int(unquote(text))
            global_dbg.notify_children_info(widget_id)
        elif cmd_id == CMD_REQ_CONTROL_TREE:
            extra = json.loads(unquote(text))
            global_dbg.notify_control_tree(extra)
        elif cmd_id == CMD_REQ_WIDGET_PROPS:
            widget_id = int(unquote(text))
            global_dbg.notify_widget_props(widget_id)



# ----------------------------------------------------------------------------------- SOCKET UTILITIES - WRITER
# =======================================================================================================================
# WriterThread
# =======================================================================================================================
class WriterThread(PyDBDaemonThread):
    """ writer thread writes out the commands in an infinite loop """

    def __init__(self, sock):
        PyDBDaemonThread.__init__(self)
        self.sock = sock
        self.name = "pydevd.Writer"
        self.cmdQueue = queue.Queue()
        self.timeout = 0

    def add_command(self, cmd):
        """ cmd is NetCommand """
        if not self.killReceived:  # we don't take new data after everybody die
            self.cmdQueue.put(cmd)

    @overrides(PyDBDaemonThread._on_run)
    def _on_run(self):
        """ just loop and write responses """

        try:
            while True:
                try:
                    try:
                        cmd = self.cmdQueue.get(1, 0.1)
                    except queue.Empty:
                        if self.killReceived:
                            try:
                                self.sock.shutdown(SHUT_WR)
                                self.sock.close()
                            except:
                                pass

                            return  # break if queue is empty and killReceived
                        else:
                            continue
                except:
                    # pqi_log.info('Finishing debug communication...(1)')
                    # when liberating the thread here, we could have errors because we were shutting down
                    # but the thread was still not liberated
                    return
                cmd.send(self.sock)

                if cmd.id == CMD_EXIT:
                    break
                if time is None:
                    break  # interpreter shutdown
                time.sleep(self.timeout)
        except Exception:
            GlobalDebuggerHolder.global_dbg.finish_debugging_session()
            pqi_log.error('Error in writer thread', exc_info=True)

    def empty(self):
        return self.cmdQueue.empty()


# --------------------------------------------------- CREATING THE SOCKET THREADS

# =======================================================================================================================
# start_server
# =======================================================================================================================
def start_server(port, *, output_errors=True):
    """ binds to a port, waits for the debugger to connect """
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(None)

    try:
        from socket import SO_REUSEPORT
        s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
    except ImportError:
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    s.bind(('', port))
    pqi_log.info("Bound to port " + str(port))

    try:
        s.listen(1)
        newSock, _addr = s.accept()
        pqi_log.info(1, "Connection accepted")
        # closing server socket is not necessary but we don't need it
        # s.shutdown(SHUT_RDWR)  # todo?
        s.close()
        return newSock

    except:
        if output_errors:
            pqi_log.error("Could not bind to port: %s" % (port,))
        traceback.print_exc()


# =======================================================================================================================
# start_client
# =======================================================================================================================
def start_client(host, port, *, output_errors=True):
    """ connects to a host/port """
    pqi_log.info(f"Connecting to {host}:{port}")

    s = socket(AF_INET, SOCK_STREAM)
    # Set inheritable for Python >= 3.4. See https://docs.python.org/3/library/os.html#fd-inheritance.
    # It fixes issues: PY-37960 and PY-14980, also https://github.com/tornadoweb/tornado/issues/2243
    if hasattr(s, 'set_inheritable'):
        s.set_inheritable(True)

    #  Set TCP keepalive on an open socket.
    #  It activates after 1 second (TCP_KEEPIDLE,) of idleness,
    #  then sends a keepalive ping once every 3 seconds (TCP_KEEPINTVL),
    #  and closes the connection after 5 failed ping (TCP_KEEPCNT), or 15 seconds
    try:
        from socket import IPPROTO_TCP, SO_KEEPALIVE, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
        s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
        s.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, 1)
        s.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, 3)
        s.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, 5)
    except ImportError:
        pass  # May not be available everywhere.

    try:
        s.settimeout(10)  # 10 seconds timeout
        s.connect((host, port))
        s.settimeout(None)  # no timeout after connected
        pqi_log.info("Connected.")
        return s
    except:
        if output_errors:
            pqi_log.error(f'Could not connect to {host}:{port}', exc_info=True)
        raise


# ------------------------------------------------------------------------------------ MANY COMMUNICATION STUFF

# =======================================================================================================================
# NetCommand
# =======================================================================================================================
class NetCommand:
    """ Commands received/sent over the network.

    Command can represent command received from the debugger,
    or one to be sent by daemon.
    """
    next_seq = 0  # sequence numbers

    # Protocol where each line is a new message (text is quoted to prevent new lines).
    QUOTED_LINE_PROTOCOL = 'quoted-line'

    # Uses http protocol to provide a new message.
    # i.e.: Content-Length:xxx\r\n\r\npayload
    HTTP_PROTOCOL = 'http'

    protocol = QUOTED_LINE_PROTOCOL

    _showing_debug_info = 0
    _show_debug_info_lock = threading.RLock()

    def __init__(self, cmd_id, seq, text):
        """
        If sequence is 0, new sequence will be generated (otherwise, this was the response
        to a command from the client).
        """
        self.id = cmd_id
        if seq == 0:
            NetCommand.next_seq += 2
            seq = NetCommand.next_seq
        self.seq = seq

        assert isinstance(text, str)

        self._show_debug_info(cmd_id, seq, text)

        if self.protocol == self.HTTP_PROTOCOL:
            msg = '%s\t%s\t%s\n' % (cmd_id, seq, text)
        else:
            encoded = quote(str(text), '/<>_=" \t')
            msg = '%s\t%s\t%s\n' % (cmd_id, seq, encoded)

        if IS_PY2:
            assert isinstance(msg, str)  # i.e.: bytes
            as_bytes = msg
        else:
            if isinstance(msg, str):
                msg = msg.encode('utf-8')

            assert isinstance(msg, bytes)
            as_bytes = msg
        self._as_bytes = as_bytes

    def send(self, sock):
        as_bytes = self._as_bytes
        if self.protocol == self.HTTP_PROTOCOL:
            sock.sendall(('Content-Length: %s\r\n\r\n' % len(as_bytes)).encode('ascii'))

        sock.sendall(as_bytes)

    @classmethod
    def _show_debug_info(cls, cmd_id, seq, text):
        pqi_log.debug(
            'sending cmd --> %20s %s' % (ID_TO_MEANING.get(str(cmd_id), 'UNKNOWN'), text.replace('\n', ' '))
        )
        # with cls._show_debug_info_lock:
        #     # Only one thread each time (rlock).
        #     if cls._showing_debug_info:
        #         # avoid recursing in the same thread (just printing could create
        #         # a new command when redirecting output).
        #         return
        #
        #     cls._showing_debug_info += 1
        #     try:
        #         out_message = 'sending cmd --> '
        #         out_message += "%20s" % ID_TO_MEANING.get(str(cmd_id), 'UNKNOWN')
        #         out_message += ' '
        #         out_message += text.replace('\n', ' ')
        #         try:
        #             sys.stderr.write('%s\n' % (out_message,))
        #         except:
        #             pass
        #     finally:
        #         cls._showing_debug_info -= 1


# # =======================================================================================================================
# # NetCommandFactory
# # =======================================================================================================================
class NetCommandFactory:
    def make_dict(self, **kwargs):
        return kwargs

    def make_json(self, **kwargs):
        return json.dumps(kwargs)

    def make_widget_info_message(self,
                                 widget_info: QWidgetInfo):
        cmd = NetCommand(CMD_WIDGET_INFO, 0, self.make_json(
            **dataclasses.asdict(widget_info)
        ))
        return cmd

    def make_exec_code_message(self, code: str):
        cmd = NetCommand(CMD_EXEC_CODE, 0, code)
        return cmd

    def make_exec_code_result_message(self, result: str):
        cmd = NetCommand(CMD_EXEC_CODE_RESULT, 0, result)
        return cmd

    def make_exec_code_err_message(self, err_msg: str):
        cmd = NetCommand(CMD_EXEC_CODE_ERROR, 0, err_msg)
        return cmd

    def make_enable_inspect_message(self, extra: OptionalDict = None):
        if extra is None:
            extra = {}
        return NetCommand(CMD_ENABLE_INSPECT, 0, json.dumps(extra))

    def make_disable_inspect_message(self):
        return NetCommand(CMD_DISABLE_INSPECT, 0, '')

    def make_inspect_finished_message(self):
        return NetCommand(CMD_INSPECT_FINISHED, 0, '')

    def make_set_widget_highlight_message(self, widget_id: int, is_highlight: bool):
        return NetCommand(CMD_SET_WIDGET_HIGHLIGHT, 0, self.make_json(
            widget_id=widget_id,
            is_highlight=is_highlight
        ))

    def make_select_widget_message(self, widget_id: int):
        return NetCommand(CMD_SELECT_WIDGET, 0, str(widget_id))

    def make_req_widget_info_message(self, widget_id: int, extra: OptionalDict = None):
        if extra is None:
            extra = {}
        return NetCommand(CMD_REQ_WIDGET_INFO, 0, self.make_json(
            widget_id=widget_id,
            extra=extra,
        ))

    def make_req_children_info_message(self, widget_id: int):
        return NetCommand(CMD_REQ_CHILDREN_INFO, 0, str(widget_id))

    def make_children_info_message(self, children_info: QWidgetChildrenInfo):
        return NetCommand(CMD_CHILDREN_INFO, 0, self.make_json(
            **dataclasses.asdict(children_info)
        ))

    def make_req_control_tree_message(self, extra: OptionalDict = None):
        if extra is None:
            extra = {}
        return NetCommand(CMD_REQ_CONTROL_TREE, 0, json.dumps(extra))

    def make_control_tree_message(self, control_tree: typing.List[typing.Dict], extra: typing.Dict):
        return NetCommand(CMD_CONTROL_TREE, 0, json.dumps({
            TreeViewResultKeys.TREE_INFO_KEY: control_tree,
            TreeViewResultKeys.EXTRA_KEY: extra,
        }))

    def make_req_widget_props_message(self, widget_id: int):
        return NetCommand(CMD_REQ_WIDGET_PROPS, 0, str(widget_id))

    def make_widget_props_message(self, widget_props: typing.List[typing.Dict]):
        return NetCommand(CMD_WIDGET_PROPS, 0, json.dumps(widget_props))

    def make_exit_message(self):
        return NetCommand(CMD_EXIT, 0, '')


INTERNAL_TERMINATE_THREAD = 1
INTERNAL_SUSPEND_THREAD = 2


# =======================================================================================================================
# InternalThreadCommand
# =======================================================================================================================
class InternalThreadCommand:
    """ internal commands are generated/executed by the debugger.

    The reason for their existence is that some commands have to be executed
    on specific threads. These are the InternalThreadCommands that get
    get posted to PyDB.cmdQueue.
    """

    def __init__(self, thread_id):
        self.thread_id = thread_id

    def can_be_executed_by(self, thread_id):
        '''By default, it must be in the same thread to be executed
        '''
        return self.thread_id == thread_id or self.thread_id.endswith('|' + thread_id)

    def do_it(self, dbg):
        raise NotImplementedError("you have to override do_it")
