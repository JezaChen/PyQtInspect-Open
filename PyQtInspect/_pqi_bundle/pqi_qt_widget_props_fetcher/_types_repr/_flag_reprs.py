"""
Representers of flags types
"""
import abc
import typing

from PyQtInspect._pqi_bundle.pqi_qt_widget_props_fetcher._types_repr._enum_reprs import CustomEnumRepr


class CustomFlagRepr(CustomEnumRepr, abc.ABC):
    """
    A base class for custom flag representations.
    :note: This class is a subclass of `CustomEnumRepr` and is used to represent flag values.
    """

    @property
    @abc.abstractmethod
    def flags_type(self):
        """
        ONLY FOR PyQt5/PySide2!!!
        For PyQt6/PySide6, the flag types are removed, so accessing this property will raise an error.
        ----------------------------------------------------
        The python equivalent type of the `QFlags` type
        For example:
          - The `Qt.InputMethodHint` is the enum type, and
          - the `Qt.InputMethodHints` is the flags type.
        ----------------------------------------------------
        But it is only valid for PyQt5/PySide2, in PyQt6/PySide6, the flag types are removed, replaced by the enum type.
        For example, in PyQt6/PySide6, the `Qt.InputMethodHint` is used as both the enum type and the flags type.
          And the `Qt.InputMethodHints` is not available anymore.
        """
        ...

    def _get_flag_type_in_current_qt_lib(self):
        """
        Get the flag type in the current Qt library.
        :return: The flag type in the current Qt library.
        """
        try:
            return self.flags_type
        except AttributeError:
            # If the flags_type is not defined, it means we are using PyQt6/PySide6
            # In this case, we can use the enum_type as the flag type
            return self.enum_type

    @property
    def zero_display(self) -> str:
        """ Get the string representation of the zero value. """
        return ''

    def _repr_impl(self, flag_val) -> str:
        """
        Get the string representation of a flag value.
        :param flag_val: The flag value to get the representation for.
        :return: A string representation of the flag value.
        """
        flag_type = self._get_flag_type_in_current_qt_lib()
        if not isinstance(flag_val, flag_type):
            raise TypeError(f'Expected {flag_type}, got {type(flag_val)}')

        if not flag_val:
            return self.zero_display

        # flag_names = [name for val, name in self._enum_val_to_str.items() if val and (flag_val & val) == val]
        flag_names = []
        for val, name in self._enum_val_to_str.items():
            if val and (flag_val & val) == val:
                flag_names.append(name)
                # if there are synonyms for the flag name, add them
                if name in self._synonyms:
                    flag_names.extend(self._synonyms[name])
        return '|'.join(flag_names)


class QFontStyleStrategyRepr(CustomFlagRepr):
    __type__ = 'QFont.StyleStrategy'

    @property
    def enum_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QFont.StyleStrategy

    @property
    def flags_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QFont.StyleStrategy

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'PreferDefault', 'PreferBitmap', 'PreferDevice', 'PreferOutline', 'ForceOutline',
            'NoAntialias', 'NoSubpixelAntialias', 'PreferAntialias',

            'OpenGLCompatible',  # deprecated since Qt 5.15.0

            'ContextFontMerging',  # since Qt 6.8
            'PreferTypoLineMetrics',  # since Qt 6.8

            'NoFontMerging',
            'PreferNoShaping',  # since Qt 5.10

            'PreferMatch', 'PreferQuality',
            'ForceIntegerMetrics',  # deprecated since Qt 5.15.0
        )


class QtInputMethodHintRepr(CustomFlagRepr):
    __type__ = ('Qt.InputMethodHint', 'Qt.InputMethodHints')

    @property
    def zero_display(self) -> str:
        return 'ImhNone'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.InputMethodHint

    @property
    def flags_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.InputMethodHints

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ImhNone',

            # Flags that alter the behavior:
            'ImhHiddenText',
            'ImhSensitiveData',
            'ImhNoAutoUppercase',
            'ImhPreferNumbers',
            'ImhPreferUppercase',
            'ImhPreferLowercase',
            'ImhNoPredictiveText',
            'ImhDate',
            'ImhTime',
            'ImhPreferLatin',
            'ImhMultiLine',
            'ImhNoEditMenu',  # introduced in Qt 5.11
            'ImhNoTextHandles',  # introduced in Qt 5.11

            # Flags that restrict input (exclusive flags):
            'ImhDigitsOnly',
            'ImhFormattedNumbersOnly',
            'ImhUppercaseOnly',
            'ImhLowercaseOnly',
            'ImhDialableCharactersOnly',
            'ImhEmailCharactersOnly',
            'ImhUrlCharactersOnly',
            'ImhLatinOnly',
        )


class QAbstractItemViewEditTriggersRepr(CustomFlagRepr):
    __type__ = ('QAbstractItemView.EditTrigger', 'QAbstractItemView.EditTriggers')

    @property
    def zero_display(self) -> str:
        """ Get the string representation of the zero value. """
        return 'NoEditTriggers'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.EditTrigger

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QAbstractItemView.EditTriggers

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoEditTriggers', 'CurrentChanged', 'DoubleClicked', 'SelectedClicked', 'EditKeyPressed',
            'AnyKeyPressed', 'AllEditTriggers'
        )


class QtAlignmentFlagRepr(CustomFlagRepr):
    __type__ = ('Qt.AlignmentFlag', 'Qt.Alignment')

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.AlignmentFlag

    @property
    def flags_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.Alignment

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'AlignLeft', 'AlignRight', 'AlignHCenter', 'AlignJustify',
            'AlignTop', 'AlignBottom', 'AlignVCenter', 'AlignBaseline',
            'AlignCenter',
            'AlignLeading', 'AlignTrailing', 'AlignAbsolute',
            # Masks
            'AlignHorizontal_Mask', 'AlignVertical_Mask'
        )


class QDockWidgetDockWidgetFeatureFlagRepr(CustomFlagRepr):
    __type__ = ('QDockWidget.DockWidgetFeature', 'QDockWidget.DockWidgetFeatures')

    @property
    def zero_display(self) -> str:
        return 'NoDockWidgetFeatures'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QDockWidget.DockWidgetFeature

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QDockWidget.DockWidgetFeatures

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'DockWidgetClosable', 'DockWidgetMovable', 'DockWidgetFloatable',
            'DockWidgetVerticalTitleBar', 'NoDockWidgetFeatures',

            'AllDockWidgetFeatures'  # deprecated
        )


class QtDockWidgetAreasFlagRepr(CustomFlagRepr):
    __type__ = ('Qt.DockWidgetArea', 'Qt.DockWidgetAreas')

    @property
    def zero_display(self) -> str:
        return 'NoDockWidgetArea'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.DockWidgetArea

    @property
    def flags_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.DockWidgetAreas

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'LeftDockWidgetArea', 'RightDockWidgetArea', 'TopDockWidgetArea', 'BottomDockWidgetArea',
            'AllDockWidgetAreas', 'NoDockWidgetArea'
        )


class QFontComboBoxFontFiltersRepr(CustomFlagRepr):
    __type__ = ('QFontComboBox.FontFilter', 'QFontComboBox.FontFilters')

    @property
    def zero_display(self) -> str:
        return 'AllFonts'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QFontComboBox.FontFilter

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QFontComboBox.FontFilters

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'AllFonts', 'ScalableFonts', 'NonScalableFonts', 'MonospacedFonts', 'ProportionalFonts'
        )


class QTextEditAutoFormattingRepr(CustomFlagRepr):
    __type__ = ('QTextEdit.AutoFormattingFlag', 'QTextEdit.AutoFormatting')

    @property
    def zero_display(self) -> str:
        return 'AutoNone'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QTextEdit.AutoFormattingFlag

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QTextEdit.AutoFormatting

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'AutoNone', 'AutoBulletList', 'AutoAll'
        )


class QtTextInteractionFlagsRepr(CustomFlagRepr):
    __type__ = ('Qt.TextInteractionFlag', 'Qt.TextInteractionFlags')

    @property
    def zero_display(self) -> str:
        return 'NoTextInteraction'

    @property
    def enum_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.TextInteractionFlag

    @property
    def flags_type(self):
        QtCore = self._get_qt_lib().QtCore
        return QtCore.Qt.TextInteractionFlags

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoTextInteraction', 'TextSelectableByMouse', 'TextSelectableByKeyboard',
            'LinksAccessibleByMouse', 'LinksAccessibleByKeyboard', 'TextEditable',
            'TextEditorInteraction', 'TextBrowserInteraction'
        )


class QDateTimeEditSectionRepr(CustomFlagRepr):
    __type__ = ('QDateTimeEdit.Section', 'QDateTimeEdit.Sections')

    @property
    def zero_display(self) -> str:
        return 'NoSection'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QDateTimeEdit.Section

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QDateTimeEdit.Sections

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'NoSection', 'AmPmSection', 'MSecSection', 'SecondSection', 'MinuteSection',
            'HourSection', 'DaySection', 'MonthSection', 'YearSection'
        )


class QPainterRenderHintsRepr(CustomFlagRepr):
    __type__ = ('QPainter.RenderHint', 'QPainter.RenderHints')

    @property
    def zero_display(self) -> str:
        return ''

    @property
    def enum_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QPainter.RenderHint

    @property
    def flags_type(self):
        QtGui = self._get_qt_lib().QtGui
        return QtGui.QPainter.RenderHints

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'Antialiasing', 'TextAntialiasing', 'SmoothPixmapTransform', 'VerticalSubpixelPositioning',
            'LosslessImageRendering', 'NonCosmeticDefaultPen'
        )


class QGraphicsCacheModeRepr(CustomFlagRepr):
    __type__ = ('QGraphicsView.CacheModeFlag', 'QGraphicsView.CacheMode')

    @property
    def zero_display(self) -> str:
        return 'CacheNone'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.CacheModeFlag

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.CacheMode

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'CacheNone', 'CacheBackground'
        )


class QGraphicsViewOptimizationFlagsRepr(CustomFlagRepr):
    __type__ = ('QGraphicsView.OptimizationFlag', 'QGraphicsView.OptimizationFlags')

    @property
    def zero_display(self) -> str:
        return ''

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.OptimizationFlag

    @property
    def flags_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QGraphicsView.OptimizationFlags

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'DontSavePainterState', 'DontAdjustForAntialiasing', 'IndirectPainting'
        )
