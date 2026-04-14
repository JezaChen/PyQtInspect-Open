import typing as _typing

from . import _base
from PyQtInspect._pqi_bundle.pqi_contants import IS_WINDOWS, IS_MACOS

def _get_setup() -> _typing.Type[_base.Setup]:
    if IS_WINDOWS:
        from ._windows import WindowsSetup as PlatformSetup
    elif IS_MACOS:
        from ._macos import MacOSSetup as PlatformSetup
    else:
        from ._base import DummySetup as PlatformSetup
    return PlatformSetup

def setup_platform():
    """ Set up platform-specific configurations. """
    PlatformSetup = _get_setup()
    PlatformSetup.setup()
