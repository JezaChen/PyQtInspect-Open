import abc
import functools
import typing
from abc import ABC
from collections import defaultdict

from PyQtInspect._pqi_bundle import pqi_log

from PyQtInspect._pqi_bundle.pqi_comm_constants import WidgetPropsKeys
from PyQtInspect._pqi_bundle.pqi_qt_tools import (
    find_method_by_name_and_call, import_Qt, find_method_by_name_and_safe_call
)

__all__ = ['WidgetPropertiesGetter']


def _get_enum_name(enum_val) -> str:
    if hasattr(enum_val, 'name'):
        return enum_val.name
    return str(enum_val)


class TypeRepr(abc.ABC):
    """
    A base class for type representations.
    Subclasses should implement the `_repr_impl` method to provide the string representation of the type.

    The `_repr_impl` method should return 
    - a dictionary with the following keys:
      - WidgetPropsKeys.VALUE_KEY: the string representation of the type
      - WidgetPropsKeys.PROPS_KEY: a dictionary of the type's properties
    - or a string if the type is a simple type
    """
    _type_to_repr = {}

    __type__ = ''

    @staticmethod
    def get_type_repr(type_) -> typing.Type['TypeRepr']:
        """
        Get the string representation of a type.
        :param type_: The type to get the representation for.
        :return: A string representation of the type.
        """
        if type_ in TypeRepr._type_to_repr:
            return TypeRepr._type_to_repr[type_]
        return TypeRepr  # fallback to the base class if not found

    def __init_subclass__(cls, **kwargs):
        TypeRepr._type_to_repr[cls.__type__] = cls

    @classmethod
    @functools.lru_cache(maxsize=1)
    def instance(cls) -> 'TypeRepr':
        """
        Get the enum representation class for this enum.
        :return: An instance of the enum representation class.
        """
        return cls()

    def _repr_impl(self, value):
        return str(value)

    @classmethod
    def repr(cls, value) -> typing.Union[str, dict]:
        """
        Get the string representation of an enum value.
        :param value: The enum value to get the representation for.
        :return: A string representation of the enum value.

        :note: This method is a fallback for types that do not have a specific representation class.
        """
        return cls.instance()._repr_impl(value)

    # === TOOL FUNCTIONS ===
    def _get_qt_lib(self):
        from PyQtInspect.pqi import SetupHolder
        return import_Qt(SetupHolder.setup[SetupHolder.KEY_QT_SUPPORT])


def get_representation(value) -> typing.Union[str, dict]:
    """
    Get the string representation of a value.
    :param value: The value to get the representation for.
    :return: A string representation of the value.
    """
    repr_cls = TypeRepr.get_type_repr(type(value).__qualname__)
    return repr_cls.repr(value)


class QRectRepr(TypeRepr):
    __type__ = 'QRect'

    def _repr_impl(self, value) -> dict:
        return {
            WidgetPropsKeys.VALUE_KEY: f'[({value.x()}, {value.y()}), {value.width()} x {value.height()}]',
            WidgetPropsKeys.PROPS_KEY: {
                'X': value.x(),
                'Y': value.y(),
                'Width': value.width(),
                'Height': value.height(),
            }
        }


class QRectFRepr(TypeRepr):
    __type__ = 'QRectF'

    def _repr_impl(self, value) -> dict:
        return {
            WidgetPropsKeys.VALUE_KEY: f'[({value.x()}, {value.y()}), {value.width()} x {value.height()}]',
            WidgetPropsKeys.PROPS_KEY: {
                'X': value.x(),
                'Y': value.y(),
                'Width': value.width(),
                'Height': value.height(),
            }
        }

class QSizeRepr(TypeRepr):
    __type__ = 'QSize'

    def _repr_impl(self, value) -> dict:
        return {
            WidgetPropsKeys.VALUE_KEY: f'{value.width()} x {value.height()}',
            WidgetPropsKeys.PROPS_KEY: {
                'Width': value.width(),
                'Height': value.height(),
            }
        }


class QColorRepr(TypeRepr):
    __type__ = 'QColor'

    def _repr_impl(self, color) -> dict:
        """
        Get the string representation of a QColor.
        :param color: The QColor object.
        :return: A dictionary with the color properties.
        """
        return {
            WidgetPropsKeys.VALUE_KEY: f'[{color.red()}, {color.green()}, {color.blue()}] ({color.alpha()})',
            WidgetPropsKeys.PROPS_KEY: {
                'Red': color.red(),
                'Green': color.green(),
                'Blue': color.blue(),
                'Alpha': color.alpha(),
            }
        }

class QBrushRepr(TypeRepr):
    __type__ = 'QBrush'

    def _repr_impl(self, brush) -> dict:
        color = brush.color()  # complex class
        color_repr: dict = get_representation(color)
        assert isinstance(color_repr, dict)

        style = brush.style()  # enum
        style_repr: str = get_representation(style)
        assert isinstance(style_repr, str)

        return {
            WidgetPropsKeys.VALUE_KEY: f'[{style_repr}, {color_repr[WidgetPropsKeys.VALUE_KEY]}]',
            WidgetPropsKeys.PROPS_KEY: {
                'Style': style_repr,
                'Color': color_repr,
            }
        }


class QUrlRepr(TypeRepr):
    __type__ = 'QUrl'

    def _repr_impl(self, url) -> dict:
        """
        Get the string representation of a QUrl.
        :param url: The QUrl object.
        :return: A dictionary with the URL properties.
        """
        return url.toString()



class CustomEnumRepr(TypeRepr):
    """
    A base class for custom enum representations.
    Subclasses should implement the `enum_type` and `enum_names` properties to provide the enum type and names.
    The `_repr_impl` method should return the string representation of the enum value.
    If the enum value is not found, it will return the string representation of the enum value.
    """

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


class CustomFlagRepr(CustomEnumRepr, ABC):
    """
    A base class for custom flag representations.
    :note: This class is a subclass of `CustomEnumRepr` and is used to represent flag values.
    """

    @property
    @abc.abstractmethod
    def flags_type(self):
        ...

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
        if not isinstance(flag_val, self.flags_type):
            raise TypeError(f'Expected {self.enum_type}, got {type(flag_val)}')

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
    __type__ = 'QToolButton.ToolButtonStyle'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QToolButton.ToolButtonStyle

    @property
    def enum_names(self) -> typing.Sequence[str]:
        return (
            'ToolButtonIconOnly', 'ToolButtonTextOnly', 'ToolButtonTextBesideIcon', 'ToolButtonTextUnderIcon',
            'ToolButtonFollowStyle'
        )


class QToolButtonArrowTypeRepr(CustomEnumRepr):
    __type__ = 'QToolButton.ArrowType'

    @property
    def enum_type(self):
        QtWidgets = self._get_qt_lib().QtWidgets
        return QtWidgets.QToolButton.ArrowType

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


class QtInputMethodHintRepr(CustomFlagRepr):
    __type__ = 'Qt.InputMethodHints'

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


class QSizePolicyRepr(TypeRepr):
    __type__ = 'QSizePolicy'

    def _repr_impl(self, size_policy) -> dict:
        """
        Get the string representation of a QSizePolicy.
        :return: a dictionary containing the size policy properties, e.g.
          {
            'v': '[Preferred, Fixed, 0, 0]',
            'p': {
                'HorizontalPolicy': 'Preferred',
                'VerticalPolicy': 'Fixed',
                'HorizontalStretch': 0,
                'VerticalStretch': 0,
            }
          }
        """
        horizontal_policy_str = get_representation(size_policy.horizontalPolicy())
        vertical_policy_str = get_representation(size_policy.verticalPolicy())
        horizontal_stretch = size_policy.horizontalStretch()
        vertical_stretch = size_policy.verticalStretch()

        return {
            WidgetPropsKeys.VALUE_KEY: f'[{horizontal_policy_str}, {vertical_policy_str}, {horizontal_stretch}, {vertical_stretch}]',
            WidgetPropsKeys.PROPS_KEY: {
                'HorizontalPolicy': horizontal_policy_str,
                'VerticalPolicy': vertical_policy_str,
                'HorizontalStretch': horizontal_stretch,
                'VerticalStretch': vertical_stretch,
            }
        }


class QFontRepr(TypeRepr):
    __type__ = 'QFont'

    def _repr_weight(self, weight) -> str:
        # QFont.weight() returns int value in PyQt5, so we need to call `WeightEnumRepr.repr` explicitly
        return WeightEnumRepr.repr(weight)

    def _repr_impl(self, font):
        family = font.family()
        pt_size = font.pointSize()
        return {
            WidgetPropsKeys.VALUE_KEY: f'[{family}, {pt_size}]',
            WidgetPropsKeys.PROPS_KEY: {
                'Family': family,
                'PointSize': pt_size,
                'Bold': font.bold(),
                'Italic': font.italic(),
                'Underline': font.underline(),
                'StrikeOut': font.strikeOut(),
                'Kerning': font.kerning(),
                'Weight': self._repr_weight(font.weight()),
                'StyleStrategy': get_representation(font.styleStrategy()),
                'HintingPreference': get_representation(font.hintingPreference()),
            }
        }


class QKeySequenceRepr(TypeRepr):
    __type__ = 'QKeySequence'

    def _repr_impl(self, key_sequence):
        """
        Get the string representation of a QKeySequence.
        :param key_sequence: The QKeySequence object.
        :return: A string representation of the key sequence.
        """
        return key_sequence.toString()


class QDateRepr(TypeRepr):
    __type__ = 'QDate'

    def _repr_impl(self, date) -> str:
        """
        Get the string representation of a QDate using system locale.
        :param date: The QDate object.
        :return: A string representation of the date.
        """
        QtCore = self._get_qt_lib().QtCore
        pqi_log.info(f'date.toString() = {date.toString(QtCore.Qt.DateFormat.ISODate)}')
        return date.toString(QtCore.Qt.DateFormat.ISODate)


class QTimeRepr(TypeRepr):
    __type__ = 'QTime'

    def _repr_impl(self, time) -> str:
        """
        Get the string representation of a QTime using system locale.
        :param time: The QTime object.
        :return: A string representation of the time.
        """
        QtCore = self._get_qt_lib().QtCore
        return time.toString(QtCore.Qt.DateFormat.ISODate)


class QDateTimeRepr(TypeRepr):
    __type__ = 'QDateTime'

    def _repr_impl(self, datetime) -> str:
        """
        Get the string representation of a QDateTime using system locale.
        :param datetime: The QDateTime object.
        :return: A string representation of the datetime.
        """
        QtCore = self._get_qt_lib().QtCore
        return datetime.toString(QtCore.Qt.DateFormat.ISODate)


class QAbstractItemViewEditTriggersRepr(CustomFlagRepr):
    __type__ = 'QAbstractItemView.EditTriggers'

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


class QtAlignmentFlagRepr(CustomFlagRepr):
    __type__ = 'Qt.Alignment'

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


class QDockWidgetDockWidgetFeatureFlagRepr(CustomFlagRepr):
    __type__ = 'QDockWidget.DockWidgetFeatures'

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
    __type__ = 'Qt.DockWidgetAreas'

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


class QFontComboBoxFontFiltersRepr(CustomFlagRepr):
    __type__ = 'QFontComboBox.FontFilters'

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


class QTextEditAutoFormattingRepr(CustomFlagRepr):
    __type__ = 'QTextEdit.AutoFormatting'

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


class QtTextInteractionFlagsRepr(CustomFlagRepr):
    __type__ = 'Qt.TextInteractionFlags'

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


class QDateTimeEditSectionRepr(CustomFlagRepr):
    __type__ = 'QDateTimeEdit.Sections'

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


class QPainterRenderHintsRepr(CustomFlagRepr):
    __type__ = 'QPainter.RenderHints'

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


class QGraphicsCacheModeRepr(CustomFlagRepr):
    __type__ = 'QGraphicsView.CacheMode'

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


class QGraphicsViewOptimizationFlagsRepr(CustomFlagRepr):
    __type__ = 'QGraphicsView.OptimizationFlags'

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
                'currentItemText': lambda o: find_method_by_name_and_call(o, 'itemText', find_method_by_name_and_call(o, 'currentIndex')),
                # w = o.currentWidget(); if w: w.objectName()
                'currentItemName': lambda o: find_method_by_name_and_safe_call(find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
                # 'currentItemIcon'
                'currentItemToolTip': lambda o: find_method_by_name_and_call(o, 'itemToolTip', find_method_by_name_and_call(o, 'currentIndex')),
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
                'currentTabText': lambda o: find_method_by_name_and_call(o, 'tabText', find_method_by_name_and_call(o, 'currentIndex')),
                'currentTabName': lambda o: find_method_by_name_and_safe_call(find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
                # ’currentTabIcon'
                'currentTabToolTip': lambda o: find_method_by_name_and_call(o, 'tabToolTip', find_method_by_name_and_call(o, 'currentIndex')),
                'currentTabWhatThis': lambda o: find_method_by_name_and_call(o, 'tabWhatsThis', find_method_by_name_and_call(o, 'currentIndex')),
            },
            'QStackedWidget': {
                'currentIndex': _generate_prop_fetcher_by_calling_method('currentIndex'),
                'currentPageName': lambda o: find_method_by_name_and_safe_call(find_method_by_name_and_call(o, 'currentWidget'), 'objectName', ''),
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
                'activateSubWindowName': lambda o: find_method_by_name_and_safe_call(find_method_by_name_and_call(o, 'activeSubWindow'), 'objectName', ''),
                'activateSubWindowTitle': lambda o: find_method_by_name_and_safe_call(find_method_by_name_and_call(o, 'activeSubWindow'), 'windowTitle ', ''),
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
