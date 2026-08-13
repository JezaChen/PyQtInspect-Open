import abc
import functools
import typing

from PyQtInspect._pqi_bundle.pqi_qt_tools import import_Qt

__all__ = [
    'TypeRepr',
    'get_representation',
]


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

    # This class variable is used to map type names to their corresponding representation classes.
    # ---
    # Update 20250822: This variable can be a sequence of type names for flag types.
    #   Since the return type of some methods is different in PyQt5 and PyQt6,
    #   for example:
    #     PyQt6.QtWidgets.QGraphicsView.optimizationFlags will return a `QGraphicsView.OptimizationFlag` type,
    #     while PyQt5.QtWidgets.QGraphicsView.optimizationFlags will return a `QGraphicsView.OptimizationFlags` type.
    # ---
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
        if isinstance(cls.__type__, str):
            TypeRepr._type_to_repr[cls.__type__] = cls
        elif isinstance(cls.__type__, typing.Iterable):
            for type_name in cls.__type__:
                TypeRepr._type_to_repr[type_name] = cls
        else:
            raise TypeError(
                f'Invalid __type__ attribute in {cls.__name__}. It should be a string or an iterable of strings.')

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
