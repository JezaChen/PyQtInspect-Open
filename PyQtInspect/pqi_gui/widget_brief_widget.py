# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2025/7/30 19:49
# Description:
# ==============================================
from PyQt5 import QtWidgets, QtCore


class BriefLine(QtWidgets.QWidget):
    def __init__(self, parent, key: str, defaultValue: str = ""):
        super().__init__(parent)
        self.setFixedHeight(30)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(5)

        self._keyLabel = QtWidgets.QLabel(self)
        self._keyLabel.setText(key)
        self._keyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._keyLabel.setWordWrap(True)
        self._keyLabel.setMinimumWidth(90)
        self._keyLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._layout.addWidget(self._keyLabel)

        self._valueLineEdit = QtWidgets.QLineEdit(self)
        self._valueLineEdit.setObjectName("codeStyleLineEdit")
        self._valueLineEdit.setText(defaultValue)
        self._valueLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._valueLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._valueLineEdit.setReadOnly(True)
        self._valueLineEdit.textChanged.connect(self._updateToolTipForValueLineEdit)

        self._layout.addWidget(self._valueLineEdit)

    def setValue(self, value: str):
        self._valueLineEdit.setText(value)

    def _updateToolTipForValueLineEdit(self, text: str):
        # If the text is too long, set the tooltip to the full text.
        metrics = self._valueLineEdit.fontMetrics()
        if metrics.width(text) > self._valueLineEdit.width():
            self._valueLineEdit.setToolTip(text)
        else:
            self._valueLineEdit.setToolTip("")


class WidgetBriefWidget(QtWidgets.QWidget):
    sigOpenCodeWindow = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(5)

        self._classNameLine = BriefLine(self, "Class")
        self._mainLayout.addWidget(self._classNameLine)

        self._objectNameLine = BriefLine(self, "Object Name")
        self._mainLayout.addWidget(self._objectNameLine)

        self._sizeLine = BriefLine(self, "Size (W, H)")
        self._mainLayout.addWidget(self._sizeLine)

        self._posLine = BriefLine(self, "Position (X, Y)")
        self._mainLayout.addWidget(self._posLine)

        self._styleSheetLine = BriefLine(self, "Style Sheet")
        self._mainLayout.addWidget(self._styleSheetLine)

        self._executionButtonsLayout = QtWidgets.QHBoxLayout()
        self._executionButtonsLayout.setContentsMargins(4, 0, 4, 0)
        self._executionButtonsLayout.setSpacing(5)

        self._execCodeButton = QtWidgets.QPushButton(self)
        self._execCodeButton.setText("Run Snippet…")
        self._execCodeButton.setToolTip("Run the snippet in the selected control's context.")
        self._execCodeButton.setFixedHeight(30)
        self._execCodeButton.clicked.connect(self.sigOpenCodeWindow)

        self._executionButtonsLayout.addWidget(self._execCodeButton)

        self._mainLayout.addLayout(self._executionButtonsLayout)

        self._mainLayout.addStretch(1)

    def setInfo(self, info):
        self._classNameLine.setValue(info["class_name"])
        objName = info["object_name"]
        self._objectNameLine.setValue(objName)
        width, height = info["size"]
        self._sizeLine.setValue(f"{width}, {height}")
        posX, posY = info["pos"]
        self._posLine.setValue(f"{posX}, {posY}")
        self._styleSheetLine.setValue(info["stylesheet"])

    def clearInfo(self):
        self._classNameLine.setValue("")
        self._objectNameLine.setValue("")
        self._sizeLine.setValue("")
        self._posLine.setValue("")
        self._styleSheetLine.setValue("")
