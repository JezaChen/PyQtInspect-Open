# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/18 15:00
# Description: 
# ==============================================
from PyQtInspect._pqi_common.pqi_setup_holder import SetupHolder


class ArgOutputterWithParam:
    """
    Tool class for arguments which have a parameter and needs to be outputted
    """
    def __init__(self, arg_name, default_val=None):
        self.arg_name = arg_name
        self.arg_v_rep = '--%s' % (arg_name,)
        self.default_val = default_val

    def to_argv(self, lst, setup):
        v = setup.get(self.arg_name)
        if v is not None and v != self.default_val:
            lst.append(self.arg_v_rep)
            lst.append('%s' % (v,))


class ArgOutputterBool:
    """
    Outputter for boolean flags.
    If the value is True, output the flag.
    """

    def __init__(self, arg_name, default_val=False):
        self.arg_name = arg_name
        self.arg_v_rep = '--%s' % (arg_name,)
        # I think the default value is usually False...
        self.default_val = default_val

    def to_argv(self, lst, setup):
        v = setup.get(self.arg_name)
        if v or self.default_val:
            lst.append(self.arg_v_rep)


class ArgOutputterWithEqualSign(ArgOutputterWithParam):
    """ Outputter which needs to be outputted with '=' sign in `to_argv` (e.g.: --qt-support=auto)
    """
    def to_argv(self, lst, setup):
        v = self.get_val(setup)
        if v is not None and v != self.default_val:
            lst.append('%s=%s' % (self.arg_v_rep, v))

    def get_val(self, setup):
        return setup.get(self.arg_name)


class QtSupportArgOutputter(ArgOutputterWithEqualSign):
    """
    Special outputter for `qt-support` argument

    Since PyQtInspect supports automatic detection of the Qt library,
      once detection succeeds it sets the value of `qt-support` to the specific library name.
    To allow spawning child processes that use a different Qt library
      (e.g., launching a PyQt6 program from a PyQt5 program),
      this argument needs special handling when being passed to the child process:
      if in automatic detection mode (the flag `is-auto-discover-qt-lib` is set),
      pass `--qt-support=auto`; otherwise pass the concrete library name.
    """
    def get_val(self, setup):
        if setup.get(SetupHolder.KEY_IS_AUTO_DISCOVER_QT_LIB):
            return 'auto'  # auto-discovery mode
        return setup.get(self.arg_name)


class ArgHandlerWithParam(ArgOutputterWithParam):
    """
    Handler for arguments which have a parameter and needs to be outputted/parsed from command line
    (e.g.: --port 19394)
    Handler = Outputter + Parser
    """

    def __init__(self, arg_name, convert_val=None, default_val=None):
        super().__init__(arg_name, default_val)
        self.convert_val = convert_val

    def handle_argv(self, argv, i, setup):
        assert argv[i] == self.arg_v_rep
        del argv[i]

        val = argv[i]
        if self.convert_val:
            val = self.convert_val(val)

        setup[self.arg_name] = val
        del argv[i]


class ArgHandlerBool(ArgOutputterBool):
    """
    If a given flag is received, mark it as 'True' in setup.
    """

    def handle_argv(self, argv, i, setup):
        assert argv[i] == self.arg_v_rep
        del argv[i]
        setup[self.arg_name] = True


ACCEPTED_ARG_HANDLERS = [
    ArgHandlerWithParam(SetupHolder.KEY_PORT, int, 19394),  # --port <client port=19394>
    ArgHandlerWithParam(SetupHolder.KEY_CLIENT, default_val='127.0.0.1'),  # --client <client ip=127.0.0.1>
    ArgHandlerWithParam(SetupHolder.KEY_STACK_MAX_DEPTH, int, 0),  # --stack-max-depth <depth=0>

    ArgHandlerBool(SetupHolder.KEY_DIRECT),  # --direct
    ArgHandlerBool(SetupHolder.KEY_MULTIPROCESS),  # --multiprocess
    ArgHandlerBool(SetupHolder.KEY_MODULE),  # --module
    ArgHandlerBool(SetupHolder.KEY_HELP),  # --help, print help and exit
    ArgHandlerBool(SetupHolder.KEY_SHOW_PQI_STACK),  # --show-pqi-stack
    ArgHandlerBool(SetupHolder.KEY_IS_DEBUG_MODE),  # --DEBUG
]

ARGV_REP_TO_HANDLER = {}
for handler in ACCEPTED_ARG_HANDLERS:
    ARGV_REP_TO_HANDLER[handler.arg_v_rep] = handler


ARG_OUTPUTTERS = [
    # The accepted arg handlers also act as outputters
    *ACCEPTED_ARG_HANDLERS,

    # === EXTRA OUTPUTTERS (not handled in command line parsing) ===
    # The original pydevd does not support subprocesses with qt parameters, add it here
    # Update since v0.4.1: Default value is changed to 'auto' instead of 'pyqt5'
    # It does not handle argument parsing; only used to patch arguments for child processes
    # The actual parsing for `qt-support` is done in `process_command_line`
    QtSupportArgOutputter(SetupHolder.KEY_QT_SUPPORT, default_val='auto'),  # --qt-support=<mode>
]


def get_pydevd_file(executable_path):
    import PyQtInspect.pqi

    f = PyQtInspect.pqi.__file__
    if f.endswith('.pyc'):
        f = f[:-1]
    elif f.endswith('$py.class'):
        f = f[:-len('$py.class')] + '.py'

    return f


def setup_to_argv(executable_path, setup):
    '''
    :param dict setup:
        A dict previously gotten from process_command_line.

    :note: does not handle --file nor --DEBUG.
    '''

    filtered = {
        # Bug fixed 20250302
        # We don't pass this parameter to the subprocess, otherwise, when a new process is created,
        #   it'd try to launch a new debugger, which is not what we want.
        'direct',
    }

    ret = [get_pydevd_file(executable_path)]

    for outputter in ARG_OUTPUTTERS:
        if outputter.arg_name in setup and outputter.arg_name not in filtered:
            outputter.to_argv(ret, setup)
    return ret


def process_command_line(argv):
    """ parses the arguments.
        removes our arguments from the command line """
    setup = {}
    for handler in ACCEPTED_ARG_HANDLERS:
        setup[handler.arg_name] = handler.default_val
    setup[SetupHolder.KEY_FILE] = ''
    setup[SetupHolder.KEY_SHOW_PQI_STACK] = False
    setup[SetupHolder.KEY_QT_SUPPORT] = 'auto'  # Changed since v0.4.1, previously was 'pyqt5'

    i = 0
    del argv[0]
    while i < len(argv):
        handler = ARGV_REP_TO_HANDLER.get(argv[i])
        if handler is not None:
            handler.handle_argv(argv, i, setup)

        elif argv[i].startswith('--qt-support'):
            # The --qt-support is special because we want to keep backward compatibility:
            # Previously, just passing '--qt-support' meant that we should use the auto-discovery mode
            # whereas now, if --qt-support is passed, it should be passed as --qt-support=<mode>, where
            # mode can be one of 'auto', 'pyqt5', 'pyqt6', 'pyside2', 'pyside6'.
            if argv[i] == '--qt-support':
                # If just `--qt-support` is passed, it means auto-discovery mode
                setup[SetupHolder.KEY_QT_SUPPORT] = 'auto'

            elif argv[i].startswith('--qt-support='):
                qt_support = argv[i][len('--qt-support='):]
                qt_support = qt_support.lower()
                # ONLY SUPPORTS PYQT5/6 AND PYSIDE2/6
                # `auto` means that PyQtInspect will detect the Qt bindings automatically.
                valid_modes = ('auto', 'pyqt5', 'pyqt6', 'pyside2', 'pyside6')
                if qt_support not in valid_modes:
                    raise ValueError("qt-support mode invalid: " + qt_support)
                else:
                    setup[SetupHolder.KEY_QT_SUPPORT] = qt_support
            else:
                raise ValueError("Unexpected definition for qt-support flag: " + argv[i])

            del argv[i]

        elif argv[i] == '--file':
            # --file is special because it's the last one (so, no handler for it).
            del argv[i]
            setup[SetupHolder.KEY_FILE] = argv[i]
            i = len(argv)  # pop out, file is our last argument

        else:
            raise ValueError("Unexpected option: " + argv[i])
    return setup
