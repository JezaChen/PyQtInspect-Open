# -*- encoding:utf-8 -*-
import pathlib

__all__ = [
    'find_pqi_entry_file_path',
    'find_compile_pqi_tool',
    'get_cc_sub_compiled_pqi_path',
]

_PQI_COMPILE_SUBDIR = '_pqi_compile'
_COMPILE_PQI_TOOL_PY = 'compile_pqi.py'
_PQI_ENTRY_FILE_NAME = 'pqi.py'

# === FOR PQI SELF ===
_PQI_ENTRY_PATH_CACHE = None


def find_pqi_entry_file_path():
    """ get the absolute path of pqi.py """
    global _PQI_ENTRY_PATH_CACHE

    if _PQI_ENTRY_PATH_CACHE is not None:
        return _PQI_ENTRY_PATH_CACHE

    path = pathlib.Path(__file__).parent.parent / _PQI_ENTRY_FILE_NAME
    if not path.exists():
        raise FileNotFoundError(f'Cant find {_PQI_ENTRY_FILE_NAME} at {path}')
    result = str(path).replace('\\', '/')
    _PQI_ENTRY_PATH_CACHE = result
    return result


# === FOR COMPILE ===
_COMPILE_PQI_TOOL_PATH_CACHE = None


def find_compile_pqi_tool():
    """ get the absolute path of compile_pqi.py """
    global _COMPILE_PQI_TOOL_PATH_CACHE

    if _COMPILE_PQI_TOOL_PATH_CACHE is not None:
        return _COMPILE_PQI_TOOL_PATH_CACHE

    path = pathlib.Path(__file__).parent.parent / _PQI_COMPILE_SUBDIR / _COMPILE_PQI_TOOL_PY
    if not path.exists():
        raise FileNotFoundError(f'Cant find {_COMPILE_PQI_TOOL_PY} at {path}')
    result = str(path).replace('\\', '/')
    _COMPILE_PQI_TOOL_PATH_CACHE = result
    return result


# === FOR CC ===
_CC_SUB_COMPILED_PQI_SUBDIR = 'cc_sub_compiled_pqi'
_CC_SUB_COMPILED_PQI_PATH_CACHE = None


def get_cc_sub_compiled_pqi_path():
    """ get the absolute path of cc_sub_compiled_pqi """
    global _CC_SUB_COMPILED_PQI_PATH_CACHE

    if _CC_SUB_COMPILED_PQI_PATH_CACHE is not None:
        return _CC_SUB_COMPILED_PQI_PATH_CACHE

    path = pathlib.Path(__file__).parent.parent / _PQI_COMPILE_SUBDIR / _CC_SUB_COMPILED_PQI_SUBDIR
    result = str(path).replace('\\', '/')
    _CC_SUB_COMPILED_PQI_PATH_CACHE = result
    return result
