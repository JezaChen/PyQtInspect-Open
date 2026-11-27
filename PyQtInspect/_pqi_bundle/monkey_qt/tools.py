__all__ = ["snake_getvalue", "snake_getfunc", "snake_setattr", "unsnake"]

import re
import string
from functools import lru_cache

_to_snake = str.maketrans({char: f'_{char.lower()}' for char in string.ascii_uppercase})


@lru_cache(512)
def getter_name(name: str, /) -> str:
    name = name.removeprefix('set')
    if name[0] == '_':
        return name[1:]
    return name[0].lower() + name[1:]


_test_names = [
    "objectName",  # QObject
    "isAccepted",  # QEvent
]
_test_snake_names = [name.translate(_to_snake) for name in _test_names]


def name_(obj, name: str, /):
    for normal_name, snake_name in zip(_test_names, _test_snake_names):
        if getattr(obj, normal_name, None) is not None:
            return name
        if getattr(obj, snake_name, None) is not None:
            return name.translate(_to_snake)
    return name


def snake_getvalue(obj, name: str, /):
    name = name_(obj, name)
    if isinstance(getattr(type(obj), name), property):
        return getattr(obj, name)
    return getattr(obj, name)()


def snake_getfunc(obj, name: str, /):
    return getattr(obj, name_(obj, name))


def snake_setattr(obj, name: str, value, /):
    assert name.startswith('set')
    name = name_(obj, name)
    try:
        getter = getattr(type(obj), getter_name(name))
    except AttributeError:
        getter = None
    if isinstance(getter, property):
        setattr(obj, name, value)
    else:
        getattr(obj, name)(value)


@lru_cache(512)
def unsnake(text: str) -> str:
    if "_" not in text:
        return text
    return re.sub(r'_([a-z])', lambda m: m.group(1).upper(), text)
