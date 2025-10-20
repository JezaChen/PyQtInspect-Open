import abc
import os
import typing
import subprocess
import sys
import shlex

from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect.pqi_gui.settings import SettingsController
from PyQtInspect.pqi_gui.settings.enums import SupportedIDE
from PyQtInspect._pqi_bundle.pqi_contants import IS_WINDOWS

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
        if cls.__ide_type__ in (SupportedIDE.NoneType, SupportedIDE.Custom):
            raise NotImplementedError(
                'Subclasses of IDEJumpHelper must override __ide_type__ attribute with a valid SupportedIDE value.'
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
            pqi_log.info(f'Found IDE path for {command_name} on Windows: {defaultPath}')
            return defaultPath
    else:
        defaultPath = _find_for_linux()
        if defaultPath:
            pqi_log.info(f'Found IDE path for {command_name} on Unix-like system: {defaultPath}')
            return defaultPath

    # If the above method fails, we can try to find the path from the environment variables
    for path_dir in os.environ['PATH'].split(os.pathsep):
        for exe_name in executable_names:
            exe_path = os.path.join(path_dir, exe_name)
            if os.path.isfile(exe_path):
                pqi_log.info(f'Found IDE path for {command_name} from PATH: {exe_path}')
                return exe_path
    pqi_log.info(f'Could not find default IDE path for {command_name}.')
    return ''


def _construct_ide_jump_command(file: str, line: int) -> typing.List[str]:
    # Get the IDE info from settings
    ide_type = SupportedIDE(SettingsController.instance().ideType)

    if ide_type == SupportedIDE.NoneType:
        raise RuntimeError('You have not configured an IDE for jumping.')

    if ide_type == SupportedIDE.Custom:
        parameters_template = SettingsController.instance().ideParameters  # type: str
        split_parameters = shlex.split(
            parameters_template,
            posix=os.name != 'nt'
        )
        command_parameters = [
            parameter.replace('{file}', file).replace('{line}', str(line))
            for parameter in split_parameters
        ]
        return [SettingsController.instance().idePath, *command_parameters]

    helper = IDEJumpHelper.get_jump_helper(ide_type)
    # use pre-defined parameters
    return [SettingsController.instance().idePath, *helper.get_command_parameters(file, line)]


# region Public APIs
def jump_to_ide(file: str, line: int):
    """ Jump to the specified file and line in the configured IDE. """
    # Validate inputs
    if not file or not os.path.isfile(file):
        raise ValueError(f'Invalid file path: {file}')
    if line <= 0:
        raise ValueError(f'Invalid line number: {line}')

    jump_command = _construct_ide_jump_command(file, line)
    pqi_log.info(f'Jumping to IDE with command: {jump_command}')
    try:
        # Use `subprocess.Popen` to launch the IDE asynchronously
        # We don't wait for the process to complete (`subprocess.run` would wait),
        #  so we cannot catch errors from the IDE itself.
        subprocess.Popen(jump_command)
    except Exception as e:
        # raise an error if the jump fails
        if IS_WINDOWS:
            # The subprocess.list2cmdline is Windows-specific
            command_display = subprocess.list2cmdline(jump_command)
        else:
            command_display = ' '.join(shlex.quote(part) for part in jump_command)
        raise RuntimeError(
            f'Failed to jump to IDE with command: {command_display}'
        ) from e


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
