from __future__ import nested_scopes

import os
import sys

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle._pqi_monkey_qt_helpers import patch_QtWidgets
from PyQtInspect._pqi_bundle.pqi_contants import IS_WINDOWS
from PyQtInspect._pqi_bundle.pqi_monkey import str_to_args_windows, is_python, patch_args


def set_trace_in_qt():
    # from _pydevd_bundle.pydevd_comm import get_global_debugger
    # debugger = get_global_debugger()
    # if debugger is not None:
    #     threading.current_thread()  # Create the dummy thread for qt.
    #     debugger.enable_tracing()
    pass


IS_PY38 = sys.version_info[0] == 3 and sys.version_info[1] == 8

_patched_qt = False

_EMPTY = object()


def _iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def _qt_split_command(command):
    """ python reimplement of splitCommand in Qt """
    args = []
    tmp = ""
    quoteCount = 0
    inQuote = False

    for i in range(len(command)):
        if command[i] == '"':
            quoteCount += 1
            if quoteCount == 3:
                quoteCount = 0
                tmp += command[i]
            continue
        if quoteCount:
            if quoteCount == 1:
                inQuote = not inQuote
            quoteCount = 0
        if not inQuote and command[i].isspace():
            if tmp:
                args.append(tmp)
                tmp = ""
        else:
            tmp += command[i]
    if tmp:
        args.append(tmp)

    return args


def patch_qt(qt_support_mode, is_attach=False):
    '''
    This method patches qt (PySide, PyQt4, PyQt5) so that we have hooks to set the tracing for QThread.
    '''
    if not qt_support_mode:
        return

    if qt_support_mode is True or qt_support_mode == 'True':
        # do not break backward compatibility
        qt_support_mode = 'auto'

    if qt_support_mode == 'auto':
        qt_support_mode = os.getenv('PYDEVD_PYQT_MODE', 'auto')

    # Avoid patching more than once
    global _patched_qt
    if _patched_qt:
        return

    _patched_qt = True

    if qt_support_mode == 'auto':

        patch_qt_on_import = None
        try:
            if IS_PY38:
                raise ImportError
            import PySide6
            qt_support_mode = 'pyside6'
        except:
            try:
                # PY-50959
                # Problem:
                # 1. We have Python 3.8;
                # 2. PyQt compatible = Auto or PySide2;
                # 3. We try to import numpy, we get "AttributeError: module 'numpy.core' has no attribute 'numerictypes'"
                #
                # Solution:
                # We decided to turn off patching for PySide2 if we have Python 3.8
                # Here we skip 'import PySide2' and keep trying to import another qt libraries
                if IS_PY38:
                    raise ImportError
                import PySide2  # @UnresolvedImport @UnusedImport
                qt_support_mode = 'pyside2'
            except:
                try:
                    import Pyside  # @UnresolvedImport @UnusedImport
                    qt_support_mode = 'pyside'
                except:
                    try:
                        import PyQt6  # @UnresolvedImport @UnusedImport
                        qt_support_mode = 'pyqt6'
                    except:
                        try:
                            import PyQt5  # @UnresolvedImport @UnusedImport
                            qt_support_mode = 'pyqt5'
                        except:
                            try:
                                import PyQt4  # @UnresolvedImport @UnusedImport
                                qt_support_mode = 'pyqt4'
                            except:
                                return

    if qt_support_mode == 'pyside6':
        if IS_PY38:
            return
        try:
            import PySide6.QtCore  # @UnresolvedImport
            import PySide6.QtWidgets  # @UnresolvedImport
            import PySide6.QtGui  # @UnresolvedImport

            _internal_patch_qt(PySide6.QtCore, qt_support_mode)
            _internal_patch_qt_widgets(PySide6, qt_support_mode, is_attach)
        except:
            return
    elif qt_support_mode == 'pyside2':
        # PY-50959
        # We can get here only if PyQt compatible = PySide2, in this case we should return
        # See comment above about PY-50959
        if IS_PY38:
            return
        try:
            import PySide2.QtCore  # @UnresolvedImport
            import PySide2.QtWidgets  # @UnresolvedImport
            import PySide2.QtGui  # @UnresolvedImport

            _internal_patch_qt(PySide2.QtCore, qt_support_mode)
            _internal_patch_qt_widgets(PySide2, qt_support_mode, is_attach)
        except:
            return

    elif qt_support_mode == 'pyside':
        try:
            import PySide.QtCore  # @UnresolvedImport
            _internal_patch_qt(PySide.QtCore, qt_support_mode)
        except:
            return

    elif qt_support_mode == 'pyqt6':
        try:
            import PyQt6.QtCore  # @UnresolvedImport
            import PyQt6.QtWidgets  # @UnresolvedImport
            import PyQt6.QtGui  # @UnresolvedImport

            _internal_patch_qt(PyQt6.QtCore)
            _internal_patch_qt_widgets(PyQt6, qt_support_mode, is_attach)
        except:
            return

    elif qt_support_mode == 'pyqt5':
        try:
            import PyQt5.QtCore  # @UnresolvedImport
            import PyQt5.QtWidgets  # @UnresolvedImport
            import PyQt5.QtGui  # @UnresolvedImport

            _internal_patch_qt(PyQt5.QtCore)
            _internal_patch_qt_widgets(PyQt5, qt_support_mode, is_attach)
        except Exception:
            pqi_log.error('Error patching PyQt5', exc_info=True)
            return

    # todo PyQt4
    # elif qt_support_mode == 'pyqt4':
    #     # Ok, we have an issue here:
    #     # PyDev-452: Selecting PyQT API version using sip.setapi fails in debug mode
    #     # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    #     # Mostly, if the user uses a different API version (i.e.: v2 instead of v1),
    #     # that has to be done before importing PyQt4 modules (PySide/PyQt5 don't have this issue
    #     # as they only implements v2).
    #     patch_qt_on_import = 'PyQt4'
    #     def get_qt_core_module():
    #         import PyQt4.QtCore  # @UnresolvedImport
    #         return PyQt4.QtCore
    #     _patch_import_to_patch_pyqt_on_import(patch_qt_on_import, get_qt_core_module)

    else:
        raise ValueError('Unexpected qt support mode: %s' % (qt_support_mode,))


# def _patch_import_to_patch_pyqt_on_import(patch_qt_on_import, get_qt_core_module):
#     # I don't like this approach very much as we have to patch __import__, but I like even less
#     # asking the user to configure something in the client side...
#     # So, our approach is to patch PyQt4 right before the user tries to import it (at which
#     # point he should've set the sip api version properly already anyways).
#
#     dotted = patch_qt_on_import + '.'
#     original_import = __import__
#
#     from _pydev_imps._pydev_sys_patch import patch_sys_module, patch_reload, cancel_patches_in_sys_module
#
#     patch_sys_module()
#     patch_reload()
#
#     def patched_import(name, *args, **kwargs):
#         if patch_qt_on_import == name or name.startswith(dotted):
#             builtins.__import__ = original_import
#             cancel_patches_in_sys_module()
#             _internal_patch_qt(get_qt_core_module()) # Patch it only when the user would import the qt module
#         return original_import(name, *args, **kwargs)
#
#     import sys
#     if sys.version_info[0] >= 3:
#         import builtins # Py3
#     else:
#         import __builtin__ as builtins
#
#     builtins.__import__ = patched_import


def _internal_patch_qt(QtCore, qt_support_mode='auto'):
    _original_thread_init = QtCore.QThread.__init__
    _original_runnable_init = QtCore.QRunnable.__init__
    _original_QThread = QtCore.QThread
    # === QProcess ===
    # -- class --
    _original_QProcess = QtCore.QProcess
    # -- pure static methods --
    _original_QProcess_execute = QtCore.QProcess.execute
    # -- hybrid methods --
    _original_QProcess_startDetached = QtCore.QProcess.startDetached

    class FuncWrapper:
        def __init__(self, original):
            self._original = original

        def __call__(self, *args, **kwargs):
            set_trace_in_qt()
            return self._original(*args, **kwargs)

    class StartedSignalWrapper(QtCore.QObject):  # Wrapper for the QThread.started signal

        try:
            _signal = QtCore.Signal()  # @UndefinedVariable
        except:
            _signal = QtCore.pyqtSignal()  # @UndefinedVariable

        def __init__(self, thread, original_started):
            QtCore.QObject.__init__(self)
            self.thread = thread
            self.original_started = original_started
            if qt_support_mode in ('pyside', 'pyside2', 'pyside6'):
                self._signal = original_started
            else:
                self._signal.connect(self._on_call)
                self.original_started.connect(self._signal)

        def connect(self, func, *args, **kwargs):
            if qt_support_mode in ('pyside', 'pyside2', 'pyside6'):
                return self._signal.connect(FuncWrapper(func), *args, **kwargs)
            else:
                return self._signal.connect(func, *args, **kwargs)

        def disconnect(self, *args, **kwargs):
            return self._signal.disconnect(*args, **kwargs)

        def emit(self, *args, **kwargs):
            return self._signal.emit(*args, **kwargs)

        def _on_call(self, *args, **kwargs):
            set_trace_in_qt()

    class ThreadWrapper(QtCore.QThread):  # Wrapper for QThread

        def __init__(self, *args, **kwargs):
            _original_thread_init(self, *args, **kwargs)

            # In PyQt5 the program hangs when we try to call original run method of QThread class.
            # So we need to distinguish instances of QThread class and instances of QThread inheritors.
            if self.__class__.run == _original_QThread.run:
                self.run = self._pqi_exec_run
            else:
                # MUST ADD PREFIX '_pqi_' to the method name, otherwise it will cause infinite recursion
                # 如果使用和pydevd相同的变量名
                # 则根据继承关系 QThead的子类 -> QThreadWrapper in pqi -> QThreadWrapper in pydevd -> QThread
                # pqi中的self._pqi_original_run会指向pydevd中的self.run,
                # 而此时self.run已经被pqi中的self._pqi_new_run(in pqi!!! pqi层的QThreadWrapper同名方法覆盖了pydevd层的方法)替换
                # 因此会无限递归pqi层面的QThreadWrapper的self._pqi_new_run方法
                self._pqi_original_run = self.run
                self.run = self._pqi_new_run
            self._original_started = self.started
            self.started = StartedSignalWrapper(self, self.started)

        # MUST ADD PREFIX '_pqi_' to the method name, otherwise it will cause infinite recursion
        def _pqi_exec_run(self):
            set_trace_in_qt()
            self.exec_()
            return None

        def _pqi_new_run(self):
            set_trace_in_qt()
            return self._pqi_original_run()

    class RunnableWrapper(QtCore.QRunnable):  # Wrapper for QRunnable

        def __init__(self, *args):
            _original_runnable_init(self, *args)

            self._pqi_original_run = self.run
            self.run = self._pqi_new_run

        def _pqi_new_run(self):
            set_trace_in_qt()
            return self._pqi_original_run()

    class QProcessWrapper(QtCore.QProcess):  # Wrapper for QProcess
        # todo: for Qt6, QProcess has some new methods, need to be wrapped in the future
        # Attention: May only support PyQt5!!!
        # Attention: May only support Windows!!!
        def __init__(self, *args):
            _original_QProcess.__init__(self, *args)

            # For patching
            self._pqi_original_program = None
            self._pqi_original_arguments = None

            # Original methods
            self._pqi_original_start = self.start
            self._pqi_original_setProgram = self.setProgram
            self._pqi_original_setArguments = self.setArguments
            self._pqi_original_program_method = self.program
            self._pqi_original_arguments_method = self.arguments
            self._pqi_original_start_detached = self.startDetached
            self._pqi_original_open = self.open

            # Patched methods
            # Cannot override methods directly
            # Otherwise, the above _pqi_original_*** method would point to the overridden method.
            # (The class is first defined and then __init__ is called.)
            self.setArguments = self._pqi_new_setArguments
            self.setProgram = self._pqi_new_setProgram
            self.start = self._pqi_new_start
            self.open = self._pqi_new_open
            self.program = self._pqi_new_program_method
            self.arguments = self._pqi_new_arguments_method

        def _pqi_new_setProgram(self, program):
            self._pqi_original_program = program
            self._pqi_original_setProgram(program)

        def _pqi_new_setArguments(self, arguments):
            self._pqi_original_arguments = arguments
            self._pqi_original_setArguments(arguments)

        def _pqi_new_program_method(self):
            if self._pqi_original_program is None:
                return ''
            return self._pqi_original_program

        def _pqi_new_arguments_method(self):
            if self._pqi_original_arguments is None:
                return []
            return self._pqi_original_arguments

        def _pqi_patch_original_program_and_args(self):
            if self._pqi_original_program is None or self._pqi_original_arguments is None:
                # If the QProcess instance is reused, we need to restore the original program and arguments
                # todo
                # 如果复用, 则必须调用start、startDetached、open方法, 这种时候self._pqi_original_arguments都不会为None
                # 且 self._pqi_original_program 和 self._pqi_original_arguments 可保证是原始的参数
                # (都拦截到了, 且method3的调用前需要setProgram和setArguments方法)
                #
                # 没有复用，method3的调用有两个前提情况
                # 前面调用过setProgram、setArguments方法: self._pqi_original_program和self._pqi_original_arguments都不为None
                # 没有调用: 则self._pqi_original_program和self._pqi_original_arguments都为None, 这里会调用原始的program和arguments方法
                self._pqi_original_program = self._pqi_original_program_method()
                self._pqi_original_arguments = self._pqi_original_arguments_method()
            arguments = [self._pqi_original_program] + self._pqi_original_arguments
            patched_arguments = patch_args(arguments)
            self._pqi_original_setProgram(patched_arguments[0])
            self._pqi_original_setArguments(patched_arguments[1:])

        def _pqi_new_start(self, __arg1=_EMPTY, __arg2=_EMPTY, __arg3=_EMPTY, *args, **kwargs):  # todo use custom objects
            """
            start(self, program: Optional[str], arguments: Iterable[Optional[str]], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
            start(self, command: Optional[str], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
            start(self, mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
            """
            if args or kwargs:  # if there are other params, raise an error
                raise RuntimeError('Not supported')

            def _patch_method1():
                # start(self, program: Optional[str], arguments: Iterable[Optional[str]], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
                nonlocal __arg1, __arg2

                self._pqi_original_program, self._pqi_original_arguments = __arg1, __arg2
                _arguments = [self._pqi_original_program] + self._pqi_original_arguments
                _patched_arguments = patch_args(_arguments)
                return _patched_arguments

            def _patch_method2():
                # start(self, command: Optional[str], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
                nonlocal __arg1
                _arg_str = __arg1
                _arguments = (str_to_args_windows if IS_WINDOWS else _qt_split_command)(__arg1)
                self._pqi_original_program, *self._pqi_original_arguments = _arguments
                if _arguments and is_python(_arguments[0]):
                    _arg_str = ' '.join(patch_args(_arguments))
                return _arg_str

            def _patched_method3():
                # start(self, mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
                self._pqi_patch_original_program_and_args()

            if __arg1 is _EMPTY and __arg2 is _EMPTY and __arg3 is _EMPTY:  # no params
                # start(self, mode = QIODevice.ReadWrite)
                _patched_method3()
                return self._pqi_original_start()
            elif __arg2 is _EMPTY and __arg3 is _EMPTY:  # single param
                if isinstance(__arg1, str):  # command
                    # start(self, command: Optional[str], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
                    arg_str = _patch_method2()
                    return self._pqi_original_start(arg_str)
                else:  # mode?
                    # start(self, mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag])
                    _patched_method3()
                    return self._pqi_original_start(__arg1)
            elif __arg3 is _EMPTY:  # two params
                if _iterable(__arg2):
                    # start(self, program: Optional[str], arguments: Iterable[Optional[str]], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag] = QIODevice.ReadWrite)
                    patched_arguments = _patch_method1()
                    return self._pqi_original_start(patched_arguments[0], patched_arguments[1:])
                else:
                    # start(self, command: Optional[str], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag])
                    arg_str = _patch_method2()
                    return self._pqi_original_start(arg_str, __arg2)
            else:  # three params
                # start(self, program: Optional[str], arguments: Iterable[Optional[str]], mode: Union[QIODevice.OpenMode, QIODevice.OpenModeFlag])
                patched_arguments = _patch_method1()
                return self._pqi_original_start(patched_arguments[0], patched_arguments[1:], __arg3)

        def _pqi_new_open(self, mode=_EMPTY, *args, **kwargs):
            # we don't specify the default param mode as QIODevice.ReadWrite,
            # because it may be different in different qt versions.
            self._pqi_patch_original_program_and_args()
            if mode is _EMPTY:
                return self._pqi_original_open()
            return self._pqi_original_open(mode, *args, **kwargs)

        # Patch static methods
        @staticmethod
        def execute(__arg1, arguments=_EMPTY):
            """
            execute(program: str, arguments: Iterable[str]) -> int
            execute(command: str) -> int # !!! it is a command!
            """
            if arguments is _EMPTY:  # __arg1 is a command
                arguments = (str_to_args_windows if IS_WINDOWS else _qt_split_command)(__arg1)
            else:  # __arg1 is a program
                arguments = [__arg1] + arguments
            patched_arguments = patch_args(arguments)
            # call the original execute
            return _original_QProcess_execute(patched_arguments[0], patched_arguments[1:])

        # Patch hybrid methods (static or member)
        def startDetached(__arg1=_EMPTY, __arg2=_EMPTY, __arg3=_EMPTY, *args, **kwargs):
            """
            startDetached(program: Optional[str], arguments: Iterable[Optional[str]], workingDirectory: Optional[str]) -> (bool, Optional[int])
            startDetached(program: Optional[str], arguments: Iterable[Optional[str]])
            startDetached(command: Optional[str]) #!!! it is a command!
            startDetached(self) -> (bool, Optional[int])
            """
            if args or kwargs:  # if there are other params, raise an error
                raise RuntimeError('Not supported')

            if isinstance(__arg1, _original_QProcess):  # member method
                # startDetached(self) -> (bool, Optional[int])
                if __arg2 is not _EMPTY or __arg3 is not _EMPTY:
                    raise TypeError('startDetached() takes 1 positional argument but 3 were given')
                self = __arg1
                self._pqi_patch_original_program_and_args()
                return _original_QProcess_startDetached(self)
            else:  # static method
                if __arg1 is _EMPTY and __arg2 is _EMPTY and __arg3 is _EMPTY:  # no params
                    # start(self, mode = QIODevice.ReadWrite)
                    return _original_QProcess_startDetached()  # must raise an error
                elif __arg2 is _EMPTY and __arg3 is _EMPTY:  # single param
                    # startDetached(command: Optional[str])
                    command = __arg1
                    arguments = (str_to_args_windows if IS_WINDOWS else _qt_split_command)(command)
                    patched_arguments = patch_args(arguments)
                    patched_command = ' '.join(patched_arguments)
                    return _original_QProcess_startDetached(patched_command)
                elif __arg3 is _EMPTY:  # two params
                    # startDetached(program: Optional[str], arguments: Iterable[Optional[str]])
                    program, arguments = __arg1, __arg2
                    patched_arguments = patch_args([program] + arguments)
                    return _original_QProcess_startDetached(patched_arguments[0], patched_arguments[1:])
                else:  # three params
                    # startDetached(program: Optional[str], arguments: Iterable[Optional[str]], workingDirectory: Optional[str])
                    program, arguments, workingDir = __arg1, __arg2, __arg3
                    patched_arguments = patch_args([program] + arguments)
                    return _original_QProcess_startDetached(patched_arguments[0], patched_arguments[1:], workingDir)

    QtCore.QThread = ThreadWrapper
    QtCore.QRunnable = RunnableWrapper
    QtCore.QProcess = QProcessWrapper


def _internal_patch_qt_widgets(QtModule, qt_support_mode='auto', is_attach=False):
    patch_QtWidgets(QtModule, qt_support_mode, is_attach)
