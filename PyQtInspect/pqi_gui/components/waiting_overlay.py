from PyQt5 import QtWidgets, QtCore


class WaitingOverlay(QtWidgets.QWidget):
    def __init__(self, parent, message: str):
        assert parent is not None, "Parent widget must be provided."
        super().__init__(parent)
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._label = QtWidgets.QLabel(message, self)
        self._label.setAlignment(QtCore.Qt.AlignCenter)
        self._layout.addWidget(self._label)

        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(self.parent().rect())
        return super().eventFilter(obj, event)
