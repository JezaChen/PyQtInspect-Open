# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/9/7 16:00
# Description: 
# ==============================================
import os
import typing

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQtInspect._pqi_bundle.pqi_contants import IS_WINDOWS, IS_MACOS
from PyQtInspect.pqi_gui._pqi_res import get_icon

from PyQtInspect.pqi_gui.settings import SettingsController
from PyQtInspect.pqi_gui.settings.enums import SupportedIDE
from PyQtInspect.pqi_gui.settings.ide_jumpers import find_default_ide_path


class IDESettingsGroupBox(QtWidgets.QGroupBox):
    """ IDE settings group box with IDE type selector, path input, and custom command input """

    def __init__(self, parent):
        super().__init__("IDE Settings", parent)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(10, 15, 10, 10)
        self._mainLayout.setSpacing(10)

        # IDE Type ComboBox
        self._ideTypeWidget = QtWidgets.QWidget(self)
        self._ideTypeLayout = QtWidgets.QHBoxLayout(self._ideTypeWidget)
        self._ideTypeLayout.setSpacing(10)

        self._ideTypeLabel = QtWidgets.QLabel("IDE Type:", self)
        self._ideTypeLabel.setFixedWidth(100)
        self._ideTypeLayout.addWidget(self._ideTypeLabel)

        self._ideTypeComboBox = QtWidgets.QComboBox(self)
        self._ideTypeComboBox.setFixedHeight(32)
        for ide_name, ide_type in SupportedIDE.get_supported_IDEs_for_settings():
            self._ideTypeComboBox.addItem(ide_name, ide_type)
        self._ideTypeComboBox.currentTextChanged.connect(self._onIDETypeChanged)
        self._ideTypeLayout.addWidget(self._ideTypeComboBox)

        self._mainLayout.addWidget(self._ideTypeWidget)

        # IDE Path Input
        self._idePathWidget = QtWidgets.QWidget(self)
        self._idePathLayout = QtWidgets.QHBoxLayout(self._idePathWidget)
        self._idePathLayout.setSpacing(10)

        self._idePathLabel = QtWidgets.QLabel("IDE Path:", self)
        self._idePathLabel.setFixedWidth(100)
        self._idePathLayout.addWidget(self._idePathLabel)

        self._idePathLineEdit = QtWidgets.QLineEdit(self)
        self._idePathLineEdit.setFixedHeight(32)
        self._idePathLayout.addWidget(self._idePathLineEdit)

        self._browseActionIcon = QtGui.QIcon(":/icons/open_file.svg")
        self._browseAction = QtWidgets.QAction(self._browseActionIcon, "Browse...", self)
        self._browseAction.setToolTip("Browse...")
        self._browseAction.triggered.connect(self._selectIDEPath)
        self._idePathLineEdit.addAction(self._browseAction, QtWidgets.QLineEdit.TrailingPosition)

        self._autoDetectActionIcon = QtGui.QIcon(":/icons/detect.svg")
        self._autoDetectAction = QtWidgets.QAction(self._autoDetectActionIcon, "Auto Detect", self)
        self._autoDetectAction.setToolTip("Auto Detect the IDE Path")
        self._autoDetectAction.triggered.connect(self._autoDetectIDEPath)
        self._idePathLineEdit.addAction(self._autoDetectAction, QtWidgets.QLineEdit.TrailingPosition)

        self._mainLayout.addWidget(self._idePathWidget)

        # Custom Command Input (only visible when IDE type is "Custom")
        self._customCommandParametersWidget = QtWidgets.QWidget(self)
        self._customCommandParametersLayout = QtWidgets.QHBoxLayout(self._customCommandParametersWidget)
        self._customCommandParametersLayout.setSpacing(10)

        self._customCommandParametersLabel = QtWidgets.QLabel("Parameters:", self)
        self._customCommandParametersLabel.setFixedWidth(100)
        self._customCommandParametersLayout.addWidget(self._customCommandParametersLabel)

        self._customCommandParametersLineEdit = QtWidgets.QLineEdit(self)
        self._customCommandParametersLineEdit.setFixedHeight(32)
        self._customCommandParametersLineEdit.setPlaceholderText("e.g., {file} --line {line}")
        self._customCommandParametersLayout.addWidget(self._customCommandParametersLineEdit)

        self._mainLayout.addWidget(self._customCommandParametersWidget)

    # region UI Update logic
    def _updateIDEPathControlsVisibility(self):
        """ Update visibility of IDE path controls based on selected IDE type """
        ideType = self.getIDEType()
        self._idePathWidget.setVisible(ideType != SupportedIDE.NoneType)
        self._autoDetectAction.setVisible(ideType not in (SupportedIDE.NoneType, SupportedIDE.Custom))

    def _updateCustomCommandParametersControlsVisibility(self):
        """ Update visibility of custom command input based on selected IDE type """
        ideType = self.getIDEType()
        self._customCommandParametersWidget.setVisible(ideType == SupportedIDE.Custom)

    # endregion

    def _onIDETypeChanged(self, _):
        """ Show/hide custom command input based on IDE type """
        self._idePathLineEdit.clear()
        self._customCommandParametersLineEdit.clear()
        self._updateIDEPathControlsVisibility()
        self._updateCustomCommandParametersControlsVisibility()

    def _selectIDEPath(self):
        """ Open file dialog to select IDE executable """
        currentPath = self._idePathLineEdit.text()
        if not currentPath:
            currentPath = ""

        if IS_WINDOWS:
            fileFilter = "Executable Files (*.exe, *.cmd);;All Files (*.*)"
        else:
            fileFilter = "All Files (*)"

        idePath = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select IDE Executable", currentPath, fileFilter
        )
        if idePath and idePath[0]:
            self._idePathLineEdit.setText(os.path.normpath(idePath[0]))

    def _autoDetectIDEPath(self):
        """ Automatically detect IDE path based on common installation locations """
        path = find_default_ide_path(self.getIDEType())
        if path:
            self._idePathLineEdit.setText(os.path.normpath(path))
        else:
            QtWidgets.QMessageBox.information(self, "Auto Detect", "No executable found for the selected IDE type.")

    def getIDEType(self) -> SupportedIDE:
        return self._ideTypeComboBox.currentData()

    def setIDEType(self, ideType: SupportedIDE):
        index = self._ideTypeComboBox.findData(ideType)
        if index >= 0:
            self._ideTypeComboBox.setCurrentIndex(index)
        self._updateIDEPathControlsVisibility()
        self._updateCustomCommandParametersControlsVisibility()

    def getIDEPath(self) -> str:
        return self._idePathLineEdit.text()

    def setIDEPath(self, path: str):
        self._idePathLineEdit.setText(path)

    def getCustomCommandParameters(self) -> str:
        return self._customCommandParametersLineEdit.text()

    def setCustomCommandParameters(self, command: str):
        self._customCommandParametersLineEdit.setText(command)

    def isValid(self) -> typing.Tuple[bool, str]:
        """ Validate IDE settings. Returns (is_valid, error_message) """
        ideType = self.getIDEType()
        idePath = self.getIDEPath()

        if ideType == SupportedIDE.NoneType:
            return True, ""

        if not idePath:
            return False, "IDE path cannot be empty"

        # Check if path exists (if provided)
        if idePath and not os.path.exists(idePath):
            return False, f"IDE path does not exist: {idePath}"

        # Check custom command for required placeholders
        if ideType == SupportedIDE.Custom:
            parameters = self.getCustomCommandParameters()
            if not parameters:
                return False, "Custom parameters are required for Custom IDE type"
            if "{file}" not in parameters:
                return False, 'Custom parameters must contain "{file}" placeholder'
            if "{line}" not in parameters:
                return False, 'Custom parameters must contain "{line}" placeholder'

        return True, ""


class SettingWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowIcon(get_icon())
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(600)

        self._mainLayout = QtWidgets.QVBoxLayout(self)
        top_margin = 10
        if IS_MACOS:
            top_margin = 30
        self._mainLayout.setContentsMargins(5, top_margin, 5, 0)
        self._mainLayout.setSpacing(5)
        self._mainLayout.addSpacing(4)

        # IDE Settings GroupBox
        self._ideSettingsGroup = IDESettingsGroupBox(self)
        self._mainLayout.addWidget(self._ideSettingsGroup)

        self._mainLayout.addStretch()

        self._buttonLayout = QtWidgets.QHBoxLayout()
        self._buttonLayout.setContentsMargins(0, 0, 0, 0)
        self._buttonLayout.setSpacing(5)

        self._saveButton = QtWidgets.QPushButton(self)
        self._saveButton.setFixedSize(100, 40)
        self._saveButton.setText("Save")
        self._saveButton.clicked.connect(self.saveSettings)
        self._buttonLayout.addWidget(self._saveButton)

        self._cancelButton = QtWidgets.QPushButton(self)
        self._cancelButton.setFixedSize(100, 40)
        self._cancelButton.setText("Cancel")
        self._cancelButton.clicked.connect(self.close)
        self._buttonLayout.addWidget(self._cancelButton)

        self._mainLayout.addLayout(self._buttonLayout)

        self._mainLayout.addSpacing(4)

        self.loadSettings()

    def loadSettings(self):
        settingsCtrl = SettingsController.instance()
        self._ideSettingsGroup.setIDEType(SupportedIDE(settingsCtrl.ideType))
        self._ideSettingsGroup.setIDEPath(settingsCtrl.idePath)
        self._ideSettingsGroup.setCustomCommandParameters(settingsCtrl.ideParameters)

    def saveSettings(self):
        # Validate IDE settings
        isValid, errorMessage = self._ideSettingsGroup.isValid()
        if not isValid:
            QtWidgets.QMessageBox.critical(self, "Error", errorMessage)
            return

        # Save IDE settings
        settingsCtrl = SettingsController.instance()
        settingsCtrl.ideType = self._ideSettingsGroup.getIDEType().value
        settingsCtrl.idePath = self._ideSettingsGroup.getIDEPath()
        settingsCtrl.ideParameters = self._ideSettingsGroup.getCustomCommandParameters()

        self.close()

    def showEvent(self, ev):
        super().showEvent(ev)
        self.loadSettings()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = SettingWindow()
    window.show()
    sys.exit(app.exec())
