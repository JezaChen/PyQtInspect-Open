# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/8/18 14:52
# Description: 
# ==============================================
import sys
import os
import time

from PyQtInspect._pqi_imps._pqi_saved_modules import threading, thread
from PyQtInspect._pqi_bundle import fix_getpass
from PyQtInspect._pqi_bundle import pqi_vm_type
from PyQtInspect.pqi_contants import IS_JYTH_LESS25, IS_PYCHARM, get_thread_id, get_current_thread_id, \
    dict_keys, dict_iter_items, DebugInfoHolder, PYTHON_SUSPEND, STATE_SUSPEND, STATE_RUN, get_frame, xrange, \
    clear_cached_thread_id, INTERACTIVE_MODE_AVAILABLE, SHOW_DEBUG_INFO_ENV, IS_PY34_OR_GREATER, IS_PY36_OR_GREATER, \
    IS_PY2, NULL, NO_FTRACE, dummy_excepthook, IS_CPYTHON, GOTO_HAS_RESPONSE, set_global_debugger, IS_PY3K
import PyQtInspect.pqi_log as pqi_log
import traceback

threadingCurrentThread = threading.current_thread


def enable_qt_support(qt_support_mode):
    import PyQtInspect.monkey_qt as monkey_qt
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

        self.reader = None
        self.writer = None
        self.output_checker_thread = None
        self.py_db_command_thread = None
        self.quitting = None
        # self.cmd_factory = NetCommandFactory()
        # self._cmd_queue = defaultdict(_queue.Queue)  # Key is thread id or '*', value is Queue

        self.breakpoints = {}

        self.__user_type_renderers = {}

        # mtime to be raised when breakpoints change
        self.mtime = 0

        self.file_to_id_to_line_breakpoint = {}
        self.file_to_id_to_plugin_breakpoint = {}

        # Note: breakpoints dict should not be mutated: a copy should be created
        # and later it should be assigned back (to prevent concurrency issues).
        self.break_on_uncaught_exceptions = {}
        self.break_on_caught_exceptions = {}

        self.ready_to_run = True
        self._main_lock = TrackedLock()
        self._lock_running_thread_ids = thread.allocate_lock()
        self._py_db_command_thread_event = threading.Event()
        # if set_as_global:
        #     CustomFramesContainer._py_db_command_thread_event = self._py_db_command_thread_event

        self._finish_debugging_session = False
        self._termination_event_set = False
        self.signature_factory = None
        # self.SetTrace = pydevd_tracing.SetTrace
        self.SetTrace = sys.settrace  # todo
        self.skip_on_exceptions_thrown_in_same_context = False
        self.ignore_exceptions_thrown_in_lines_with_ignore_exception = True

        # Suspend debugger even if breakpoint condition raises an exception.
        # May be changed with CMD_PYDEVD_JSON_CONFIG.
        self.skip_suspend_on_breakpoint_exception = ()  # By default suspend on any Exception.
        self.skip_print_breakpoint_exception = ()  # By default print on any Exception.

        # By default user can step into properties getter/setter/deleter methods
        self.disable_property_trace = False
        self.disable_property_getter_trace = False
        self.disable_property_setter_trace = False
        self.disable_property_deleter_trace = False

        # this is a dict of thread ids pointing to thread ids. Whenever a command is passed to the java end that
        # acknowledges that a thread was created, the thread id should be passed here -- and if at some time we do not
        # find that thread alive anymore, we must remove it from this list and make the java side know that the thread
        # was killed.
        self._running_thread_ids = {}
        self._set_breakpoints_with_id = False

        # This attribute holds the file-> lines which have an @IgnoreException.
        self.filename_to_lines_where_exceptions_are_ignored = {}

        # working with plugins (lazily initialized)
        self.plugin = None
        self.has_plugin_line_breaks = False
        self.has_plugin_exception_breaks = False
        self.thread_analyser = None
        self.asyncio_analyser = None

        # matplotlib support in debugger and debug console
        self.mpl_in_use = False
        self.mpl_hooks_in_debug_console = False
        self.mpl_modules_for_patching = {}

        self._filename_to_not_in_scope = {}
        self.first_breakpoint_reached = False
        # self.is_filter_enabled = pydevd_utils.is_filter_enabled()
        # self.is_filter_libraries = pydevd_utils.is_filter_libraries()
        self.show_return_values = False
        self.remove_return_values_flag = False
        self.redirect_output = False

        # this flag disables frame evaluation even if it's available
        self.use_frame_eval = True
        self.stop_on_start = False

        # If True, pydevd will send a single notification when all threads are suspended/resumed.
        # self._threads_suspended_single_notification = ThreadsSuspendedSingleNotification(self)

        self._local_thread_trace_func = threading.local()

        # sequence id of `CMD_PROCESS_CREATED` command -> threading.Event
        self.process_created_msg_received_events = dict()
        # the role PyDB plays in the communication with IDE
        self.communication_role = None

        # self.collect_return_info = collect_return_info

        # If True, pydevd will stop on assertion errors in tests.
        self.stop_on_failed_tests = False

        # If True, pydevd finished all work and only waits output_checker_thread
        self.wait_output_checker_thread = False

    def get_thread_local_trace_func(self):
        try:
            thread_trace_func = self._local_thread_trace_func.thread_trace_func
        except AttributeError:
            thread_trace_func = self.trace_dispatch
        return thread_trace_func

    def enable_tracing(self, thread_trace_func=None, apply_to_all_threads=False):
        '''
        Enables tracing.

        If in regular mode (tracing), will set the tracing function to the tracing
        function for this thread -- by default it's `PyDB.trace_dispatch`, but after
        `PyDB.enable_tracing` is called with a `thread_trace_func`, the given function will
        be the default for the given thread.
        '''
        # set_fallback_excepthook()
        pass

    def disable_tracing(self):
        pass

    def on_breakpoints_changed(self, removed=False):
        '''
        When breakpoints change, we have to re-evaluate all the assumptions we've made so far.
        '''
        if not self.ready_to_run:
            # No need to do anything if we're still not running.
            return

        self.mtime += 1
        if not removed:
            # When removing breakpoints we can leave tracing as was, but if a breakpoint was added
            # we have to reset the tracing for the existing functions to be re-evaluated.
            self.set_tracing_for_untraced_contexts()

    def set_tracing_for_untraced_contexts(self, ignore_current_thread=False):
        # Enable the tracing for existing threads (because there may be frames being executed that
        # are currently untraced).
        pass

    @property
    def multi_threads_single_notification(self):
        return self._threads_suspended_single_notification.multi_threads_single_notification

    @multi_threads_single_notification.setter
    def multi_threads_single_notification(self, notify):
        self._threads_suspended_single_notification.multi_threads_single_notification = notify

    def get_plugin_lazy_init(self):
        pass

    def in_project_scope(self, filename):
        pass

    def is_ignored_by_filters(self, filename):
        pass

    def is_exception_trace_in_project_scope(self, trace):
        pass

    def is_top_level_trace_in_project_scope(self, trace):
        pass

    def is_test_item_or_set_up_caller(self, frame):
        pass

    def set_unit_tests_debugging_mode(self):
        self.stop_on_failed_tests = True

    def has_threads_alive(self):
        pass

    def finish_debugging_session(self):
        self._finish_debugging_session = True

    def initialize_network(self, sock):
        pass

    def connect(self, host, port):
        pass

    def get_internal_queue(self, thread_id):
        """ returns internal command queue for a given thread.
        if new queue is created, notify the RDB about it """
        if thread_id.startswith('__frame__'):
            thread_id = thread_id[thread_id.rfind('|') + 1:]
        return self._cmd_queue[thread_id]

    def post_internal_command(self, int_cmd, thread_id):
        """ if thread_id is *, post to the '*' queue"""
        queue = self.get_internal_queue(thread_id)
        queue.put(int_cmd)

    def enable_output_redirection(self, redirect_stdout, redirect_stderr):
        pass

    def check_output_redirect(self):
        pass

    def init_matplotlib_in_debug_console(self):
        pass

    def init_matplotlib_support(self):
        pass

    def _activate_mpl_if_needed(self):
        pass

    def _call_mpl_hook(self):
        pass

    def notify_thread_created(self, thread_id, thread, use_lock=True):
        pass

    def notify_thread_not_alive(self, thread_id, use_lock=True):
        pass

    def send_process_created_message(self):
        """Sends a message that a new process has been created.
        """
        pass

    def send_process_will_be_substituted(self):
        """When `PyDB` works in server mode this method sends a message that a
        new process is going to be created. After that it waits for the
        response from the IDE to be sure that the IDE received this message.
        Waiting for the response is required because the current process might
        become substituted before it actually sends the message and the IDE
        will not try to connect to `PyDB` in this case.

        When `PyDB` works in client mode this method does nothing because the
        substituted process will try to connect to the IDE itself.
        """
        pass

    def set_next_statement(self, frame, event, func_name, next_line):
        pass

    def cancel_async_evaluation(self, thread_id, frame_id):
        pass

    def do_wait_suspend(self, thread, frame, event, arg, send_suspend_message=True,
                        is_unhandled_exception=False):  # @UnusedVariable
        """ busy waits until the thread state changes to RUN
        it expects thread's state as attributes of the thread.
        Upon running, processes any outstanding Stepping commands.

        :param is_unhandled_exception:
            If True we should use the line of the exception instead of the current line in the frame
            as the paused location on the top-level frame (exception info must be passed on 'arg').
        """
        pass

    def _do_wait_suspend(self, thread, frame, event, arg, suspend_type, from_this_thread):
        pass

    def stop_on_unhandled_exception(self, thread, frame, frames_byid, arg):
        pass

    def set_trace_for_frame_and_parents(self, frame, **kwargs):
        pass

    def _create_pydb_command_thread(self):
        pass

    def _create_check_output_thread(self):
        pass

    def start_auxiliary_daemon_threads(self):
        pass

    def prepare_to_run(self, enable_tracing_from_start=True):
        ''' Shared code to prepare debugging by installing traces and registering threads '''
        self.patch_threads()

    def patch_threads(self):
        try:
            # not available in jython!
            threading.settrace(self.trace_dispatch)  # for all future threads
        except:
            pass

        from pqi_monkey import patch_thread_modules
        patch_thread_modules()

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

            if self.break_on_caught_exceptions or self.has_plugin_line_breaks or self.has_plugin_exception_breaks \
                    or self.signature_factory:
                # disable frame evaluation if there are exception breakpoints with 'On raise' activation policy
                # or if there are plugin exception breakpoints or if collecting run-time types is enabled
                self.frame_eval_func = None

            # call prepare_to_run when we already have all information about breakpoints
            self.prepare_to_run()

        t = threadingCurrentThread()
        thread_id = get_current_thread_id(t)

        if hasattr(sys, 'exc_clear'):
            # we should clean exception information in Python 2, before user's code execution
            sys.exc_clear()

        # Notify that the main thread is created.
        # self.notify_thread_created(thread_id, t)

        if set_trace:
            self.enable_tracing()

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

    def wait_for_commands(self, globals):
        pass

    # trace_dispatch = _trace_dispatch
    # frame_eval_func = frame_eval_func
    # dummy_trace_dispatch = dummy_trace_dispatch

    # noinspection SpellCheckingInspection
    @staticmethod
    def stoptrace():
        """A proxy method for calling :func:`stoptrace` from the modules where direct import
        is impossible because, for example, a circular dependency."""
        pass


def set_debug(setup):
    setup['DEBUG_RECORD_SOCKET_READS'] = True
    setup['DEBUG_TRACE_BREAKPOINTS'] = 1
    setup['DEBUG_TRACE_LEVEL'] = 3


# =======================================================================================================================
# settrace
# =======================================================================================================================
def settrace(
        host=None,
        stdoutToServer=False,
        stderrToServer=False,
        port=5678,
        suspend=True,
        trace_only_current_thread=False,
        overwrite_prev_trace=False,
        patch_multiprocessing=False,
        stop_at_frame=None,
):
    '''Sets the tracing function with the pydev debug function and initializes needed facilities.

    @param host: the user may specify another host, if the debug server is not in the same machine (default is the local
        host)

    @param stdoutToServer: when this is true, the stdout is passed to the debug server

    @param stderrToServer: when this is true, the stderr is passed to the debug server
        so that they are printed in its console and not in this process console.

    @param port: specifies which port to use for communicating with the server (note that the server must be started
        in the same port). @note: currently it's hard-coded at 5678 in the client

    @param suspend: whether a breakpoint should be emulated as soon as this function is called.

    @param trace_only_current_thread: determines if only the current thread will be traced or all current and future
        threads will also have the tracing enabled.

    @param overwrite_prev_trace: deprecated

    @param patch_multiprocessing: if True we'll patch the functions which create new processes so that launched
        processes are debugged.

    @param stop_at_frame: if passed it'll stop at the given frame, otherwise it'll stop in the function which
        called this method.
    '''
    _set_trace_lock.acquire()
    try:
        _locked_settrace(
            host,
            stdoutToServer,
            stderrToServer,
            port,
            suspend,
            trace_only_current_thread,
            patch_multiprocessing,
            stop_at_frame,
        )
    finally:
        _set_trace_lock.release()


_set_trace_lock = thread.allocate_lock()


def _locked_settrace(
        host,
        stdoutToServer,
        stderrToServer,
        port,
        suspend,
        trace_only_current_thread,
        patch_multiprocessing,
        stop_at_frame,
):
    if SetupHolder.setup is None:
        setup = {
            'client': host,  # dispatch expects client to be set to the host address when server is False
            'server': False,
            'port': int(port),
            'multiprocess': patch_multiprocessing,
        }
        SetupHolder.setup = setup

    if patch_multiprocessing:
        try:
            import PyQtInspect.pqi_monkey
        except:
            pass
        else:
            PyQtInspect.pqi_monkey.patch_new_process_functions()

    try:
        print('pydev_monkey_qt')
        import monkey_qt
    except:
        pass
    else:
        monkey_qt.patch_qt("pyqt5")

    global connected
    global bufferStdOutToServer
    global bufferStdErrToServer


# =======================================================================================================================
# main
# =======================================================================================================================
def usage(do_exit=True, exit_code=0):
    sys.stdout.write('Usage:\n')
    sys.stdout.write('\tpydevd.py --port N [(--client hostname) | --server] --file executable [file_options]\n')
    if do_exit:
        sys.exit(exit_code)


def main():
    # parse the command line. --file is our last argument that is required
    try:
        from _pqi_bundle.pqi_command_line_handling import process_command_line
        setup = process_command_line(sys.argv)
        SetupHolder.setup = setup
    except ValueError:
        traceback.print_exc()
        usage(exit_code=1)

    debugger = PyDB()

    import PyQtInspect.pqi_monkey

    if setup['multiprocess']:
        PyQtInspect.pqi_monkey.patch_new_process_functions()

    is_module = setup['module']

    enable_qt_support("pyqt5")
    debugger.run(setup["file"], None, None, is_module)


if __name__ == '__main__':
    main()
