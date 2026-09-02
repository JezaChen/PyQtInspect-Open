from typing import NamedTuple, Callable


class QObjectInspectAPIFunctions(NamedTuple):
    isdeleted: Callable[[object], bool]
    ispycreated: Callable[[object], bool]


class QObjectInspectAPI:
    _instance = None

    @classmethod
    def instance(cls):
        assert cls._instance is not None, \
            "QObjectInspectAPI instance is not initialized. Call QObjectInspectAPI.init_instance() first."
        return cls._instance

    @classmethod
    def init_instance(cls, *args, **kwargs):
        assert cls._instance is None, \
            "QObjectInspectAPI instance is already initialized. Call QObjectInspectAPI.instance() to get the existing instance."
        cls._instance = cls(*args, **kwargs)

    def __init__(self, functions: QObjectInspectAPIFunctions):
        self._functions = functions

    @property
    def isdeleted(self):
        return self._functions.isdeleted

    @property
    def ispycreated(self):
        return self._functions.ispycreated


class QtModuleAPI:
    _instance = None

    @classmethod
    def instance(cls):
        assert cls._instance is not None, \
            "QtModuleAPI instance is not initialized. Call QtModuleAPI.init_instance() first."
        return cls._instance

    @classmethod
    def init_instance(cls, *args, **kwargs):
        assert cls._instance is None, \
            "QtModuleAPI instance is already initialized. Call QtModuleAPI.instance() to get the existing instance."
        cls._instance = cls(*args, **kwargs)

    def __init__(self, qt_module):
        self._qt_module = qt_module

    @property
    def QtCore(self):
        return self._qt_module.QtCore

    @property
    def QtGui(self):
        return self._qt_module.QtGui

    @property
    def QtWidgets(self):
        return self._qt_module.QtWidgets
