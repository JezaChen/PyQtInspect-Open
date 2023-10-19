# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/18 14:52
# Description: 
# ==============================================
import sys
import os
import time

from PyQtInspect._pqi_bundle._pqi_monkey_qt_helpers import _filter_trace_stack
from PyQtInspect._pqi_bundle.pqi_comm_constants import CMD_PROCESS_CREATED
from PyQtInspect._pqi_bundle.pqi_qt_tools import exec_code_in_widget, get_parent_info, get_widget_size, get_widget_pos, \
    get_stylesheet, get_children_info, import_Qt
from PyQtInspect._pqi_imps._pqi_saved_modules import threading, thread
from PyQtInspect._pqi_bundle.pqi_contants import get_current_thread_id
from PyQtInspect._pqi_bundle.pqi_comm import PyDBDaemonThread, ReaderThread, get_global_debugger, set_global_debugger, \
    WriterThread, start_client, start_server, CommunicationRole, NetCommand, NetCommandFactory
import traceback

from PyQtInspect._pqi_bundle.pqi_structures import QWidgetInfo, QWidgetChildrenInfo

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
    finally:
        stream.close()

    # execute the script (note: it's important to compile first to have the filename set in debug mode)
    exec(compile(contents + "\n", file, 'exec'), glob, loc)


# =======================================================================================================================
# SetupHolder
# =======================================================================================================================
class SetupHolder:
    setup = None


class TrackedLock(object):
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


class PyDB(object):
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
        self._selected_widget = None
        self._id_to_widget = {}

    def _try_reconnect(self):
        """
        Attempts to reconnect to the last host and port used for connection.
        Retries up to 10 times with a delay between retries. If a successful
        reconnection is made, it prints a message indicating the reconnection.
        Returns True if reconnection was successful, False otherwise.
        """
        retry_count = 0
        while retry_count <= 10:
            try:
                self.connect(self._last_host, self._last_port)
                print("Reconnected to %s:%s" % (self._last_host, self._last_port))
                return True  # success
            except:
                retry_count += 1
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

    def connect(self, host, port):
        self._last_host, self._last_port = host, port
        if host:
            self.communication_role = CommunicationRole.CLIENT
            s = start_client(host, port)
        else:
            self.communication_role = CommunicationRole.SERVER
            s = start_server(port)

        self.initialize_network(s)
        if host:
            self.send_process_created_message()

    def check_output_redirect(self):
        pass

    def send_process_created_message(self):
        """Sends a message that a new process has been created.
        """
        cmdText = '<process/>'
        cmd = NetCommand(CMD_PROCESS_CREATED, 0, cmdText)
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
        self.check_output_redirect()
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
        pass

    def enable_inspect(self):
        self.inspect_enabled = True

    def disable_inspect(self):
        self.inspect_enabled = False

    def notify_inspect_finished(self, widget):
        self.select_widget(widget)

        cmd = self.cmd_factory.make_inspect_finished_message()
        self.writer.add_command(cmd)

    def select_widget(self, widget):
        self._selected_widget = widget

    def exec_code_in_selected_widget(self, code):
        QtCore = import_Qt(SetupHolder.setup['qt-support']).QtCore
        if hasattr(self._selected_widget, '_pqi_exec'):
            event = QtCore.QEvent(QtCore.QEvent.User)
            event._pqi_exec_code = code
            QtCore.QCoreApplication.postEvent(self._selected_widget, event)

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
        if widget is not None:
            QtCore = import_Qt(SetupHolder.setup['qt-support']).QtCore
            attribute = '_pqi_highlight_self' if is_highlight else '_pqi_unhighlight_self'
            if hasattr(widget, attribute):
                event = QtCore.QEvent(QtCore.QEvent.User)
                event._pqi_is_highlight = is_highlight
                QtCore.QCoreApplication.postEvent(widget, event)

    def select_widget_by_id(self, widget_id):
        widget = self._id_to_widget.get(widget_id, None)
        if widget is not None:
            self.select_widget(widget)

    def notify_widget_info(self, widget_id, extra):
        widget = self._id_to_widget.get(widget_id, None)
        if widget is None:
            return

        parent_info = list(get_parent_info(widget))
        parent_classes, parent_ids, parent_obj_names = [], [], []
        if parent_info:
            parent_classes, parent_ids, parent_obj_names = zip(*get_parent_info(widget))

        widget_info = QWidgetInfo(
            class_name=widget.__class__.__name__,
            object_name=widget.objectName(),
            id=id(widget),
            stacks_when_create=_filter_trace_stack(getattr(widget, '_pqi_stacks_when_create', [])),
            size=get_widget_size(widget),
            pos=get_widget_pos(widget),
            parent_classes=parent_classes,
            parent_ids=parent_ids,
            parent_object_names=parent_obj_names,
            stylesheet=get_stylesheet(widget),
            extra=extra,
        )
        self.send_widget_message(widget_info)

    def notify_children_info(self, widget_id):
        widget = self._id_to_widget.get(widget_id, None)
        if widget is None:
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


def set_debug(setup):
    setup['DEBUG_RECORD_SOCKET_READS'] = True
    setup['DEBUG_TRACE_BREAKPOINTS'] = 1
    setup['DEBUG_TRACE_LEVEL'] = 3


# =======================================================================================================================
# settrace
# =======================================================================================================================
def settrace(
        host=None,
        port=5678,
        patch_multiprocessing=False,
        qt_support="pyqt5",
):
    '''Sets the tracing function with the pydev debug function and initializes needed facilities.

    @param host: the user may specify another host, if the debug server is not in the same machine (default is the local
        host)

    @param port: specifies which port to use for communicating with the server (note that the server must be started
        in the same port). @note: currently it's hard-coded at 5678 in the client

    @param patch_multiprocessing: if True we'll patch the functions which create new processes so that launched
        processes are debugged.

    @param qt_support: the Qt support to be used (currently 'pyqt5' is default).
    '''
    _set_trace_lock.acquire()
    try:
        _locked_settrace(
            host,
            port,
            patch_multiprocessing,
            qt_support
        )
    finally:
        _set_trace_lock.release()


_set_trace_lock = thread.allocate_lock()


def _locked_settrace(
        host,
        port,
        patch_multiprocessing,
        qt_support,
):
    if SetupHolder.setup is None:
        setup = {
            'client': host,  # dispatch expects client to be set to the host address when server is False
            'server': False,
            'port': int(port),
            'multiprocess': patch_multiprocessing,
            'qt-support': qt_support,
        }
        SetupHolder.setup = setup

    if patch_multiprocessing:
        try:
            import PyQtInspect._pqi_bundle.pqi_monkey
        except:
            pass
        else:
            PyQtInspect._pqi_bundle.pqi_monkey.patch_new_process_functions()

    try:
        import PyQtInspect._pqi_bundle.pqi_monkey_qt
    except:
        pass
    else:
        PyQtInspect._pqi_bundle.pqi_monkey_qt.patch_qt(qt_support)

    global connected
    connected = False

    # Reset created PyDB daemon threads after fork - parent threads don't exist in a child process.
    PyDBDaemonThread.created_pydb_daemon_threads = {}

    if not connected:

        if SetupHolder.setup is None:
            setup = {
                'client': host,  # dispatch expects client to be set to the host address when server is False
                'server': False,
                'port': int(port),
                'multiprocess': patch_multiprocessing,
                'qt-support': qt_support,
            }
            SetupHolder.setup = setup

        debugger = PyDB()
        debugger.connect(host, port)  # Note: connect can raise error.

        # Mark connected only if it actually succeeded.
        connected = True

        while not debugger.ready_to_run:
            time.sleep(0.1)  # busy wait until we receive run command

        # Stop the tracing as the last thing before the actual shutdown for a clean exit.
        # atexit.register(stoptrace)  todo


# =======================================================================================================================
# main
# =======================================================================================================================
def usage(do_exit=True, exit_code=0):
    sys.stdout.write('Usage:\n')
    sys.stdout.write('\tpqi.py --port N [(--client hostname) | --server] --file executable [file_options]\n')
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
        usage(exit_code=1)

    port = setup['port']
    host = setup['client']

    debugger = PyDB()

    try:
        debugger.connect(host, port)
    except:
        sys.stderr.write("Could not connect to %s: %s\n" % (host, port))
        traceback.print_exc()
        sys.exit(1)

    import PyQtInspect._pqi_bundle.pqi_monkey

    if setup['multiprocess']:
        PyQtInspect._pqi_bundle.pqi_monkey.patch_new_process_functions()

    is_module = setup['module']

    enable_qt_support(setup['qt-support'])
    if setup['file']:
        debugger.run(setup["file"], None, None, is_module)


if __name__ == '__main__':
    main()
