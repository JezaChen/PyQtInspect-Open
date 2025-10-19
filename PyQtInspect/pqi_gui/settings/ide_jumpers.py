import abc
import os
import typing
import subprocess
import sys

from PyQtInspect.pqi_gui.settings import SettingsController
from PyQtInspect.pqi_gui.settings.enums import SupportedIDE

__all__ = [
    'SupportedIDE',

    'jump_to_ide',
    'find_default_ide_path',
]


class IDEJumpHelper(abc.ABC):
    """ Abstract base class for IDE jump helpers. """

    __ide_type__: typing.ClassVar[SupportedIDE] = SupportedIDE.NoneType
    __ide_type_to_helper__: typing.ClassVar[typing.Dict[SupportedIDE, typing.Type['IDEJumpHelper']]] = {}

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, '__ide_type__') or cls.__ide_type__ in (SupportedIDE.NoneType, SupportedIDE.Custom):
            raise NotImplementedError(
                'Subclasses of IDEJumpHelper must define __ide_type__ attribute with a valid SupportedIDE value.'
            )

        IDEJumpHelper.__ide_type_to_helper__[cls.__ide_type__] = cls
        super().__init_subclass__(**kwargs)

    @staticmethod
    def get_jump_helper(ide_type: SupportedIDE) -> typing.Type['IDEJumpHelper']:
        """ Get the jump helper class for the specified IDE type. """
        helper_cls = IDEJumpHelper.__ide_type_to_helper__.get(ide_type)
        if not helper_cls:
            raise ValueError(f'No jump helper found for IDE type: {ide_type}')
        return helper_cls

    # region Abstract Methods
    @classmethod
    @abc.abstractmethod
    def get_command_parameters(cls, file: str, line: int) -> typing.List[str]:
        """ Get the command arguments to jump to the specified file and line.
        @note: For IDE jump command construction, these parameters will be appended to the IDE executable path.
        """

    @classmethod
    @abc.abstractmethod
    def get_command_name(cls) -> str:
        """ Get the command name of the IDE executable.
        @note: For IDE default path finding, this name will be used in terminal commands like 'which' or 'Get-Command'.
        """

    @classmethod
    @abc.abstractmethod
    def get_executable_name_candidates(cls) -> typing.List[str]:
        """ Get the list of possible executable names for the IDE.
        @note: For IDE default path finding, they will be used to search the IDE executable in system PATH.
        """
    # endregion


class PyCharmJumpHelper(IDEJumpHelper):
    """ Jump helper for PyCharm IDE. """
    __ide_type__ = SupportedIDE.PyCharm

    @classmethod
    def get_command_parameters(cls, file: str, line: int) -> typing.List[str]:
        return ['--line', str(line), file]

    @classmethod
    def get_command_name(cls) -> str:
        return 'pycharm'

    @classmethod
    def get_executable_name_candidates(cls) -> typing.List[str]:
        return ['pycharm64.exe', 'pycharm.exe', 'pycharm']


class VSCodeJumpHelper(IDEJumpHelper):
    """ Jump helper for Visual Studio Code IDE. """
    __ide_type__ = SupportedIDE.VSCode

    @classmethod
    def get_command_parameters(cls, file: str, line: int) -> typing.List[str]:
        return ['--goto', f'{file}:{line}']

    @classmethod
    def get_command_name(cls) -> str:
        return 'code'

    @classmethod
    def get_executable_name_candidates(cls) -> typing.List[str]:
        return ['Code.exe', 'code']


class CursorJumpHelper(IDEJumpHelper):
    """ Jump helper for Cursor. """
    __ide_type__ = SupportedIDE.Cursor

    @classmethod
    def get_command_parameters(cls, file: str, line: int) -> typing.List[str]:
        return ['--goto', f'{file}:{line}']

    @classmethod
    def get_command_name(cls) -> str:
        return 'cursor'

    @classmethod
    def get_executable_name_candidates(cls) -> typing.List[str]:
        return ['Cursor.exe', 'cursor']


def _find_default_ide_path_helper(
        command_name: str,
        executable_names: typing.List[str]
) -> str:
    def _find_for_windows() -> str:
        """ For Windows, we can use powershell command to find the path """
        output = subprocess.run(
            f'powershell -Command "$(Get-Command {command_name}).path"',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        if output.stdout:
            return output.stdout.strip()
        return ''

    def _find_for_linux() -> str:
        """ for Unix-like systems, we can use which command to find the path """
        output = subprocess.run(
            f'which {command_name}',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        if output.stdout:
            return output.stdout.strip()
        return ''

    # First, try to use terminal command to find the path
    if sys.platform == 'win32':
        defaultPath = _find_for_windows()
        if defaultPath:
            return defaultPath
    else:
        defaultPath = _find_for_linux()
        if defaultPath:
            return defaultPath

    # If the above method fails, we can try to find the path from the environment variables
    for path_dir in os.environ['PATH'].split(os.pathsep):
        for exe_name in executable_names:
            exe_path = os.path.join(path_dir, exe_name)
            if os.path.isfile(exe_path):
                return exe_path
    return ''


def _construct_ide_jump_command(file: str, line: int) -> str:
    # Get the IDE info from settings
    ide_type = SupportedIDE(SettingsController.instance().ideType)

    if ide_type == SupportedIDE.NoneType:
        raise RuntimeError('You have not configured an IDE for jumping.')

    if ide_type == SupportedIDE.Custom:
        args = SettingsController.instance().ideParameters  # type: str
        args = args.replace('{file}', file).replace('{line}', str(line))
        return f'"{SettingsController.instance().idePath}" {args}'

    helper = IDEJumpHelper.get_jump_helper(ide_type)
    # use pre-defined parameters
    cmd_parts = [f'"{SettingsController.instance().idePath}"']
    cmd_parts.extend(helper.get_command_parameters(file, line))
    return ' '.join(cmd_parts)


# region Public APIs
def jump_to_ide(file: str, line: int):
    """ Jump to the specified file and line in the configured IDE. """
    # Validate inputs
    if not file or not os.path.isfile(file):
        raise ValueError(f'Invalid file path: {file}')
    if line <= 0:
        raise ValueError(f'Invalid line number: {line}')

    jump_command = _construct_ide_jump_command(file, line)
    try:
        subprocess.Popen(jump_command, shell=True)
    except Exception as e:
        # raise an error if the jump fails
        raise RuntimeError(f'Failed to jump to IDE with command: {jump_command}') from e


def find_default_ide_path(ide_type: SupportedIDE) -> str:
    """ Find the default path of the specified IDE type. """
    if ide_type in (SupportedIDE.Custom, SupportedIDE.NoneType):
        raise ValueError('Cannot find default path for Custom or NoneType IDE.')

    helper = IDEJumpHelper.get_jump_helper(ide_type)
    return _find_default_ide_path_helper(
        helper.get_command_name(),
        helper.get_executable_name_candidates()
    )

# endregion
