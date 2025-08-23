"""
Representers of ordinary types
"""

from PyQtInspect._pqi_bundle import pqi_log

from PyQtInspect._pqi_bundle.pqi_comm_constants import WidgetPropsKeys
from PyQtInspect._pqi_bundle.pqi_qt_widget_props_fetcher._types_repr._base import TypeRepr, get_representation


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
        from PyQtInspect._pqi_bundle.pqi_qt_widget_props_fetcher._types_repr._enum_reprs import WeightEnumRepr
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
