# -*- encoding:utf-8 -*-
# ==============================================
# Author: 陈建彰
# Time: 2023/10/11 18:39
# Description: 
# ==============================================
import compileall
import sys


def compile_pqi_module():
    compileall.compile_dir("PyQtInspect", force=True)


def copy_pyc_files_to(dest_dir: str):
    import os
    import shutil
    for root, dirs, files in os.walk("PyQtInspect"):
        for file in files:
            if file.endswith(".pyc"):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, src_file)
                # remove `cpython-xxx`
                dest_file = dest_file.replace("cpython-37.", "")
                # remove `__pycache__`
                dest_file = dest_file.replace("__pycache__\\", "")
                sub_dir = os.path.dirname(dest_file)
                if not os.path.exists(sub_dir):
                    os.makedirs(sub_dir)

                shutil.copy(src_file, dest_file)


def compile_pqi_module_new(output_dir):
    import os
    import py_compile

    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PyQtInspect")

    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith(".py"):
                src_file = os.path.join(root, file)

                # remove the module path
                src_relative_path = os.path.relpath(src_file, module_path)

                dest_file = os.path.join(output_dir, src_relative_path + "c")  # xxx/xxx.py -> xxx/xxx.pyc
                sub_dir = os.path.dirname(dest_file)
                if not os.path.exists(sub_dir):
                    os.makedirs(sub_dir)
                py_compile.compile(src_file, dest_file)


if __name__ == '__main__':
    dstPath = sys.argv[1]
    compile_pqi_module_new(dstPath)
