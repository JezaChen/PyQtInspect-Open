"""Qt monkey-patching support."""


def patch_qt(qt_support_mode, is_attach=False):
    """Load and apply the Qt monkey patches on demand."""
    from .patcher import patch_qt as _patch_qt

    return _patch_qt(qt_support_mode, is_attach)

__all__ = ('patch_qt',)
