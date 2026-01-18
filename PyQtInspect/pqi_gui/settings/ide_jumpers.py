import abc
import os
import pathlib
import typing
import subprocess
import sys
import shlex

from PyQtInspect.pqi_gui.settings import SettingsController
from PyQtInspect.pqi_gui.settings.enums import SupportedIDE
from PyQtInspect._pqi_bundle import pqi_log
from PyQtInspect._pqi_bundle.pqi_contants import IS_WINDOWS, IS_MACOS

__all__ = [
    'SupportedIDE',

    'jump_to_ide',
    'auto_detect_ide_path',
]

def _path_endswith(a: pathlib.Path, b: pathlib.Path) -> bool:
    """ Check if path `a` ends with path `b`. """
    a_parts = a.parts
    b_parts = b.parts
    return len(a_parts) >= len(b_parts) and a_parts[-len(b_parts):] == b_parts


class IDEJumpHelper(abc.ABC):
    """ Abstract base class for IDE jump helpers. """

    def __new__(cls, *args, **kwargs):
        # Forbid instantiation
        raise TypeError(f'{cls.__name__} cannot be instantiated.')

    __ide_type__: typing.ClassVar[SupportedIDE] = SupportedIDE.NoneType
    __ide_type_to_helper__: typing.ClassVar[typing.Dict[SupportedIDE, typing.Type['IDEJumpHelper']]] = {}

    def __init_subclass__(cls, **kwargs):
        if cls.__new__ != IDEJumpHelper.__new__:
            raise TypeError(f'Subclasses of IDEJumpHelper cannot override __new__ method, which may bypass instantiation restriction.')

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
    def get_executable_name_candidates(cls) -> typing.Set[str]:
        """ Get the list of possible executable names for the IDE.
        @note: For IDE default path finding, they will be used to search the IDE executable in system PATH.
        """

    @classmethod
    def match_executable_name(cls, exe_path: str) -> bool:
        """ Check if the given executable path matches any of the known executable names for the IDE. """
        return os.path.basename(exe_path) in cls.get_executable_name_candidates()
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
    def get_executable_name_candidates(cls) -> typing.Set[str]:
        return {'pycharm64.exe', 'pycharm.exe', 'pycharm'}


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
    def get_executable_name_candidates(cls) -> typing.Set[str]:
        return {'Code.exe', 'code'}

    @classmethod
    def _bundle_id_candidates_on_macos(cls) -> typing.Set[str]:
        return {'com.microsoft.VSCode', 'com.microsoft.VSCodeInsiders'}

    @classmethod
    def _check_macos_bundle_id(cls, exe_path: str) -> bool:
        exe_path = pathlib.Path(exe_path)
        # Check if the executable path ends with the typical Electron app path
        if not _path_endswith(exe_path, pathlib.Path('Contents/MacOS/Electron')):
            return False

        # Traverse up to find the .app bundle and check the bundle identifier
        for parent in exe_path.parents[2:]:  # skip 'Contents/MacOS/Electron'
            if parent.suffix == '.app':
                plist = parent / 'Contents' / 'Info.plist'
                if plist.is_file():
                    try:
                        import plistlib
                        with open(plist, 'rb') as f:
                            plist_data = plistlib.load(f)
                            if plist_data.get('CFBundleIdentifier') in cls._bundle_id_candidates_on_macos():
                                return True
                    except Exception as e:
                        pqi_log.warning(f'Failed to load {plist}: {e}')
        return False

    @classmethod
    def match_executable_name(cls, exe_path: str) -> bool:
        if super().match_executable_name(exe_path):
            return True
        # Special handling for macOS where the running executable might be `Applications/Visual Studio Code.app/Contents/MacOS/Electron`
        if IS_MACOS and cls._check_macos_bundle_id(exe_path):
            return True
        return False

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
    def get_executable_name_candidates(cls) -> typing.Set[str]:
        return {'Cursor.exe', 'cursor'}


def _find_default_ide_path_helper(
        ide_jump_helper: typing.Type['IDEJumpHelper'],
) -> str:
    """ Find the default path of the specified IDE by its command name and executable name candidates. """
    command_name = ide_jump_helper.get_command_name()
    executable_names = ide_jump_helper.get_executable_name_candidates()

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
            pqi_log.info(f'Found IDE path for {command_name} from commands on Windows: {defaultPath}')
            return defaultPath
    else:
        defaultPath = _find_for_linux()
        if defaultPath:
            pqi_log.info(f'Found IDE path for {command_name} from commands on Unix-like system: {defaultPath}')
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


def _find_ide_path_from_running_processes_helper(
        ide_jump_helper: typing.Type['IDEJumpHelper']
) -> str:
    """ Try to find the IDE path from running processes. """
    try:
        import psutil
    except ImportError:
        pqi_log.warning('psutil module is not installed, cannot find IDE path from running processes.')
        return ''

    for proc in psutil.process_iter(['exe']):
        try:
            exe_path = proc.info['exe']
            if exe_path and ide_jump_helper.match_executable_name(exe_path):
                pqi_log.info(f'Found IDE path from running process: {exe_path}')
                return exe_path
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    pqi_log.info('Could not find IDE path from running processes.')
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


def _find_default_ide_path(ide_type: SupportedIDE) -> str:
    """ Find the default path of the specified IDE type. """
    if ide_type in (SupportedIDE.Custom, SupportedIDE.NoneType):
        raise ValueError('Cannot find default path for Custom or NoneType IDE.')

    helper = IDEJumpHelper.get_jump_helper(ide_type)
    return _find_default_ide_path_helper(helper)


def _find_ide_path_from_running_processes(ide_type: SupportedIDE) -> str:
    """ Try to find the IDE path from running processes. """
    if ide_type in (SupportedIDE.Custom, SupportedIDE.NoneType):
        raise ValueError('Cannot find IDE path for Custom or NoneType IDE.')

    helper = IDEJumpHelper.get_jump_helper(ide_type)
    return _find_ide_path_from_running_processes_helper(helper)


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


def auto_detect_ide_path(ide_type: SupportedIDE) -> str:
    """ Auto-detect the IDE path by first checking running processes, then default installation paths. """
    ide_path = _find_ide_path_from_running_processes(ide_type)
    if ide_path:
        return ide_path

    ide_path = _find_default_ide_path(ide_type)
    return ide_path

# endregion
