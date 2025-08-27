"""
Representers of enum types
"""
import abc
import typing
from collections import defaultdict

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_qt_widget_props_fetcher._types_repr._base import TypeRepr

__all__ = [
    # Just expose the CustomEnumRepr class, its subclasses can be registered by internal logic
    'CustomEnumRepr',
    # special expose for QFontRepr
    'WeightEnumRepr'
]


class CustomEnumRepr(TypeRepr):
    """
    A base class for custom enum representations.
    Subclasses should implement the `enum_type` and `enum_names` properties to provide the enum type and names.
    The `_repr_impl` method should return the string representation of the enum value.
    If the enum value is not found, it will return the string representation of the enum value.
    """

    all_enum_repr_classes = []  # type: list[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        CustomEnumRepr.all_enum_repr_classes.append(cls.__name__)

    def __init__(self):
        self._enum_val_to_str = {}
        self._synonyms = defaultdict(list)

        for name in self.enum_names:
            enum_val = getattr(self.enum_type, name, None)
            if enum_val is not None:
                if enum_val in self._enum_val_to_str:  # already exists,
                    self._synonyms[self._enum_val_to_str[enum_val]].append(name)
                else:
                    self._enum_val_to_str[enum_val] = name
            else:
                pqi_log.info(f'Enum name "{name}" not found in {self.enum_type.__name__}. ')

    def _repr_impl(self, enum_val) -> str:
        s_val = self._enum_val_to_str.get(
            enum_val,
            # if the enum value is not found, return its string representation
            str(enum_val)
        )

        if s_val in self._synonyms:
            # if there are synonyms for the enum value, return the first one
            return f'{s_val} ({", ".join(self._synonyms[s_val])})'
        return s_val

    @property
    @abc.abstractmethod
    def enum_type(self):
        ...

    @property
    @abc.abstractmethod
    def enum_names(self) -> typing.Sequence[str]:
        ...


class WeightEnumRepr(CustomEnumRepr):
    __type__ = 'QFont.Weight'

    @property
    def enum_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QFont.Weight

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Thin', 'ExtraLight', 'Light', 'Normal',
            'Medium', 'DemiBold', 'Bold', 'ExtraBold', 'Black'
        )

    def _repr_impl(self, enum_val) -> str:
        s_val = super()._repr_impl(enum_val)
        try:
            s_val = f'{s_val} ({int(enum_val)})'
        except ValueError:
            pass
        return s_val


class QSizePolicyPolicyRepr(CustomEnumRepr):
    __type__ = 'QSizePolicy.Policy'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QSizePolicy.Policy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Fixed', 'Minimum', 'Maximum', 'Preferred', 'Expanding',
            'MinimumExpanding', 'Ignored'
        )


class QFontHintingPreferenceRepr(CustomEnumRepr):
    __type__ = 'QFont.HintingPreference'

    @property
    def enum_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QFont.HintingPreference

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'PreferDefaultHinting', 'PreferNoHinting', 'PreferVerticalHinting', 'PreferFullHinting'
        )


class QtFocusPolicyRepr(CustomEnumRepr):
    __type__ = 'Qt.FocusPolicy'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.FocusPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoFocus', 'TabFocus', 'ClickFocus', 'StrongFocus', 'WheelFocus'
        )


class QtContextMenuPolicyRepr(CustomEnumRepr):
    __type__ = 'Qt.ContextMenuPolicy'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.ContextMenuPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoContextMenu', 'PreventContextMenu', 'DefaultContextMenu', 'ActionsContextMenu', 'CustomContextMenu'
        )


class QtLayoutDirectionRepr(CustomEnumRepr):
    __type__ = 'Qt.LayoutDirection'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.LayoutDirection

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'LeftToRight', 'RightToLeft', 'LayoutDirectionAuto'
        )


class QFrameShapeRepr(CustomEnumRepr):
    __type__ = 'QFrame.Shape'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QFrame.Shape

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoFrame', 'Box', 'Panel', 'StyledPanel', 'HLine', 'VLine', 'WinPanel'
        )


class QFrameShadowRepr(CustomEnumRepr):
    __type__ = 'QFrame.Shadow'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QFrame.Shadow

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Plain', 'Raised', 'Sunken'
        )


class QToolButtonPopupModeRepr(CustomEnumRepr):
    __type__ = 'QToolButton.ToolButtonPopupMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QToolButton.ToolButtonPopupMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'DelayedPopup', 'MenuButtonPopup', 'InstantPopup'
        )


class QToolButtonToolButtonStyleRepr(CustomEnumRepr):
    __type__ = 'Qt.ToolButtonStyle'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.ToolButtonStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ToolButtonIconOnly', 'ToolButtonTextOnly', 'ToolButtonTextBesideIcon', 'ToolButtonTextUnderIcon',
            'ToolButtonFollowStyle'
        )


class QToolButtonArrowTypeRepr(CustomEnumRepr):
    __type__ = 'Qt.ArrowType'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.ArrowType

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoArrow', 'UpArrow', 'DownArrow', 'LeftArrow', 'RightArrow'
        )


class QtScrollBarPolicyRepr(CustomEnumRepr):
    __type__ = 'Qt.ScrollBarPolicy'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.ScrollBarPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ScrollBarAsNeeded', 'ScrollBarAlwaysOff', 'ScrollBarAlwaysOn'
        )


class QAbstractScrollAreaSizeAdjustPolicyRepr(CustomEnumRepr):
    __type__ = 'QAbstractScrollArea.SizeAdjustPolicy'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractScrollArea.SizeAdjustPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'AdjustIgnored', 'AdjustToContents', 'AdjustToContentsOnFirstShow'
        )


class QAbstractItemViewDragDropModeRepr(CustomEnumRepr):
    __type__ = 'QAbstractItemView.DragDropMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.DragDropMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoDragDrop', 'DragOnly', 'DropOnly', 'DragDrop', 'InternalMove'
        )


class QAbstractItemViewSelectionModeRepr(CustomEnumRepr):
    __type__ = 'QAbstractItemView.SelectionMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.SelectionMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoSelection', 'SingleSelection', 'MultiSelection', 'ExtendedSelection', 'ContiguousSelection'
        )


class QAbstractItemViewSelectionBehaviorRepr(CustomEnumRepr):
    __type__ = 'QAbstractItemView.SelectionBehavior'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.SelectionBehavior

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'SelectItems', 'SelectRows', 'SelectColumns'
        )


class QAbstractItemViewScrollModeRepr(CustomEnumRepr):
    __type__ = 'QAbstractItemView.ScrollMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.ScrollMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ScrollPerItem', 'ScrollPerPixel'
        )


class QtTextElideModeRepr(CustomEnumRepr):
    __type__ = 'Qt.TextElideMode'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.TextElideMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ElideLeft', 'ElideRight', 'ElideMiddle', 'ElideNone'
        )


class QtDropActionRepr(CustomEnumRepr):
    __type__ = 'Qt.DropAction'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.DropAction

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'CopyAction', 'MoveAction', 'LinkAction', 'ActionMask', 'TargetMoveAction', 'IgnoreAction'
        )


class QListViewMovementRepr(CustomEnumRepr):
    __type__ = 'QListView.Movement'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QListView.Movement

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Static', 'Free'
        )


class QListViewFlowRepr(CustomEnumRepr):
    __type__ = 'QListView.Flow'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QListView.Flow

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'LeftToRight', 'TopToBottom'
        )


class QListViewResizeModeRepr(CustomEnumRepr):
    __type__ = 'QListView.ResizeMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QListView.ResizeMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Fixed', 'Adjust'
        )


class QListViewLayoutModeRepr(CustomEnumRepr):
    __type__ = 'QListView.LayoutMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QListView.LayoutMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'SinglePass', 'Batched'
        )


class QListViewViewModeRepr(CustomEnumRepr):
    __type__ = 'QListView.ViewMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QListView.ViewMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ListMode', 'IconMode'
        )


class QtPenStyleRepr(CustomEnumRepr):
    __type__ = 'Qt.PenStyle'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.PenStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoPen', 'SolidLine', 'DashLine', 'DotLine', 'DashDotLine',
            'DashDotDotLine', 'CustomDashLine'
        )


class QTabWidgetTabPositionRepr(CustomEnumRepr):
    __type__ = 'QTabWidget.TabPosition'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QTabWidget.TabPosition

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'North', 'South', 'West', 'East'
        )


class QTabWidgetTabShapeRepr(CustomEnumRepr):
    __type__ = 'QTabWidget.TabShape'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QTabWidget.TabShape

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Rounded', 'Triangular'
        )


class QtQBrushStyleRepr(CustomEnumRepr):
    __type__ = 'Qt.BrushStyle'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.BrushStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoBrush', 'SolidPattern', 'Dense1Pattern', 'Dense2Pattern', 'Dense3Pattern',
            'Dense4Pattern', 'Dense5Pattern', 'Dense6Pattern', 'Dense7Pattern',
            'HorPattern', 'VerPattern', 'CrossPattern', 'BDiagPattern',
            'FDiagPattern', 'DiagCrossPattern',
            'LinearGradientPattern', 'ConicalGradientPattern', 'RadialGradientPattern',
            'TexturePattern',
        )


class QMdiAreaWindowOrderRepr(CustomEnumRepr):
    __type__ = 'QMdiArea.WindowOrder'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QMdiArea.WindowOrder

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'CreationOrder', 'StackingOrder', 'ActivationHistoryOrder'
        )


class QMdiAreaViewModeRepr(CustomEnumRepr):
    __type__ = 'QMdiArea.ViewMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QMdiArea.ViewMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'SubWindowView', 'TabbedView'
        )


class QComboBoxInsertPolicyRepr(CustomEnumRepr):
    __type__ = 'QComboBox.InsertPolicy'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QComboBox.InsertPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoInsert', 'InsertAtTop', 'InsertAtCurrent', 'InsertAtBottom',
            'InsertAfterCurrent', 'InsertBeforeCurrent', 'InsertAlphabetically'
        )


class QComboBoxSizeAdjustPolicyRepr(CustomEnumRepr):
    __type__ = 'QComboBox.SizeAdjustPolicy'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QComboBox.SizeAdjustPolicy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'AdjustToContents', 'AdjustToContentsOnFirstShow', 'AdjustToMinimumContentsLengthWithIcon'
        )


class QFontDatabaseWritingSystemRepr(CustomEnumRepr):
    __type__ = 'QFontDatabase.WritingSystem'

    @property
    def enum_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QFontDatabase.WritingSystem

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Any', 'Latin', 'Greek', 'Cyrillic', 'Armenian', 'Hebrew', 'Arabic',
            'Syriac', 'Thaana', 'Devanagari', 'Bengali', 'Gurmukhi', 'Gujarati',
            'Oriya', 'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Sinhala',
            'Thai', 'Lao', 'Tibetan', 'Myanmar', 'Georgian', 'Khmer',
            'SimplifiedChinese', 'TraditionalChinese', 'Japanese', 'Korean',
            'Vietnamese', 'Symbol',
            'Other',  # the same as Symbol
            'Ogham', 'Runic', 'Nko'
        )


class QLineEditEchoModeRepr(CustomEnumRepr):
    __type__ = 'QLineEdit.EchoMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QLineEdit.EchoMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Normal', 'NoEcho', 'Password', 'PasswordEchoOnEdit'
        )


class QtCursorMoveStyleRepr(CustomEnumRepr):
    __type__ = 'Qt.CursorMoveStyle'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.CursorMoveStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'LogicalMoveStyle', 'VisualMoveStyle'
        )


class QTextEditLineWrapModeRepr(CustomEnumRepr):
    __type__ = 'QTextEdit.LineWrapMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QTextEdit.LineWrapMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoWrap', 'WidgetWidth', 'FixedPixelWidth', 'FixedColumnWidth'
        )


class QPlainTextEditLineWrapModeRepr(CustomEnumRepr):
    __type__ = 'QPlainTextEdit.LineWrapMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QPlainTextEdit.LineWrapMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoWrap', 'WidgetWidth'
        )


class QAbstractSpinBoxStepTypeRepr(CustomEnumRepr):
    __type__ = 'QAbstractSpinBox.StepType'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractSpinBox.StepType

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'DefaultStepType', 'AdaptiveDecimalStepType'
        )


class QAbstractSpinBoxButtonSymbolsRepr(CustomEnumRepr):
    __type__ = 'QAbstractSpinBox.ButtonSymbols'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractSpinBox.ButtonSymbols

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'UpDownArrows', 'PlusMinus', 'NoButtons'
        )


class QAbstractSpinBoxCorrectionModeRepr(CustomEnumRepr):
    __type__ = 'QAbstractSpinBox.CorrectionMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractSpinBox.CorrectionMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'CorrectToPreviousValue', 'CorrectToNearestValue'
        )


class QtTimeSpecRepr(CustomEnumRepr):
    __type__ = 'Qt.TimeSpec'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.TimeSpec

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'LocalTime', 'UTC', 'OffsetFromUTC', 'TimeZone'
        )


class QtOrientationRepr(CustomEnumRepr):
    __type__ = 'Qt.Orientation'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.Orientation

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Horizontal', 'Vertical'
        )


class QSliderTickPositionRepr(CustomEnumRepr):
    __type__ = 'QSlider.TickPosition'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QSlider.TickPosition

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoTicks', 'TicksBothSides', 'TicksAbove', 'TicksBelow', 'TicksLeft', 'TicksRight'
        )


class QtTextFormatRepr(CustomEnumRepr):
    __type__ = 'Qt.TextFormat'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.TextFormat

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'PlainText', 'RichText', 'AutoText',
            'MarkdownText'  # Added since Qt 5.14
        )


class QGraphicsViewDragModeRepr(CustomEnumRepr):
    __type__ = 'QGraphicsView.DragMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.DragMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoDrag', 'ScrollHandDrag', 'RubberBandDrag'
        )


class QGraphicsViewViewportAnchorRepr(CustomEnumRepr):
    __type__ = 'QGraphicsView.ViewportAnchor'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.ViewportAnchor

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoAnchor', 'AnchorViewCenter', 'AnchorUnderMouse'
        )


class QGraphicsViewViewportUpdateModeRepr(CustomEnumRepr):
    __type__ = 'QGraphicsView.ViewportUpdateMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.ViewportUpdateMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'FullViewportUpdate', 'MinimalViewportUpdate', 'SmartViewportUpdate',
            'BoundingRectViewportUpdate', 'NoViewportUpdate'
        )


class QtItemSelectionModeRepr(CustomEnumRepr):
    __type__ = 'Qt.ItemSelectionMode'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.ItemSelectionMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ContainsItemShape', 'IntersectsItemShape', 'ContainsItemBoundingRect', 'IntersectsItemBoundingRect'
        )


class QtDayOfWeekRepr(CustomEnumRepr):
    __type__ = 'Qt.DayOfWeek'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.DayOfWeek

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        )


class QCalendarWidgetSelectionModeRepr(CustomEnumRepr):
    __type__ = 'QCalendarWidget.SelectionMode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QCalendarWidget.SelectionMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoSelection', 'SingleSelection'
        )


class QCalendarWidgetHorizontalHeaderFormatRepr(CustomEnumRepr):
    __type__ = 'QCalendarWidget.HorizontalHeaderFormat'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QCalendarWidget.HorizontalHeaderFormat

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'SingleLetterDayNames', 'ShortDayNames', 'LongDayNames', 'NoHorizontalHeader'
        )


class QCalendarWidgetVerticalHeaderFormatRepr(CustomEnumRepr):
    __type__ = 'QCalendarWidget.VerticalHeaderFormat'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QCalendarWidget.VerticalHeaderFormat

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ISOWeekNumbers', 'NoVerticalHeader'
        )


class QLCDNumberModeRepr(CustomEnumRepr):
    __type__ = 'QLCDNumber.Mode'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QLCDNumber.Mode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Hex', 'Dec', 'Oct', 'Bin'
        )


class QLCDNumberSegmentStyleRepr(CustomEnumRepr):
    __type__ = 'QLCDNumber.SegmentStyle'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QLCDNumber.SegmentStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Outline', 'Filled', 'Flat'
        )


class QProgressBarDirectionRepr(CustomEnumRepr):
    __type__ = 'QProgressBar.Direction'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QProgressBar.Direction

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'TopToBottom', 'BottomToTop'
        )

# class QQuickWidgetResizeModeRepr(CustomEnumRepr):
#     __type__ = 'QQuickWidget.ResizeMode'
#
#     @property
#     def enum_type(self):
#         QtWidgets = self._get_qt_lib().QtWidgets
#         return QtWidgets.QQuickWidget.ResizeMode
#
#     @property
#     def enum_names(self) -> typing.Sequence[str]:
#         return (
#             'SizeViewToRootObject', 'SizeRootObjectToView'
#         )
