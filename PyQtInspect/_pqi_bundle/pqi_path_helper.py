# -*- encoding:utf-8 -*-
import pathlib

__all__ = [
    'is_relative_to',
    'find_pqi_module_path',
    'find_compile_pqi_tool',
    'find_pqi_server_gui_entry',
]

_PQI_COMPILE_SUBDIR = '_pqi_compile'
_COMPILE_PQI_TOOL_PY = 'compile_pqi.py'
_PQI_ENTRY_FILE_NAME = 'pqi.py'
_PQI_SERVER_GUI_ENTRY_FILE_NAME = 'pqi_server_gui.py'


# === COMMON UTILS ===

def is_relative_to(path, parent):
    """ check if path is relative to parent """
    path = pathlib.Path(path)
    parent = pathlib.Path(parent)
    try:
        return path.is_relative_to(parent)
    except AttributeError:
        return str(path).startswith(str(parent))


# === FOR PQI SELF ===
_PQI_MODULE_PATH_CACHE = None


def find_pqi_module_path():
    """ get the absolute path of pqi.py """
    global _PQI_MODULE_PATH_CACHE

    if _PQI_MODULE_PATH_CACHE is not None:
        return _PQI_MODULE_PATH_CACHE

    path = pathlib.Path(__file__).parent.parent
    if not path.exists():
        raise FileNotFoundError(f'Cant find PyQtInspect module at {path}')
    result = str(path).replace('\\', '/')
    _PQI_MODULE_PATH_CACHE = result
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


def find_pqi_server_gui_entry():
    """ get the absolute path of pqi_server_gui.py """
    path = pathlib.Path(__file__).parent.parent / _PQI_SERVER_GUI_ENTRY_FILE_NAME
    if not path.exists():
        raise FileNotFoundError(f'Cant find {_PQI_SERVER_GUI_ENTRY_FILE_NAME} at {path}')
    return str(path).replace('\\', '/')

