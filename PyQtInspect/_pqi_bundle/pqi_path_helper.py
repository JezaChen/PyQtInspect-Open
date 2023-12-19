# -*- encoding:utf-8 -*-
import pathlib

_PQI_COMPILE_SUBDIR = '_pqi_compile'
_COMPILE_PQI_TOOL_PY = 'compile_pqi.py'


def find_compile_pqi_tool():
    path = pathlib.Path(__file__).parent.parent / _PQI_COMPILE_SUBDIR / _COMPILE_PQI_TOOL_PY
    if not path.exists():
        raise FileNotFoundError(f'Cant find {_COMPILE_PQI_TOOL_PY} at {path}')
    return str(path).replace('\\', '/')


# === FOR CC ===
_CC_SUB_COMPILED_PQI_SUBDIR = 'cc_sub_compiled_pqi'


def get_cc_sub_compiled_pqi_path():
    path = pathlib.Path(__file__).parent.parent / _PQI_COMPILE_SUBDIR / _CC_SUB_COMPILED_PQI_SUBDIR
    return str(path).replace('\\', '/')
