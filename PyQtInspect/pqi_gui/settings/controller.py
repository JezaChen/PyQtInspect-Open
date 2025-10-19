# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/9/7 16:11
# Description: 
# ==============================================
import typing

from PyQt5 import QtCore

from PyQtInspect.pqi_gui.settings.enums import SupportedIDE

T = typing.TypeVar("T")


class SettingField:
    def __init__(self, key: str, type_: typing.Type[T], default: T):
        self.key = key  # type: str
        self.type_ = type_  # type: typing.Type[T]
        self.default = default  # type: T

    def __get__(self, instance: 'SettingsController', owner) -> T:
        if instance is None:
            return self  # type: ignore
        return instance._getValue(self.key, self.type_, self.default)

    def __set__(self, instance: 'SettingsController', value: T):
        instance._setValue(self.key, value)

    def __delete__(self, instance: 'SettingsController'):
        instance._removeValue(self.key)


class SettingsController:
    _filePath = "settings.ini"

    class SettingsKeys:
        PyCharmPath = "PyCharmPath"
        AlwaysOnTop = "AlwaysOnTop"
        PressF8ToFinishSelecting = "PressF8ToFinishSelecting"
        MockRightClickAsLeftClick = "MockRightClickAsLeftClick"

        class IDE:
            Type = "IDE/Type"
            Path = "IDE/Path"
            Parameters = "IDE/Parameters"

    __slots__ = ('_setting',)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._setting = QtCore.QSettings(self._filePath, QtCore.QSettings.IniFormat)
        self._setting.setIniCodec("UTF-8")

    def _getValue(self, key: str, type_: typing.Type[T], default: T):
        return self._setting.value(key, default, type_)

    def _setValue(self, key: str, value):
        self._setting.setValue(key, value)
        self._setting.sync()

    def _removeValue(self, key: str):
        self._setting.remove(key)
        self._setting.sync()

    pyCharmPath = SettingField(SettingsKeys.PyCharmPath, str, "")
    alwaysOnTop = SettingField(SettingsKeys.AlwaysOnTop, bool, False)
    pressF8ToFinishSelecting = SettingField(SettingsKeys.PressF8ToFinishSelecting, bool, True)
    mockRightClickAsLeftClick = SettingField(SettingsKeys.MockRightClickAsLeftClick, bool, True)

    ideType = SettingField(SettingsKeys.IDE.Type, str, SupportedIDE.NoneType.value)
    idePath = SettingField(SettingsKeys.IDE.Path, str, "")
    ideParameters = SettingField(SettingsKeys.IDE.Parameters, str, "")

