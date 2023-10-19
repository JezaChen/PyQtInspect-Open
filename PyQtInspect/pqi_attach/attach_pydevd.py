import sys
import os


def process_command_line(argv):
    setup = {}
    setup['port'] = 5678  # Default port for PyDev remote debugger
    setup['pid'] = 0
    setup['host'] = '127.0.0.1'
    setup['protocol'] = ''
    setup['debug-mode'] = ''

    i = 0
    while i < len(argv):
        if argv[i] == '--port':
            del argv[i]
            setup['port'] = int(argv[i])
            del argv[i]

        elif argv[i] == '--pid':
            del argv[i]
            setup['pid'] = int(argv[i])
            del argv[i]

        elif argv[i] == '--host':
            del argv[i]
            setup['host'] = argv[i]
            del argv[i]

        elif argv[i] == '--protocol':
            del argv[i]
            setup['protocol'] = argv[i]
            del argv[i]

    if not setup['pid']:
        sys.stderr.write('Expected --pid to be passed.\n')
        sys.exit(1)
    return setup


def main(setup):
    sys.path.append(os.path.dirname(__file__))
    import add_code_to_python_process
    import psutil

    dirname = os.path.dirname
    pydevd_dirname = dirname(dirname(dirname(__file__)))

    show_debug_info_on_target_process = 0

    if sys.platform == 'win32':
        setup['pythonpath'] = pydevd_dirname.replace('\\', '/')
        setup['pythonpath2'] = os.path.dirname(__file__).replace('\\', '/')
        path2_rel_path = os.path.relpath(setup['pythonpath2'], pydevd_dirname).replace('\\', '/')

        if "cc_sub" in psutil.Process(setup['pid']).name():
            print("cc_sub process, compile pqi module")
            cc_sub_exe = psutil.Process(setup['pid']).exe()
            compile_tool_path = os.path.join(pydevd_dirname, "compile_pqi.py")

            import subprocess
            cc_sub_compiled_pqi_path = os.path.join(pydevd_dirname, 'cc_sub_compiled_pqi').replace('\\', '/')
            subprocess.Popen(f"{cc_sub_exe} {compile_tool_path} {cc_sub_compiled_pqi_path}/PyQtInspect",
                             shell=True).wait()

            setup['pythonpath'] = cc_sub_compiled_pqi_path
            setup['pythonpath2'] = os.path.join(cc_sub_compiled_pqi_path, path2_rel_path).replace('\\', '/')

        python_code = '''import sys;
sys.path.append("%(pythonpath)s");
sys.path.append("%(pythonpath2)s");
import attach_script;
attach_script.attach(port=%(port)s, host="%(host)s", protocol="%(protocol)s");
'''.replace('\r\n', '').replace('\r', '').replace('\n', '')
    else:
        setup['pythonpath'] = pydevd_dirname
        setup['pythonpath2'] = os.path.dirname(__file__)
        # We have to pass it a bit differently for gdb
        python_code = '''import sys;
sys.path.append(\\\"%(pythonpath)s\\\");
sys.path.append(\\\"%(pythonpath2)s\\\");
import attach_script;
attach_script.attach(port=%(port)s, host=\\\"%(host)s\\\", protocol=\\\"%(protocol)s\\\", debug_mode=\\\"%(debug-mode)s\\\");
'''.replace('\r\n', '').replace('\r', '').replace('\n', '')

    python_code = python_code % setup
    add_code_to_python_process.run_python_code(
        setup['pid'], python_code, connect_debugger_tracing=True, show_debug_info=show_debug_info_on_target_process)


if __name__ == '__main__':
    main(process_command_line(sys.argv[1:]))
