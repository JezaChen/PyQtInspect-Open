import typing
from PyQtInspect._pqi_bundle import pqi_log

from PyQtInspect._pqi_bundle.pqi_comm_constants import WidgetPropsKeys
from PyQtInspect._pqi_bundle.pqi_qt_tools import (
    find_method_by_name_and_call, find_method_by_name_and_safe_call
)
from PyQtInspect._pqi_bundle.pqi_qt_widget_props_fetcher._types_repr import get_representation

__all__ = [
    'WidgetPropertiesGetter',
]


def _generate_prop_fetcher_by_calling_method(method_name: str) -> typing.Callable[[object], typing.Any]:
    """
    Generate a property fetcher function that calls a method by its name.
    :param method_name: The name of the method to call.
    :return: A function that takes an object and returns the result of calling the method on it.
    """
    return lambda o: find_method_by_name_and_call(o, method_name)


class WidgetPropertiesGetter:
    def __init__(self):
        self._fetchers = {
            'QObject': {
                'objectName': _generate_prop_fetcher_by_calling_method('objectName'),
            },
            'QWidget': {
                'enabled': _generate_prop_fetcher_by_calling_method('isEnabled'),
                'geometry': _generate_prop_fetcher_by_calling_method('geometry'),
                'sizePolicy': _generate_prop_fetcher_by_calling_method('sizePolicy'),
                'minimumSize': _generate_prop_fetcher_by_calling_method('minimumSize'),
                'maximumSize': _generate_prop_fetcher_by_calling_method('maximumSize'),
                'sizeIncrement': _generate_prop_fetcher_by_calling_method('sizeIncrement'),
                'baseSize': _generate_prop_fetcher_by_calling_method('baseSize'),
                'font': _generate_prop_fetcher_by_calling_method('font'),
                # todo cursor...
                'mouseTracking': _generate_prop_fetcher_by_calling_method('hasMouseTracking'),
                # This property was introduced in Qt 5.9.
                'tabletTracking': _generate_prop_fetcher_by_calling_method('hasTabletTracking'),
                'focusPolicy': _generate_prop_fetcher_by_calling_method('focusPolicy'),
                'contextMenuPolicy': _generate_prop_fetcher_by_calling_method('contextMenuPolicy'),
                'acceptDrops': _generate_prop_fetcher_by_calling_method('acceptDrops'),
                'toolTip': _generate_prop_fetcher_by_calling_method('toolTip'),
                'toolTipDuration': _generate_prop_fetcher_by_calling_method('toolTipDuration'),
                'statusTip': _generate_prop_fetcher_by_calling_method('statusTip'),
                'whatsThis': _generate_prop_fetcher_by_calling_method('whatsThis'),
                'accessibleName': _generate_prop_fetcher_by_calling_method('accessibleName'),
                'accessibleDescription': _generate_prop_fetcher_by_calling_method('accessibleDescription'),
                'layoutDirection': _generate_prop_fetcher_by_calling_method('layoutDirection'),
                'autoFillBackground': _generate_prop_fetcher_by_calling_method('autoFillBackground'),
                'styleSheet': _generate_prop_fetcher_by_calling_method('styleSheet'),
                # todo locale...
                'inputMethodHints': _generate_prop_fetcher_by_calling_method('inputMethodHints'),
            },
            'QFrame': {
                'frameShape': _generate_prop_fetcher_by_calling_method('frameShape'),
                'frameShadow': _generate_prop_fetcher_by_calling_method('frameShadow'),
                'lineWidth': _generate_prop_fetcher_by_calling_method('lineWidth'),
                'midLineWidth': _generate_prop_fetcher_by_calling_method('midLineWidth'),
            },
            'QAbstractButton': {
                'text': _generate_prop_fetcher_by_calling_method('text'),
                # todo icon
                'iconSize': _generate_prop_fetcher_by_calling_method('iconSize'),
                'shortcut': _generate_prop_fetcher_by_calling_method('shortcut'),
                'checkable': _generate_prop_fetcher_by_calling_method('isCheckable'),
                'checked': _generate_prop_fetcher_by_calling_method('isChecked'),
                'autoRepeat': _generate_prop_fetcher_by_calling_method('autoRepeat'),
                'autoExclusive': _generate_prop_fetcher_by_calling_method('autoExclusive'),
                'autoRepeatDelay': _generate_prop_fetcher_by_calling_method('autoRepeatDelay'),
                'autoRepeatInterval': _generate_prop_fetcher_by_calling_method('autoRepeatInterval'),
            },
            'QPushButton': {
                'default': _generate_prop_fetcher_by_calling_method('isDefault'),
                'flat': _generate_prop_fetcher_by_calling_method('isFlat'),
                'autoDefault': _generate_prop_fetcher_by_calling_method('autoDefault'),
            },
            'QToolButton': {
                'popupMode': _generate_prop_fetcher_by_calling_method('popupMode'),
                'toolButtonStyle': _generate_prop_fetcher_by_calling_method('toolButtonStyle'),
                'autoRaise': _generate_prop_fetcher_by_calling_method('autoRaise'),
                'arrowType': _generate_prop_fetcher_by_calling_method('arrowType'),
            },
            'QCheckBox': {
                'tristate': _generate_prop_fetcher_by_calling_method('isTristate'),
            },
            'QCommandLinkButton': {
                'description': _generate_prop_fetcher_by_calling_method('description'),
            },
            'QAbstractScrollArea': {
                'horizontalScrollBarPolicy': _generate_prop_fetcher_by_calling_method('horizontalScrollBarPolicy'),
                'verticalScrollBarPolicy': _generate_prop_fetcher_by_calling_method('verticalScrollBarPolicy'),
                'sizeAdjustPolicy': _generate_prop_fetcher_by_calling_method('sizeAdjustPolicy'),
            },
            'QAbstractItemView': {
                'autoScroll': _generate_prop_fetcher_by_calling_method('hasAutoScroll'),
                'autoScrollMargin': _generate_prop_fetcher_by_calling_method('autoScrollMargin'),
                'editTriggers': _generate_prop_fetcher_by_calling_method('editTriggers'),
                'tabKeyNavigation': _generate_prop_fetcher_by_calling_method('tabKeyNavigation'),
                'showDropIndicator': _generate_prop_fetcher_by_calling_method('showDropIndicator'),
                'dragEnabled': _generate_prop_fetcher_by_calling_method('dragEnabled'),
                'dragDropOverwriteMode': _generate_prop_fetcher_by_calling_method('dragDropOverwriteMode'),
                'dragDropMode': _generate_prop_fetcher_by_calling_method('dragDropMode'),
                'defaultDropAction': _generate_prop_fetcher_by_calling_method('defaultDropAction'),
                'alternatingRowColors': _generate_prop_fetcher_by_calling_method('alternatingRowColors'),
                'selectionMode': _generate_prop_fetcher_by_calling_method('selectionMode'),
                'selectionBehavior': _generate_prop_fetcher_by_calling_method('selectionBehavior'),
                'iconSize': _generate_prop_fetcher_by_calling_method('iconSize'),
                'textElideMode': _generate_prop_fetcher_by_calling_method('textElideMode'),
                'verticalScrollMode': _generate_prop_fetcher_by_calling_method('verticalScrollMode'),
                'horizontalScrollMode': _generate_prop_fetcher_by_calling_method('horizontalScrollMode'),
            },
            'QListView': {
                'movement': _generate_prop_fetcher_by_calling_method('movement'),
                'flow': _generate_prop_fetcher_by_calling_method('flow'),
                'isWrapping': _generate_prop_fetcher_by_calling_method('isWrapping'),
                'resizeMode': _generate_prop_fetcher_by_calling_method('resizeMode'),
                'layoutMode': _generate_prop_fetcher_by_calling_method('layoutMode'),
                'spacing': _generate_prop_fetcher_by_calling_method('spacing'),
                'gridSize': _generate_prop_fetcher_by_calling_method('gridSize'),
                'viewMode': _generate_prop_fetcher_by_calling_method('viewMode'),
                'modelColumn': _generate_prop_fetcher_by_calling_method('modelColumn'),
                'uniformItemSizes': _generate_prop_fetcher_by_calling_method('uniformItemSizes'),
                'batchSize': _generate_prop_fetcher_by_calling_method('batchSize'),
                'wordWrap': _generate_prop_fetcher_by_calling_method('wordWrap'),
                'selectionRectVisible': _generate_prop_fetcher_by_calling_method('isSelectionRectVisible'),
                'itemAlignment': _generate_prop_fetcher_by_calling_method('itemAlignment'),
            },
            'QTreeView': {
                'autoExpandDelay': _generate_prop_fetcher_by_calling_method('autoExpandDelay'),
                'indentation': _generate_prop_fetcher_by_calling_method('indentation'),
                'rootIsDecorated': _generate_prop_fetcher_by_calling_method('rootIsDecorated'),
                'uniformRowHeights': _generate_prop_fetcher_by_calling_method('uniformRowHeights'),
                'itemsExpandable': _generate_prop_fetcher_by_calling_method('itemsExpandable'),
                'sortingEnabled': _generate_prop_fetcher_by_calling_method('isSortingEnabled'),
                'animated': _generate_prop_fetcher_by_calling_method('isAnimated'),
                'allColumnsShowFocus': _generate_prop_fetcher_by_calling_method('allColumnsShowFocus'),
                'wordWrap': _generate_prop_fetcher_by_calling_method('wordWrap'),
                'headerHidden': _generate_prop_fetcher_by_calling_method('isHeaderHidden'),
                'expandsOnDoubleClick': _generate_prop_fetcher_by_calling_method('expandsOnDoubleClick'),
            },
            'QTableView': {
                'showGrid': _generate_prop_fetcher_by_calling_method('showGrid'),
                'gridStyle': _generate_prop_fetcher_by_calling_method('gridStyle'),
                'sortingEnabled': _generate_prop_fetcher_by_calling_method('isSortingEnabled'),
                'wordWrap': _generate_prop_fetcher_by_calling_method('wordWrap'),
                'cornerButtonEnabled': _generate_prop_fetcher_by_calling_method('isCornerButtonEnabled'),
            },
            'QColumnView': {
                'resizeGripsVisible': _generate_prop_fetcher_by_calling_method('resizeGripsVisible'),
            },
            'QUndoView': {
                'emptyLabel': _generate_prop_fetcher_by_calling_method('emptyLabel'),
                # clearIcon
            },
            'QListWidget': {
                'currentRow': _generate_prop_fetcher_by_calling_method('currentRow'),
                'sortingEnabled': _generate_prop_fetcher_by_calling_method('isSortingEnabled'),
            },
            'QTreeWidget': {
                'columnCount': _generate_prop_fetcher_by_calling_method('columnCount'),
            },
            'QTableWidget': {
                'rowCount': _generate_prop_fetcher_by_calling_method('rowCount'),
                'columnCount': _generate_prop_fetcher_by_calling_method('columnCount'),
            },
            'QGroupBox': {
                'title': _generate_prop_fetcher_by_calling_method('title'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'flat': _generate_prop_fetcher_by_calling_method('isFlat'),
                'checkable': _generate_prop_fetcher_by_calling_method('isCheckable'),
                'checked': _generate_prop_fetcher_by_calling_method('isChecked'),
            },
            'QScrollArea': {
                'widgetResizable': _generate_prop_fetcher_by_calling_method('widgetResizable'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
            },
            'QToolBox': {
                'currentIndex': _generate_prop_fetcher_by_calling_method('currentIndex'),
                # o.itemText(o.currentIndex())
                'currentItemText': lambda o: find_method_by_name_and_call(o, 'itemText', find_method_by_name_and_call(o,
                                                                                                                      'currentIndex')),
                # w = o.currentWidget(); if w: w.objectName()
                'currentItemName': lambda o: find_method_by_name_and_safe_call(
                    find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
                # 'currentItemIcon'
                'currentItemToolTip': lambda o: find_method_by_name_and_call(o, 'itemToolTip',
                                                                             find_method_by_name_and_call(o,
                                                                                                          'currentIndex')),
                # 'tabSpacing'
            },
            'QTabWidget': {
                'tabPosition': _generate_prop_fetcher_by_calling_method('tabPosition'),
                'tabShape': _generate_prop_fetcher_by_calling_method('tabShape'),
                'currentIndex': _generate_prop_fetcher_by_calling_method('currentIndex'),
                'elideMode': _generate_prop_fetcher_by_calling_method('elideMode'),
                'usesScrollButtons': _generate_prop_fetcher_by_calling_method('usesScrollButtons'),
                'documentMode': _generate_prop_fetcher_by_calling_method('documentMode'),
                'tabsClosable': _generate_prop_fetcher_by_calling_method('tabsClosable'),
                'movable': _generate_prop_fetcher_by_calling_method('isMovable'),
                'tabBarAutoHide': _generate_prop_fetcher_by_calling_method('tabBarAutoHide'),
                'currentTabText': lambda o: find_method_by_name_and_call(o, 'tabText', find_method_by_name_and_call(o,
                                                                                                                    'currentIndex')),
                'currentTabName': lambda o: find_method_by_name_and_safe_call(
                    find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
                # ’currentTabIcon'
                'currentTabToolTip': lambda o: find_method_by_name_and_call(o, 'tabToolTip',
                                                                            find_method_by_name_and_call(o,
                                                                                                         'currentIndex')),
                'currentTabWhatThis': lambda o: find_method_by_name_and_call(o, 'tabWhatsThis',
                                                                             find_method_by_name_and_call(o,
                                                                                                          'currentIndex')),
            },
            'QStackedWidget': {
                'currentIndex': _generate_prop_fetcher_by_calling_method('currentIndex'),
                'currentPageName': lambda o: find_method_by_name_and_safe_call(
                    find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
            },
            'QMdiArea': {
                'background': _generate_prop_fetcher_by_calling_method('background'),
                'activationOrder': _generate_prop_fetcher_by_calling_method('activationOrder'),
                'viewMode': _generate_prop_fetcher_by_calling_method('viewMode'),
                'documentMode': _generate_prop_fetcher_by_calling_method('documentMode'),
                'tabsClosable': _generate_prop_fetcher_by_calling_method('tabsClosable'),
                'tabsMovable': _generate_prop_fetcher_by_calling_method('tabsMovable'),
                'tabShape': _generate_prop_fetcher_by_calling_method('tabShape'),
                'tabPosition': _generate_prop_fetcher_by_calling_method('tabPosition'),
                'activateSubWindowName': lambda o: find_method_by_name_and_safe_call(
                    find_method_by_name_and_call(o, 'activeSubWindow'), 'objectName', ''),
                'activateSubWindowTitle': lambda o: find_method_by_name_and_safe_call(
                    find_method_by_name_and_call(o, 'activeSubWindow'), 'windowTitle ', ''),
            },
            'QDockWidget': {
                'floating': _generate_prop_fetcher_by_calling_method('isFloating'),
                'features': _generate_prop_fetcher_by_calling_method('features'),
                'allowedAreas': _generate_prop_fetcher_by_calling_method('allowedAreas'),
                'windowTitle': _generate_prop_fetcher_by_calling_method('windowTitle'),
                # 'dockWidgetArea'
                # 'docked'
            },
            'QAxWidget': {
                # 'control', 'orientation'
            },
            'QComboBox': {
                'editable': _generate_prop_fetcher_by_calling_method('isEditable'),
                'currentText': _generate_prop_fetcher_by_calling_method('currentText'),
                'currentIndex': _generate_prop_fetcher_by_calling_method('currentIndex'),
                'maxVisibleItems': _generate_prop_fetcher_by_calling_method('maxVisibleItems'),
                'maxCount': _generate_prop_fetcher_by_calling_method('maxCount'),
                'insertPolicy': _generate_prop_fetcher_by_calling_method('insertPolicy'),
                'sizeAdjustPolicy': _generate_prop_fetcher_by_calling_method('sizeAdjustPolicy'),
                'minimumContentsLength': _generate_prop_fetcher_by_calling_method('minimumContentsLength'),
                'iconSize': _generate_prop_fetcher_by_calling_method('iconSize'),
                'placeholderText': _generate_prop_fetcher_by_calling_method('placeholderText'),
                'duplicatesEnabled': _generate_prop_fetcher_by_calling_method('duplicatesEnabled'),
                'frame': _generate_prop_fetcher_by_calling_method('hasFrame'),
                'modelColumn': _generate_prop_fetcher_by_calling_method('modelColumn'),
            },
            'QFontComboBox': {
                'writingSystem': _generate_prop_fetcher_by_calling_method('writingSystem'),
                'fontFilters': _generate_prop_fetcher_by_calling_method('fontFilters'),
                'currentFont': _generate_prop_fetcher_by_calling_method('currentFont'),
            },
            'QLineEdit': {
                'inputMask': _generate_prop_fetcher_by_calling_method('inputMask'),
                'text': _generate_prop_fetcher_by_calling_method('text'),
                'maxLength': _generate_prop_fetcher_by_calling_method('maxLength'),
                'frame': _generate_prop_fetcher_by_calling_method('hasFrame'),
                'echoMode': _generate_prop_fetcher_by_calling_method('echoMode'),
                'cursorPosition': _generate_prop_fetcher_by_calling_method('cursorPosition'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'dragEnabled': _generate_prop_fetcher_by_calling_method('dragEnabled'),
                'readOnly': _generate_prop_fetcher_by_calling_method('isReadOnly'),
                'placeholderText': _generate_prop_fetcher_by_calling_method('placeholderText'),
                'cursorMoveStyle': _generate_prop_fetcher_by_calling_method('cursorMoveStyle'),
                'clearButtonEnabled': _generate_prop_fetcher_by_calling_method('isClearButtonEnabled'),
            },
            'QTextEdit': {
                'autoFormatting': _generate_prop_fetcher_by_calling_method('autoFormatting'),
                'tabChangesFocus': _generate_prop_fetcher_by_calling_method('tabChangesFocus'),
                'documentTitle': _generate_prop_fetcher_by_calling_method('documentTitle'),
                'undoRedoEnabled': _generate_prop_fetcher_by_calling_method('isUndoRedoEnabled'),
                'lineWrapMode': _generate_prop_fetcher_by_calling_method('lineWrapMode'),
                'lineWrapColumnOrWidth': _generate_prop_fetcher_by_calling_method('lineWrapColumnOrWidth'),
                'readOnly': _generate_prop_fetcher_by_calling_method('isReadOnly'),
                'markdown': _generate_prop_fetcher_by_calling_method('toMarkdown'),
                'html': _generate_prop_fetcher_by_calling_method('toHtml'),
                'overwriteMode': _generate_prop_fetcher_by_calling_method('overwriteMode'),
                'tabStopDistance': _generate_prop_fetcher_by_calling_method('tabStopDistance'),
                'acceptRichText': _generate_prop_fetcher_by_calling_method('acceptRichText'),
                'cursorWidth': _generate_prop_fetcher_by_calling_method('cursorWidth'),
                'textInteractionFlags': _generate_prop_fetcher_by_calling_method('textInteractionFlags'),
                'placeholderText': _generate_prop_fetcher_by_calling_method('placeholderText'),
            },
            'QPlainTextEdit': {
                'tabChangesFocus': _generate_prop_fetcher_by_calling_method('tabChangesFocus'),
                'documentTitle': _generate_prop_fetcher_by_calling_method('documentTitle'),
                'undoRedoEnabled': _generate_prop_fetcher_by_calling_method('isUndoRedoEnabled'),
                'lineWrapMode': _generate_prop_fetcher_by_calling_method('lineWrapMode'),
                'readOnly': _generate_prop_fetcher_by_calling_method('isReadOnly'),
                'plainText': _generate_prop_fetcher_by_calling_method('toPlainText'),
                'overwriteMode': _generate_prop_fetcher_by_calling_method('overwriteMode'),
                'tabStopDistance': _generate_prop_fetcher_by_calling_method('tabStopDistance'),
                'cursorWidth': _generate_prop_fetcher_by_calling_method('cursorWidth'),
                'textInteractionFlags': _generate_prop_fetcher_by_calling_method('textInteractionFlags'),
                'maximumBlockCount': _generate_prop_fetcher_by_calling_method('maximumBlockCount'),
                'backgroundVisible': _generate_prop_fetcher_by_calling_method('backgroundVisible'),
                'centerOnScroll': _generate_prop_fetcher_by_calling_method('centerOnScroll'),
                'placeholderText': _generate_prop_fetcher_by_calling_method('placeholderText'),
            },
            'QAbstractSpinBox': {
                'wrapping': _generate_prop_fetcher_by_calling_method('wrapping'),
                'frame': _generate_prop_fetcher_by_calling_method('hasFrame'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'readOnly': _generate_prop_fetcher_by_calling_method('isReadOnly'),
                'buttonSymbols': _generate_prop_fetcher_by_calling_method('buttonSymbols'),
                'specialValueText': _generate_prop_fetcher_by_calling_method('specialValueText'),
                'accelerated': _generate_prop_fetcher_by_calling_method('isAccelerated'),
                'correctionMode': _generate_prop_fetcher_by_calling_method('correctionMode'),
                'keyboardTracking': _generate_prop_fetcher_by_calling_method('keyboardTracking'),
                'showGroupSeparator': _generate_prop_fetcher_by_calling_method('isGroupSeparatorShown'),
            },
            'QSpinBox': {
                'suffix': _generate_prop_fetcher_by_calling_method('suffix'),
                'prefix': _generate_prop_fetcher_by_calling_method('prefix'),
                'minimum': _generate_prop_fetcher_by_calling_method('minimum'),
                'maximum': _generate_prop_fetcher_by_calling_method('maximum'),
                'singleStep': _generate_prop_fetcher_by_calling_method('singleStep'),
                'stepType': _generate_prop_fetcher_by_calling_method('stepType'),
                'value': _generate_prop_fetcher_by_calling_method('value'),
                'displayIntegerBase': _generate_prop_fetcher_by_calling_method('displayIntegerBase'),
            },
            'QDoubleSpinBox': {
                'prefix': _generate_prop_fetcher_by_calling_method('prefix'),
                'suffix': _generate_prop_fetcher_by_calling_method('suffix'),
                'decimals': _generate_prop_fetcher_by_calling_method('decimals'),
                'minimum': _generate_prop_fetcher_by_calling_method('minimum'),
                'maximum': _generate_prop_fetcher_by_calling_method('maximum'),
                'singleStep': _generate_prop_fetcher_by_calling_method('singleStep'),
                'stepType': _generate_prop_fetcher_by_calling_method('stepType'),
                'value': _generate_prop_fetcher_by_calling_method('value'),
            },
            'QDateTimeEdit': {
                'dateTime': _generate_prop_fetcher_by_calling_method('dateTime'),
                'date': _generate_prop_fetcher_by_calling_method('date'),
                'time': _generate_prop_fetcher_by_calling_method('time'),
                'maximumDateTime': _generate_prop_fetcher_by_calling_method('maximumDateTime'),
                'minimumDateTime': _generate_prop_fetcher_by_calling_method('minimumDateTime'),
                'maximumDate': _generate_prop_fetcher_by_calling_method('maximumDate'),
                'minimumDate': _generate_prop_fetcher_by_calling_method('minimumDate'),
                'maximumTime': _generate_prop_fetcher_by_calling_method('maximumTime'),
                'minimumTime': _generate_prop_fetcher_by_calling_method('minimumTime'),
                'currentSection': _generate_prop_fetcher_by_calling_method('currentSection'),
                'displayFormat': _generate_prop_fetcher_by_calling_method('displayFormat'),
                'calendarPopup': _generate_prop_fetcher_by_calling_method('calendarPopup'),
                'currentSectionIndex': _generate_prop_fetcher_by_calling_method('currentSectionIndex'),
                'timeSpec': _generate_prop_fetcher_by_calling_method('timeSpec'),
            },
            'QTimeEdit': {
                'time': _generate_prop_fetcher_by_calling_method('time'),
            },
            'QDateEdit': {
                'date': _generate_prop_fetcher_by_calling_method('date'),
            },
            'QAbstractSlider': {
                'minimum': _generate_prop_fetcher_by_calling_method('minimum'),
                'maximum': _generate_prop_fetcher_by_calling_method('maximum'),
                'singleStep': _generate_prop_fetcher_by_calling_method('singleStep'),
                'pageStep': _generate_prop_fetcher_by_calling_method('pageStep'),
                'value': _generate_prop_fetcher_by_calling_method('value'),
                'sliderPosition': _generate_prop_fetcher_by_calling_method('sliderPosition'),
                'tracking': _generate_prop_fetcher_by_calling_method('hasTracking'),
                'orientation': _generate_prop_fetcher_by_calling_method('orientation'),
                'invertedAppearance': _generate_prop_fetcher_by_calling_method('invertedAppearance'),
                'invertedControls': _generate_prop_fetcher_by_calling_method('invertedControls'),
            },
            'QDial': {
                'wrapping': _generate_prop_fetcher_by_calling_method('wrapping'),
                'notchTarget': _generate_prop_fetcher_by_calling_method('notchTarget'),
                'notchesVisible': _generate_prop_fetcher_by_calling_method('notchesVisible'),
            },
            'QSlider': {
                'tickPosition': _generate_prop_fetcher_by_calling_method('tickPosition'),
                'tickInterval': _generate_prop_fetcher_by_calling_method('tickInterval'),
            },
            'QKeySequenceEdit': {
                'keySequence': _generate_prop_fetcher_by_calling_method('keySequence'),
                'clearButtonEnabled': _generate_prop_fetcher_by_calling_method('isClearButtonEnabled'),  # since 6.4
                'maximumSequenceLength': _generate_prop_fetcher_by_calling_method('maximumSequenceLength'),  # since 6.5
            },
            'QLabel': {
                'text': _generate_prop_fetcher_by_calling_method('text'),
                'textFormat': _generate_prop_fetcher_by_calling_method('textFormat'),
                'scaledContents': _generate_prop_fetcher_by_calling_method('hasScaledContents'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'wordWrap': _generate_prop_fetcher_by_calling_method('wordWrap'),
                'margin': _generate_prop_fetcher_by_calling_method('margin'),
                'indent': _generate_prop_fetcher_by_calling_method('indent'),
                'openExternalLinks': _generate_prop_fetcher_by_calling_method('openExternalLinks'),
                'textInteractionFlags': _generate_prop_fetcher_by_calling_method('textInteractionFlags'),
                # 'buddy'
            },
            'QTextBrowser': {
                'source': _generate_prop_fetcher_by_calling_method('source'),
                'searchPaths': _generate_prop_fetcher_by_calling_method('searchPaths'),
                'openExternalLinks': _generate_prop_fetcher_by_calling_method('openExternalLinks'),
                'openLinks': _generate_prop_fetcher_by_calling_method('openLinks'),
            },
            'QGraphicsView': {
                'backgroundBrush': _generate_prop_fetcher_by_calling_method('backgroundBrush'),
                'foregroundBrush': _generate_prop_fetcher_by_calling_method('foregroundBrush'),
                'interactive': _generate_prop_fetcher_by_calling_method('isInteractive'),
                'sceneRect': _generate_prop_fetcher_by_calling_method('sceneRect'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'renderHints': _generate_prop_fetcher_by_calling_method('renderHints'),
                'dragMode': _generate_prop_fetcher_by_calling_method('dragMode'),
                'cacheMode': _generate_prop_fetcher_by_calling_method('cacheMode'),
                'transformationAnchor': _generate_prop_fetcher_by_calling_method('transformationAnchor'),
                'resizeAnchor': _generate_prop_fetcher_by_calling_method('resizeAnchor'),
                'viewportUpdateMode': _generate_prop_fetcher_by_calling_method('viewportUpdateMode'),
                'rubberBandSelectionMode': _generate_prop_fetcher_by_calling_method('rubberBandSelectionMode'),
                'optimizationFlags': _generate_prop_fetcher_by_calling_method('optimizationFlags'),
            },
            'QCalendarWidget': {
                'selectedDate': _generate_prop_fetcher_by_calling_method('selectedDate'),
                'minimumDate': _generate_prop_fetcher_by_calling_method('minimumDate'),
                'maximumDate': _generate_prop_fetcher_by_calling_method('maximumDate'),
                'firstDayOfWeek': _generate_prop_fetcher_by_calling_method('firstDayOfWeek'),
                'gridVisible': _generate_prop_fetcher_by_calling_method('isGridVisible'),
                'selectionMode': _generate_prop_fetcher_by_calling_method('selectionMode'),
                'horizontalHeaderFormat': _generate_prop_fetcher_by_calling_method('horizontalHeaderFormat'),
                'verticalHeaderFormat': _generate_prop_fetcher_by_calling_method('verticalHeaderFormat'),
                'navigationBarVisible': _generate_prop_fetcher_by_calling_method('isNavigationBarVisible'),
                'dateEditEnabled': _generate_prop_fetcher_by_calling_method('isDateEditEnabled'),
                'dateEditAcceptDelay': _generate_prop_fetcher_by_calling_method('dateEditAcceptDelay'),
            },
            'QLCDNumber': {
                'smallDecimalPoint': _generate_prop_fetcher_by_calling_method('smallDecimalPoint'),
                'digitCount': _generate_prop_fetcher_by_calling_method('digitCount'),
                'mode': _generate_prop_fetcher_by_calling_method('mode'),
                'segmentStyle': _generate_prop_fetcher_by_calling_method('segmentStyle'),
                'value': _generate_prop_fetcher_by_calling_method('value'),
                'intValue': _generate_prop_fetcher_by_calling_method('intValue'),
            },
            'QProgressBar': {
                'minimum': _generate_prop_fetcher_by_calling_method('minimum'),
                'maximum': _generate_prop_fetcher_by_calling_method('maximum'),
                'value': _generate_prop_fetcher_by_calling_method('value'),
                'alignment': _generate_prop_fetcher_by_calling_method('alignment'),
                'textVisible': _generate_prop_fetcher_by_calling_method('isTextVisible'),
                'orientation': _generate_prop_fetcher_by_calling_method('orientation'),
                'invertedAppearance': _generate_prop_fetcher_by_calling_method('invertedAppearance'),
                'textDirection': _generate_prop_fetcher_by_calling_method('textDirection'),
                'format': _generate_prop_fetcher_by_calling_method('format'),
            },
            'QQuickWidget': {
                # todo need to import QtQuickWidgets
                # 'resizeMode': _generate_prop_fetcher_by_calling_method('resizeMode'),
                'source': _generate_prop_fetcher_by_calling_method('source'),
            },
        }

    def get_object_properties(self, widget):
        """
        Get the properties info of a widget.
        :param widget:
        :return: a list of dictionaries, each dictionary contains the class name and its properties
          The order of the classes is from the most derived class to the base class. (e.g. QLabel -> QWidget -> QObject)
          Structure:
          [
              {
                  'cn': 'QWidget',  // cn: class name
                  'p': {  // p: properties
                      'objectName': 'myWidget',
                      'enabled': True,
                      'geometry': {  // the complex property which contains sub-properties
                          'v': '[(120, 240), 171 x 16]',  // v: value (string representation)
                          'p': {  // recursive properties...
                                'X': 120,
                                'Y': 240,
                                'Width': 171,
                                'Height': 16,
                          }
                      },
                  }
              },
              ...
          ]
        """
        res = []
        for cls in reversed(type(widget).__mro__):
            cls_name = cls.__name__
            if cls_name in self._fetchers:
                props = {}
                cls_info = {
                    WidgetPropsKeys.CLASSNAME_KEY: cls_name,
                    WidgetPropsKeys.PROPS_KEY: props,
                }

                for prop, fetcher in self._fetchers[cls_name].items():
                    try:
                        val = fetcher(widget)
                        props[prop] = get_representation(val)
                    except Exception as e:  # noqa
                        pqi_log.warning(f'Failed to fetch property {prop} of {cls_name}: {e}')
                res.append(cls_info)
        return res
