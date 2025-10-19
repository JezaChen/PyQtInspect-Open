import enum
import typing

class SupportedIDE(enum.Enum):
    """ Enum for supported IDEs. """
    PyCharm = 'PyCharm'
    VSCode = 'VSCode'
    Cursor = 'Cursor'

    Custom = 'Custom'
    NoneType = 'None'

    @staticmethod
    def get_supported_IDEs_for_settings() -> typing.List[typing.Tuple[str, 'SupportedIDE']]:
        """ Get the list of supported IDEs for settings selection. """
        return [
            # (Display Name, Enum Value)
            ('No IDE', SupportedIDE.NoneType),
            ('PyCharm', SupportedIDE.PyCharm),
            ('Visual Studio Code', SupportedIDE.VSCode),
            ('Cursor', SupportedIDE.Cursor),
            ('Custom', SupportedIDE.Custom),
        ]
