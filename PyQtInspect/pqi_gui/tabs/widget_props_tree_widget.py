import typing
from PyQt5 import QtWidgets, QtCore, QtGui

from PyQtInspect._pqi_bundle.pqi_comm_constants import WidgetPropsKeys
from PyQtInspect.pqi_gui.components.waiting_overlay import WaitingOverlay


class WidgetPropsTreeWidget(QtWidgets.QTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Disable editing

        self._model = QtGui.QStandardItemModel(self)
        self.setModel(self._model)
        self.setToolTipDuration(1_000)

    def notifyWidgetPropsInfo(self, propsInfo: typing.Sequence[typing.Mapping]):
        self._model.clear()
        self._model.setHorizontalHeaderLabels(['Property', 'Value'])
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        for clsInfo in propsInfo:
            clsName = clsInfo.get(WidgetPropsKeys.CLASSNAME_KEY, '')
            if not clsName:
                continue
            rootItem = QtGui.QStandardItem(clsName)
            self._model.appendRow([rootItem])

            props = clsInfo.get(WidgetPropsKeys.PROPS_KEY, {})
            self._addSubItems(rootItem, props)

            # Expand the root item to the first level
            self.expandRecursively(rootItem.index(), 1)

    def _addSubItems(self, parentItem: QtGui.QStandardItem, props: typing.Mapping):
        """ Recursively add sub items to the tree view. """
        for name, value in props.items():
            propNameItem = QtGui.QStandardItem(name)
            propValue = ''
            if isinstance(value, dict):
                propValue = value.get(WidgetPropsKeys.VALUE_KEY, '')
                # Recursively add sub items for nested dictionaries (properties)
                self._addSubItems(propNameItem, value.get(WidgetPropsKeys.PROPS_KEY, {}))
            else:
                propValue = str(value)

            # Replace newlines with spaces for better display
            # For stylesheet text, it may contain multiple lines,
            #   which makes the item height too large.
            propValueToDisplay = propValue.replace('\r\n', ' ').replace('\n', ' ').strip()
            propValueItem = QtGui.QStandardItem(propValueToDisplay)
            # Add tooltip
            propValueItem.setToolTip(str(propValue))
            parentItem.appendRow([propNameItem, propValueItem])

    def clear(self):
        self._model.clear()


class WidgetPropsTreeContainer(QtWidgets.QWidget):
    tab_name = "Properties"  # todo base class?

    def __init__(self, parent):
        super().__init__(parent)
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._mainLayout)
        self._treeWidget = WidgetPropsTreeWidget(self)
        self._mainLayout.addWidget(self._treeWidget)

        self._waitingOverlay = WaitingOverlay(self, "Waiting for inspect to finish...")
        self._waitingOverlay.setGeometry(self.rect())
        self._waitingOverlay.setVisible(False)

    def notifyWidgetPropsInfo(self, propsInfo: typing.Sequence[typing.Mapping]):
        # It also means that the inspect is finished.
        self._treeWidget.notifyWidgetPropsInfo(propsInfo)
        self._waitingOverlay.setVisible(False)

    def notifyInspectBegin(self):
        self._waitingOverlay.setVisible(True)
        self._treeWidget.clear()

