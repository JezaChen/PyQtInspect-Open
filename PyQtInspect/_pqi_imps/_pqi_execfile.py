import marshal
import sys

# todo
if sys.version_info < (3, 7):
    BYTE_CODE_OFFSET = 12
elif sys.version_info <= (3, 13):
    BYTE_CODE_OFFSET = 16


def get_magic_number_of_executable():
    import importlib.util
    return importlib.util.MAGIC_NUMBER


def exec_pyc(pyc_file_path: str, globals_=None, locals_=None):
    if globals_ is None:
        globals_ = {}
    globals_.update({
        '__name__': '__main__',
        '__file__': pyc_file_path,
    })
    with open(pyc_file_path, 'rb') as pyc:
        pyc_magic_number = pyc.read(4)
        if pyc_magic_number != get_magic_number_of_executable():
            raise ValueError(f'The magic number of {pyc_file_path} is not equal to the magic number of executable.')

        pyc.seek(BYTE_CODE_OFFSET)
        content = pyc.read()
        code = marshal.loads(content)
        exec(code, globals_, locals_)


def compile_file(file_path):
    import py_compile
    py_compile.compile(file_path, cfile=file_path + 'c')


if __name__ == '__main__':
    exec_pyc('example.pyc')
