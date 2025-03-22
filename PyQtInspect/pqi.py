# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/18 14:52
# Description: 
# ==============================================
import atexit
import subprocess
import sys
import os
import time
import pathlib

pyqt_inspect_module_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if pyqt_inspect_module_dir not in sys.path:
    sys.path.insert(0, pyqt_inspect_module_dir)

from PyQtInspect._pqi_bundle.pqi_comm_constants import CMD_PROCESS_CREATED, CMD_QT_PATCH_SUCCESS
from PyQtInspect._pqi_bundle.pqi_qt_tools import exec_code_in_widget, get_parent_info, get_widget_size, get_widget_pos, \
    get_stylesheet, get_children_info, set_widget_highlight, get_widget_object_name, is_wrapped_pointer_valid, \
    get_create_stack, get_control_tree
from PyQtInspect._pqi_imps._pqi_saved_modules import threading, thread
from PyQtInspect._pqi_bundle.pqi_contants import get_current_thread_id, SHOW_DEBUG_INFO_ENV, DebugInfoHolder, IS_WINDOWS
from PyQtInspect._pqi_bundle.pqi_comm import PyDBDaemonThread, ReaderThread, get_global_debugger, set_global_debugger, \
    WriterThread, start_client, start_server, CommunicationRole, NetCommand, NetCommandFactory
from PyQtInspect._pqi_bundle.pqi_typing import OptionalDict
from PyQtInspect._pqi_bundle.pqi_structures import QWidgetInfo, QWidgetChildrenInfo
from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_connect_tools import random_port
from PyQtInspect._pqi_bundle.pqi_path_helper import find_pqi_server_gui_entry

import traceback

threadingCurrentThread = threading.current_thread


def enable_qt_support(qt_support_mode):
    import PyQtInspect._pqi_bundle.pqi_monkey_qt as monkey_qt
    monkey_qt.patch_qt(qt_support_mode)


def get_fullname(mod_name):
    import pkgutil

    try:
        loader = pkgutil.get_loader(mod_name)
    except:
        return None
    if loader is not None:
        for attr in ("get_filename", "_get_filename"):
            meth = getattr(loader, attr, None)
            if meth is not None:
                return meth(mod_name)
    return None


def get_package_dir(mod_name):
    for path in sys.path:
        mod_path = os.path.join(path, mod_name.replace('.', '/'))
        if os.path.isdir(mod_path):
            return mod_path
    return None


def save_main_module(file, module_name):
    # patch provided by: Scott Schlesier - when script is run, it does not
    # use globals from pydevd:
    # This will prevent the pydevd script from contaminating the namespace for the script to be debugged
    # pretend pydevd is not the main module, and
    # convince the file to be debugged that it was loaded as main
    sys.modules[module_name] = sys.modules['__main__']
    sys.modules[module_name].__name__ = module_name

    try:
        from importlib.machinery import ModuleSpec
        from importlib.util import module_from_spec
        m = module_from_spec(ModuleSpec('__main__', loader=None))
    except:
        # A fallback for Python <= 3.4
        from imp import new_module
        m = new_module('__main__')

    sys.modules['__main__'] = m
    orig_module = sys.modules[module_name]
    for attr in ['__loader__', '__spec__']:
        if hasattr(orig_module, attr):
            orig_attr = getattr(orig_module, attr)
            setattr(m, attr, orig_attr)
    m.__file__ = file

    return m


def execfile(file, glob=None, loc=None):
    if glob is None:
        import sys
        glob = sys._getframe().f_back.f_globals
    if loc is None:
        loc = glob

    # It seems that the best way is using tokenize.open(): http://code.activestate.com/lists/python-dev/131251/
    import tokenize
    stream = tokenize.open(file)  # @UndefinedVariable
    try:
        contents = stream.read()
    except:
        from PyQtInspect._pqi_imps._pqi_execfile import exec_pyc
        import sys
        pqi_log.debug(f'exec_pyc: {file}, sys.argv: {sys.argv}')
        exec_pyc(file, glob, loc)
        return
    finally:
        stream.close()

    # execute the script (note: it's important to compile first to have the filename set in debug mode)
    exec(compile(contents + "\n", file, 'exec'), glob, loc)


# =======================================================================================================================
# SetupHolder
# =======================================================================================================================
from PyQtInspect._pqi_common.pqi_setup_holder import SetupHolder


class TrackedLock:
    """The lock that tracks if it has been acquired by the current thread
    """

    def __init__(self):
        self._lock = thread.allocate_lock()
        # thread-local storage
        self._tls = threading.local()
        self._tls.is_lock_acquired = False

    def acquire(self):
        self._lock.acquire()
        self._tls.is_lock_acquired = True

    def release(self):
        self._lock.release()
        self._tls.is_lock_acquired = False

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def is_acquired_by_current_thread(self):
        return self._tls.is_lock_acquired


connected = False


def stoptrace():
    """Stops tracing in the current process and undoes all monkey-patches done by the debugger."""
    # TODO need to un-patch the Qt modules

    global connected

    if connected:
        debugger = get_global_debugger()

        if debugger:
            debugger.exiting()

        connected = False


class PyDB:
    """ Main debugging class
    Lots of stuff going on here:

    PyDB starts two threads on startup that connect to remote debugger (RDB)
    The threads continuously read & write commands to RDB.
    PyDB communicates with these threads through command queues.
       Every RDB command is processed by calling process_net_command.
       Every PyDB net command is sent to the net by posting NetCommand to WriterThread queue

       Some commands need to be executed on the right thread (suspend/resume & friends)
       These are placed on the internal command queue.
    """

    _RECONNECT_DELAY = 1
    _RECONNECT_TRIES = 10 if IS_WINDOWS else 100

    def __init__(self, set_as_global=True):
        if set_as_global:
            set_global_debugger(self)
            # pydevd_tracing.replace_sys_set_trace_func()

        self._last_host = None
        self._last_port = None

        self.reader = None
        self.writer = None
        self.cmd_factory = NetCommandFactory()
        # self._cmd_queue = defaultdict(_queue.Queue)  # Key is thread id or '*', value is Queue

        self.breakpoints = {}

        self.ready_to_run = True

        self._finish_debugging_session = False

        # the role PyDB plays in the communication with IDE
        self.communication_role = None

        self.inspect_enabled = False
        self._inspect_extra_data = {}
        self._selected_widget = None

        # Mapping from QWidget object's ID to QWidget object
        # The reason for using dict instead of WeakValueDictionary,
        # is that for some internal child controls (such as QSpinbox.lineEdit()),
        # there are no references at the Python level.
        # This results in the wrapper objects being recycled by gc, and subsequently, these controls can't be found.
        # Using dict can prolong the lifecycle of these wrappers,
        # but each time it's accessed, it needs to check whether it is valid, if it is not, it needs to be removed.
        self._id_to_widget = {}
        self.global_event_filter = None
        self.global_native_event_filter = None

    def _try_reconnect(self):
        """
        Attempts to reconnect to the last host and port used for connection.
        Retries up to 10 times with a delay between retries. If a successful
        reconnection is made, it prints a message indicating the reconnection.
        Returns True if reconnection was successful, False otherwise.
        """
        retry_count = 0
        while retry_count <= self._RECONNECT_TRIES:
            try:
                self.connect(self._last_host, self._last_port)
                pqi_log.info("Reconnected to %s:%s" % (self._last_host, self._last_port))
                return True  # success
            except:
                retry_count += 1
                if not IS_WINDOWS:
                    # ---
                    # For non-Windows platforms, we need to wait a bit longer between retries
                    # because in Windows, connect() will block until the connection is established or times out.
                    # ---
                    time.sleep(self._RECONNECT_DELAY)
        return False

    def finish_debugging_session(self):
        if not self._try_reconnect():
            self._finish_debugging_session = True

    def initialize_network(self, sock):
        sock.settimeout(None)

        self.writer = WriterThread(sock)
        self.reader = ReaderThread(sock)
        self.writer.start()
        self.reader.start()

    def connect(self, host, port, *, output_connection_errors=True):
        self._last_host, self._last_port = host, port
        if host:
            self.communication_role = CommunicationRole.CLIENT
            s = start_client(host, port, output_errors=output_connection_errors)
        else:
            self.communication_role = CommunicationRole.SERVER
            s = start_server(port, output_errors=output_connection_errors)

        self.initialize_network(s)
        if host:
            self.send_process_created_message()

    def send_process_created_message(self):
        """Sends a message that a new process has been created.
        """
        cmdText = '<process/>'
        cmd = NetCommand(CMD_PROCESS_CREATED, 0, cmdText)
        self.writer.add_command(cmd)

    def send_qt_patch_success_message(self):
        cmdText = str(os.getpid())
        cmd = NetCommand(CMD_QT_PATCH_SUCCESS, 0, cmdText)
        self.writer.add_command(cmd)

    def run(self, file, globals=None, locals=None, is_module=False, set_trace=True):
        module_name = None
        entry_point_fn = ''
        if is_module:
            # When launching with `python -m <module>`, python automatically adds
            # an empty path to the PYTHONPATH which resolves files in the current
            # directory, so, depending how pydevd itself is launched, we may need
            # to manually add such an entry to properly resolve modules in the
            # current directory
            if '' not in sys.path:
                sys.path.insert(0, '')
            file, _, entry_point_fn = file.partition(':')
            module_name = file
            filename = get_fullname(file)
            if filename is None:
                mod_dir = get_package_dir(module_name)
                if mod_dir is None:
                    sys.stderr.write("No module named %s\n" % file)
                    return
                else:
                    filename = get_fullname("%s.__main__" % module_name)
                    if filename is None:
                        sys.stderr.write("No module named %s\n" % file)
                        return
                    else:
                        file = filename
            else:
                file = filename
                mod_dir = os.path.dirname(filename)
                main_py = os.path.join(mod_dir, '__main__.py')
                main_pyc = os.path.join(mod_dir, '__main__.pyc')
                if filename.endswith('__init__.pyc'):
                    if os.path.exists(main_pyc):
                        filename = main_pyc
                    elif os.path.exists(main_py):
                        filename = main_py
                elif filename.endswith('__init__.py'):
                    if os.path.exists(main_pyc) and not os.path.exists(main_py):
                        filename = main_pyc
                    elif os.path.exists(main_py):
                        filename = main_py

            sys.argv[0] = filename

        if os.path.isdir(file):
            new_target = os.path.join(file, '__main__.py')
            if os.path.isfile(new_target):
                file = new_target

        m = None
        if globals is None:
            m = save_main_module(file, 'PyQtInspect.pqi')
            globals = m.__dict__
            try:
                globals['__builtins__'] = __builtins__
            except NameError:
                pass  # Not there on Jython...

        if locals is None:
            locals = globals

        # Predefined (writable) attributes: __name__ is the module's name;
        # __doc__ is the module's documentation string, or None if unavailable;
        # __file__ is the pathname of the file from which the module was loaded,
        # if it was loaded from a file. The __file__ attribute is not present for
        # C modules that are statically linked into the interpreter; for extension modules
        # loaded dynamically from a shared library, it is the pathname of the shared library file.

        # I think this is an ugly hack, bug it works (seems to) for the bug that says that sys.path should be the same in
        # debug and run.
        if sys.path[0] != '' and m is not None and m.__file__.startswith(sys.path[0]):
            # print >> sys.stderr, 'Deleting: ', sys.path[0]
            del sys.path[0]

        if not is_module:
            # now, the local directory has to be added to the pythonpath
            # sys.path.insert(0, os.getcwd())
            # Changed: it's not the local directory, but the directory of the file launched
            # The file being run must be in the pythonpath (even if it was not before)
            sys.path.insert(0, os.path.split(os.path.realpath(file))[0])

        if set_trace:

            while not self.ready_to_run:
                time.sleep(0.1)  # busy wait until we receive run command

        t = threadingCurrentThread()
        thread_id = get_current_thread_id(t)

        if hasattr(sys, 'exc_clear'):
            # we should clean exception information in Python 2, before user's code execution
            sys.exc_clear()

        return self._exec(is_module, entry_point_fn, module_name, file, globals, locals)

    def _exec(self, is_module, entry_point_fn, module_name, file, globals, locals):
        '''
        This function should have frames tracked by unhandled exceptions (the `_exec` name is important).
        '''
        if not is_module:
            execfile(file, globals, locals)  # execute the script
        else:
            # treat ':' as a separator between module and entry point function
            # if there is no entry point we run we same as with -m switch. Otherwise we perform
            # an import and execute the entry point
            if entry_point_fn:
                mod = __import__(module_name, level=0, fromlist=[entry_point_fn], globals=globals, locals=locals)
                func = getattr(mod, entry_point_fn)
                func()
            else:
                # Run with the -m switch
                import runpy
                if hasattr(runpy, '_run_module_as_main'):
                    # Newer versions of Python actually use this when the -m switch is used.
                    if sys.version_info[:2] <= (2, 6):
                        runpy._run_module_as_main(module_name, set_argv0=False)
                    else:
                        runpy._run_module_as_main(module_name, alter_argv=False)
                else:
                    runpy.run_module(module_name)
        return globals

    def exiting(self):
        # noinspection PyBroadException
        try:
            sys.stdout.flush()
        except:
            pass
        # noinspection PyBroadException
        try:
            sys.stderr.flush()
        except:
            pass
        cmd = self.cmd_factory.make_exit_message()
        self.writer.add_command(cmd)

    def send_widget_message(self, widget_info: QWidgetInfo):
        cmd = self.cmd_factory.make_widget_info_message(widget_info)
        self.writer.add_command(cmd)

    # trace_dispatch = _trace_dispatch
    # frame_eval_func = frame_eval_func
    # dummy_trace_dispatch = dummy_trace_dispatch

    # noinspection SpellCheckingInspection
    @staticmethod
    def stoptrace():
        """A proxy method for calling :func:`stoptrace` from the modules where direct import
        is impossible because, for example, a circular dependency."""
        stoptrace()

    def dispose_and_kill_all_pqi_threads(self):
        # TODO
        py_db = get_global_debugger()
        if py_db is self:
            set_global_debugger(None)

    def enable_inspect(self, extra_data: OptionalDict = None):
        if extra_data is None:
            extra_data = {}

        self.inspect_enabled = True
        self._inspect_extra_data = extra_data

    def disable_inspect(self):
        self.inspect_enabled = False
        self._inspect_extra_data = {}

    @property
    def mock_left_button_down(self) -> bool:
        return self._inspect_extra_data.get('mock_left_button_down', False)

    def notify_inspect_finished(self, widget):
        self.select_widget(widget)

        cmd = self.cmd_factory.make_inspect_finished_message()
        self.writer.add_command(cmd)

    def select_widget(self, widget):
        self._selected_widget = widget

    def exec_code_in_selected_widget(self, code):
        exec_code_in_widget(self._selected_widget, code)

    def notify_exec_code_result(self, result):
        cmd = self.cmd_factory.make_exec_code_result_message(result)
        self.writer.add_command(cmd)

    def notify_exec_code_error_message(self, err_msg):
        cmd = self.cmd_factory.make_exec_code_err_message(err_msg)
        self.writer.add_command(cmd)

    def notify_thread_not_alive(self, thread_id):
        ...

    def register_widget(self, widget):
        self._id_to_widget[id(widget)] = widget

    def set_widget_highlight_by_id(self, widget_id: int, is_highlight: bool):
        widget = self._id_to_widget.get(widget_id, None)

        if widget is None:
            return

        if not is_wrapped_pointer_valid(widget):
            del self._id_to_widget[widget_id]
            return

        set_widget_highlight(widget, is_highlight)

    def select_widget_by_id(self, widget_id):
        widget = self._id_to_widget.get(widget_id, None)

        if widget is None:
            return

        if not is_wrapped_pointer_valid(widget):
            del self._id_to_widget[widget_id]
            return

        self.select_widget(widget)

    def send_widget_info_to_server(self, widget, extra=None):
        if extra is None:
            extra = {}

        parent_info = list(get_parent_info(widget))
        parent_classes, parent_ids, parent_obj_names = [], [], []
        if parent_info:
            parent_classes, parent_ids, parent_obj_names = zip(*get_parent_info(widget))

        widget_info = QWidgetInfo(
            class_name=widget.__class__.__name__,
            object_name=get_widget_object_name(widget),
            id=id(widget),
            stacks_when_create=get_create_stack(widget),
            size=get_widget_size(widget),
            pos=get_widget_pos(widget),
            parent_classes=parent_classes,
            parent_ids=parent_ids,
            parent_object_names=parent_obj_names,
            stylesheet=get_stylesheet(widget),
            extra=extra,
        )
        self.send_widget_message(widget_info)

    def notify_widget_info(self, widget_id, extra):
        widget = self._id_to_widget.get(widget_id, None)

        if widget is None:
            return

        if not is_wrapped_pointer_valid(widget):
            del self._id_to_widget[widget_id]
            return

        self.send_widget_info_to_server(widget, extra)

    def notify_children_info(self, widget_id):
        """
        Notify the children information of the given widget to the debugger.

        @param widget_id: The ID of the widget.
        @note: used for the bottom hierarchy view of the server GUI program.
        """
        widget = self._id_to_widget.get(widget_id, None)

        if widget is None:
            return

        if not is_wrapped_pointer_valid(widget):
            del self._id_to_widget[widget_id]
            return

        children_info_list = list(get_children_info(widget))
        child_classes, child_ids, child_object_names = [], [], []
        if children_info_list:
            child_classes, child_ids, child_object_names = zip(*children_info_list)

        children_info = QWidgetChildrenInfo(
            widget_id=widget_id,
            child_classes=child_classes,
            child_ids=child_ids,
            child_object_names=child_object_names,
        )

        cmd = self.cmd_factory.make_children_info_message(children_info)
        self.writer.add_command(cmd)

    def notify_control_tree(self, extra):
        control_tree = get_control_tree()
        cmd = self.cmd_factory.make_control_tree_message(control_tree, extra)
        self.writer.add_command(cmd)


def set_debug(setup):
    import logging

    setup['DEBUG_RECORD_SOCKET_READS'] = True
    setup['LOG_TO_FILE_LEVEL'] = logging.DEBUG
    setup['LOG_TO_CONSOLE_LEVEL'] = logging.DEBUG
    setup['SHOW_CONNECTION_ERRORS'] = True


# =======================================================================================================================
# settrace
# =======================================================================================================================
def settrace(
        host='127.0.0.1',
        port=19394,
        patch_multiprocessing=False,
        qt_support='pyqt5',
        is_attach=False,
):
    '''Sets the tracing function with the pydev debug function and initializes needed facilities.

    @param host: the user may specify another host, if the debug server is not in the same machine (default is the local
        host)

    @param port: specifies which port to use for communicating with the server (note that the server must be started
        in the same port).

    @param patch_multiprocessing: if True we'll patch the functions which create new processes so that launched
        processes are debugged.

    @param qt_support: the Qt support to be used (currently 'pyqt5' is default).

    @param is_attach: if True, we're attaching to an existing process (and not launching a new one) now.
    '''
    _set_trace_lock.acquire()
    try:
        _locked_settrace(
            host,
            port,
            patch_multiprocessing,
            qt_support,
            is_attach
        )
    finally:
        _set_trace_lock.release()


_set_trace_lock = thread.allocate_lock()


def _locked_settrace(
        host,
        port,
        patch_multiprocessing,
        qt_support,
        is_attach
):
    if SetupHolder.setup is None:
        setup = {
            'client': host,  # dispatch expects client to be set to the host address when server is False
            'server': False,
            'port': int(port),
            'multiprocess': patch_multiprocessing,
            'qt-support': qt_support,
            'stack-max-depth': 0,
            'show-pqi-stack': False,
        }
        SetupHolder.setup = setup

    if patch_multiprocessing:
        try:
            import PyQtInspect._pqi_bundle.pqi_monkey
        except:
            pass
        else:
            PyQtInspect._pqi_bundle.pqi_monkey.patch_new_process_functions()

    global connected
    connected = False

    # Reset created PyDB daemon threads after fork - parent threads don't exist in a child process.
    PyDBDaemonThread.created_pydb_daemon_threads = {}

    if not connected:
        debugger = PyDB()
        debugger.connect(host, port)  # Note: connect can raise error.

        # Mark connected only if it actually succeeded.
        connected = True

        while not debugger.ready_to_run:
            time.sleep(0.1)  # busy wait until we receive run command

        # Stop the tracing as the last thing before the actual shutdown for a clean exit.
        atexit.register(stoptrace)

    try:
        import PyQtInspect._pqi_bundle.pqi_monkey_qt
    except:
        pass
    else:
        PyQtInspect._pqi_bundle.pqi_monkey_qt.patch_qt(qt_support, is_attach=is_attach)


# =======================================================================================================================
# main
# =======================================================================================================================
def usage(do_exit=True, exit_code=0):
    sys.stdout.write('Usage:\n')
    sys.stdout.write(
        '\tpqi.py [--port N --client hostname | --direct] [--multiprocess] [--show-pqi-stack] '
        '--qt-support=[pyqt5|pyqt6|pyside2|pyside6] '
        '--file executable [file_options]\n'
    )
    if do_exit:
        sys.exit(exit_code)


def main():
    # parse the command line. --file is our last argument that is required
    try:
        from PyQtInspect._pqi_bundle.pqi_command_line_handling import process_command_line
        setup = process_command_line(sys.argv)
        SetupHolder.setup = setup
    except ValueError:
        traceback.print_exc()
        return usage(exit_code=1)

    # for debug
    if SHOW_DEBUG_INFO_ENV:
        set_debug(setup)

    DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = setup.get('DEBUG_RECORD_SOCKET_READS',
                                                          DebugInfoHolder.DEBUG_RECORD_SOCKET_READS)
    DebugInfoHolder.LOG_TO_FILE_LEVEL = setup.get('LOG_TO_FILE_LEVEL', DebugInfoHolder.LOG_TO_FILE_LEVEL)
    DebugInfoHolder.LOG_TO_CONSOLE_LEVEL = setup.get('LOG_TO_CONSOLE_LEVEL', DebugInfoHolder.LOG_TO_CONSOLE_LEVEL)

    # connect
    is_direct_mode = setup.get('direct', False)
    if not is_direct_mode:
        port = setup['port']
        host = setup['client']
    else:
        # ===============================================
        #  Direct mode: run the server at the same time
        # ===============================================
        # Override the host and port to localhost and a random port
        host = setup['client'] = '127.0.0.1'
        port = setup['port'] = random_port()
        # Run server first
        try:
            # Run with detached mode
            subprocess.Popen(
                ['pqi-server', '--port', str(port), '--direct'],
                close_fds=True, stdin=None, stdout=None, stderr=None,
            )
        except Exception as e:
            # If we can't start the server by calling ``pqi-server``,
            # try to run the GUI entry directly.
            pqi_log.warning(f'Failed to start pqi-server: "{e}", trying to run GUI entry directly.')
            try:
                gui_entry = find_pqi_server_gui_entry()
                subprocess.Popen(
                    [sys.executable, gui_entry, '--port', str(port), '--direct'],
                    close_fds=True, stdin=None, stdout=None, stderr=None,
                    creationflags=subprocess.DETACHED_PROCESS if IS_WINDOWS else 0,
                )
            except:
                # OK, we tried our best, let's give up...
                pqi_log.error(f'Failed to start pqi-server GUI entry: "{e}", exiting.')
                sys.stderr.write(f'Error: "{e}"\n')
                sys.exit(1)

    # run the client
    debugger = PyDB()

    while True:
        try:
            debugger.connect(
                host, port,
                # show connection errors if (1. not in direct mode) or (2. in debug mode)
                output_connection_errors=(not is_direct_mode or setup.get('SHOW_CONNECTION_ERRORS', False))
            )
            # Connected successfully, break the loop.
            break
        except:
            if not is_direct_mode:
                # If not in direct mode, just give up if we can't connect.
                sys.stderr.write("Could not connect to %s: %s\n" % (host, port))
                traceback.print_exc()
                sys.exit(1)
            else:
                # Otherwise, keep trying to connect in direct mode until succeed. (For Mac, it's necessary)
                time.sleep(0.1)
                continue

    global connected
    connected = True  # Mark that we're connected when started from cli.

    atexit.register(stoptrace)

    import PyQtInspect._pqi_bundle.pqi_monkey

    if setup['multiprocess']:
        PyQtInspect._pqi_bundle.pqi_monkey.patch_new_process_functions()

    is_module = setup['module']

    enable_qt_support(setup['qt-support'])

    if setup['file']:
        debugger.run(setup["file"], None, None, is_module)


if __name__ == '__main__':
    main()
