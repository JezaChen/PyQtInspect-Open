import sys as _sys
import typing as _typing

from . import _base

def _get_setup() -> _typing.Type[_base.Setup]:
    if _sys.platform.startswith("win"):
        from ._windows import WindowsSetup as PlatformSetup
    elif _sys.platform == "darwin":
        from ._macos import MacOSSetup as PlatformSetup
    else:
        from ._base import DummySetup as PlatformSetup
    return PlatformSetup

def setup_platform():
    """ Set up platform-specific configurations. """
    PlatformSetup = _get_setup()
    PlatformSetup.setup()
